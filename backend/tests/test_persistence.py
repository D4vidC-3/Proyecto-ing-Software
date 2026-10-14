from fastapi.testclient import TestClient
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
import main
from app.models.entities import Profile
from app.models.candidate_profile import CandidateProfile
from app.services.profile_gaps import profile_gaps

client = TestClient(main.app)


def test_profile_crud_and_new_connection(database):
    created = client.post(
        "/api/v1/profiles", json={"name": "Demo", "skills": ["Python"]}
    )
    assert created.status_code == 201
    cid = created.json()["candidate_id"]
    assert created.json()["source"] == "manual"
    url = f"/api/v1/profiles/{cid}"
    assert client.get(url).json()["profile"]["name"] == "Demo"
    assert len(client.get("/api/v1/profiles").json()) == 1
    assert (
        client.put(
            url, json={"name": "Corregido", "preferences": {"work_modes": ["remoto"]}}
        ).status_code
        == 200
    )
    database.dispose()
    with Session(database) as session:
        assert session.scalar(select(Profile)).data["name"] == "Corregido"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.get("/api/v1/profiles").json() == []


def test_migration_tables(database):
    assert set(inspect(database).get_table_names()) == {
        "alembic_version",
        "candidates",
        "profiles",
        "vacancies",
        "applications",
        "reminders",
        "agent_logs",
        "simulations",
    }


def test_unknown_and_optional_gaps():
    gaps = profile_gaps(CandidateProfile(name="  ", years_experience=0))
    assert next(g for g in gaps if g["field"] == "name")["missing"]
    assert not next(g for g in gaps if g["field"] == "experience")["missing"]
    assert next(g for g in gaps if g["field"] == "salary")["importance"] == "opcional"


def test_profile_invalid_salary_and_ids():
    assert (
        client.post(
            "/api/v1/profiles",
            json={"preferences": {"salary_min_cop": 5, "salary_max_cop": 3}},
        ).status_code
        == 422
    )
    assert client.get("/api/v1/profiles/invalid").status_code == 422
    assert client.get("/api/v1/profiles/" + "a" * 32).status_code == 404
