from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
import main
from app.database import make_engine
from app.services.vacancies import ingest

client = TestClient(main.app)


def prepare(database):
    with Session(database) as db:
        ingest(db)
        db.commit()
    cid = client.post("/api/v1/profiles", json={"name": "Prueba local"}).json()["candidate_id"]
    return cid


def apply(cid, simulation_id=None):
    return client.post("/api/v1/applications", json={"candidate_id": cid, "vacancy_id": "demo-01", "confirmed": True, "simulation_id": simulation_id})


def interview(cid):
    response = apply(cid)
    assert response.status_code == 201
    aid = response.json()["id"]
    for status in ["en_revision", "entrevista"]:
        assert client.patch(f"/api/v1/applications/{aid}", json={"status": status}).status_code == 200
    return aid


def test_hiring_availability_new_simulation_and_persistence(database):
    cid = prepare(database)
    aid = interview(cid)
    hired = client.patch(f"/api/v1/applications/{aid}", json={"status": "contratado"})
    assert hired.status_code == 200 and hired.json()["hired_at"]
    cid2 = client.post("/api/v1/profiles", json={}).json()["candidate_id"]
    assert apply(cid2).status_code == 409
    database.dispose()
    old = client.get("/api/v1/simulations").json()
    assert old["occupied_vacancy_ids"] == ["demo-01"]
    assert len(old["hires"]) == 1
    for confirmed in [False, "true", 1]:
        response = client.post("/api/v1/simulations", json={"confirmed": confirmed, "expected_current_id": old["current_id"]})
        assert response.status_code in (403, 422)
    result = client.post("/api/v1/simulations", json={"confirmed": True, "expected_current_id": old["current_id"]})
    assert result.status_code == 201
    new = result.json()
    assert new["current_id"] != old["current_id"]
    assert new["occupied_vacancy_ids"] == [] and new["hires"] == old["hires"]
    assert apply(cid, old["current_id"]).status_code == 409
    assert apply(cid, new["current_id"]).status_code == 201
    assert apply(cid).status_code == 409
    applications = client.get(f"/api/v1/profiles/{cid}/applications").json()
    assert len(applications) == 2
    assert len({a["simulation_id"] for a in applications}) == 2
    archived = next(a for a in applications if a["id"] == aid)
    assert not archived["is_current"] and archived["allowed_transitions"] == []
    assert client.patch(f"/api/v1/applications/{aid}", json={"status": "descartado"}).status_code == 409
    assert len(client.get(f"/api/v1/profiles/{cid}/reminders").json()) == 1
    database.dispose()
    assert client.get("/api/v1/simulations").json()["current_id"] == new["current_id"]


def test_simultaneous_hires_and_simulation_confirmation(database):
    first = prepare(database)
    second = client.post("/api/v1/profiles", json={}).json()["candidate_id"]
    ids = [interview(first), interview(second)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda aid: client.patch(f"/api/v1/applications/{aid}", json={"status": "contratado"}).status_code, ids))
    assert sorted(results) == [200, 409]
    sim = client.get("/api/v1/simulations").json()
    assert len(sim["hires"]) == 1
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post("/api/v1/simulations", json={"confirmed": True, "expected_current_id": sim["current_id"]}).status_code, range(2)))
    assert sorted(results) == [201, 409]


def test_upgrade_preserves_legacy_rows_and_does_not_invent_hire_dates(tmp_path):
    url = f'sqlite:///{tmp_path / "legacy.db"}'
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "0001")
    engine = make_engine(url)
    tables = ["candidates", "profiles", "vacancies", "applications", "reminders", "agent_logs"]
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO candidates VALUES ('c', '2025-01-01')"))
        conn.execute(text("INSERT INTO profiles VALUES ('p', 'c', 'd', '{}', 'groq', '2025-01-01')"))
        conn.execute(text("INSERT INTO vacancies VALUES ('v', '{}')"))
        conn.execute(text("INSERT INTO applications VALUES ('a', 'c', 'v', 'contratado', '2025-01-01', '{}')"))
        conn.execute(text("INSERT INTO reminders VALUES ('r', 'a', '2025-01-02', 'Histórico', 0)"))
        conn.execute(text("INSERT INTO agent_logs VALUES ('l', 'c', 'a', 'perfil', 'crear', 'ok', 'Histórico', 'p', '2025-01-01')"))
        before = {t: [dict(r) for r in conn.execute(text(f"SELECT * FROM {t}")).mappings()] for t in tables}
    engine.dispose()
    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        for table in tables:
            fields = ", ".join(before[table][0])
            assert [dict(r) for r in conn.execute(text(f"SELECT {fields} FROM {table}")).mappings()] == before[table]
        assert conn.execute(text("SELECT hired_at FROM applications")).scalar() is None
        assert not conn.execute(text("PRAGMA foreign_key_check")).all()
    engine.dispose()
