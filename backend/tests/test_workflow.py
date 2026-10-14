import json
from pathlib import Path
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
import main
from app.models.entities import (
    Vacancy,
    Application,
    Reminder,
    AgentLog,
    Candidate,
    Profile,
)
from app.models.candidate_profile import CandidateProfile
from app.services.vacancies import ingest, DATASET
from app.services.matching import score

client = TestClient(main.app)


@pytest.fixture
def seeded(database):
    with Session(database) as db:
        assert ingest(db) == 18
        db.commit()
    return database


def profile():
    response = client.post(
        "/api/v1/profiles",
        json={
            "name": "Demo",
            "target_role": "Desarrolladora Backend Python",
            "location": "Medellín",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "preferences": {
                "work_modes": ["híbrido", "remoto"],
                "salary_min_cop": 4500000,
                "salary_max_cop": 5500000,
            },
        },
    )
    assert response.status_code == 201
    return response.json()["candidate_id"]


def apply(cid, confirmed=True, vacancy="demo-01"):
    return client.post(
        "/api/v1/applications",
        json={"candidate_id": cid, "vacancy_id": vacancy, "confirmed": confirmed},
    )


def test_ingestion_idempotent_and_source_atomic(seeded, tmp_path):
    with Session(seeded) as db:
        ingest(db)
        db.commit()
        assert db.scalar(select(func.count()).select_from(Vacancy)) == 18
        p = tmp_path / "bad.json"
        p.write_text('[{"id":"broken"}]')
        with pytest.raises(ValueError):
            ingest(db, p)
        assert db.scalar(select(func.count()).select_from(Vacancy)) == 18
        p.write_text("not json")
        with pytest.raises(ValueError):
            ingest(db, p)
        with pytest.raises(FileNotFoundError):
            ingest(db, tmp_path / "absent")


def test_normalization_and_missing_vacancy_data(seeded):
    from app.models.contracts import VacancyData

    v = json.loads(DATASET.read_text())[0]
    v["work_mode"] = " HÍBRIDO "
    v["required_skills"] = ["Python", " Python ", ""]
    clean = VacancyData.model_validate(v)
    assert clean.work_mode == "hibrido" and clean.required_skills == ["Python"]
    assert client.get("/api/v1/vacancies/demo-15").json()["salary_min_cop"] is None
    assert client.get("/api/v1/vacancies/demo-99").status_code == 404
    assert client.get("/api/v1/vacancies/no").status_code == 422


def test_scoring_exact_and_unknown():
    v = json.loads(DATASET.read_text())[0]
    p = CandidateProfile(
        target_role=v["title"],
        skills=v["required_skills"],
        location="Medellin",
        preferences={
            "work_modes": ["híbrido"],
            "salary_min_cop": 4500000,
            "salary_max_cop": 5500000,
        },
    )
    result = score(p, v)
    assert result["score"] == 100
    assert sum(c["points"] for c in result["components"]) == 100
    assert result["missing_skills"] == []
    result = score(CandidateProfile(), v)
    assert result["score"] == 0
    assert len(result["unknown"]) == 5
    p.skills = ["Python"]
    result = score(p, v)
    assert result["score"] == 70
    assert result["matched_skills"] == ["python"]
    assert result["missing_skills"] == ["fastapi", "postgresql"]


def test_scoring_incompatible_and_unknown_salary():
    v = json.loads(DATASET.read_text())[0]
    p = CandidateProfile(
        location="Cali",
        preferences={"work_modes": ["presencial"], "salary_min_cop": 9000000},
    )
    result = score(p, v)
    assert result["score"] == 0 and "salary" not in result["unknown"]
    v["salary_max_cop"] = None
    assert "salary" in score(p, v)["unknown"]


def test_ranking_and_persisted_trace(seeded):
    cid = profile()
    results = client.get(f"/api/v1/profiles/{cid}/recommendations").json()
    assert len(results) == 18
    assert [r["score"] for r in results] == sorted(
        [r["score"] for r in results], reverse=True
    )
    assert results[0]["vacancy"]["id"] == "demo-01"
    assert len(client.get("/api/v1/vacancies").json()) == 18
    logs = client.get(f"/api/v1/profiles/{cid}/activity").json()
    assert {"perfil", "vacantes"} <= {l["agent"] for l in logs}


@pytest.mark.parametrize("confirmation", [False, None, "true", 1])
def test_requires_strict_confirmation(seeded, confirmation):
    cid = profile()
    response = apply(cid, confirmation)
    assert response.status_code in (403, 422)
    with Session(seeded) as db:
        assert db.scalar(select(func.count()).select_from(Application)) == 0
        assert db.scalar(select(func.count()).select_from(Reminder)) == 0


def test_application_lifecycle_evidence_and_cascade(seeded):
    cid = profile()
    response = apply(cid)
    assert response.status_code == 201
    app = response.json()
    aid = app["id"]
    assert app["status"] == "postulado" and app["evidence"]["type"] == "simulada"
    assert app["evidence"]["confirmed"] is True
    evidence = app["evidence"]
    assert apply(cid).status_code == 409
    assert (
        client.patch(
            f"/api/v1/applications/{aid}", json={"status": "entrevista"}
        ).status_code
        == 409
    )
    for status in ["en_revision", "entrevista", "descartado"]:
        result = client.patch(f"/api/v1/applications/{aid}", json={"status": status})
        assert result.status_code == 200
        assert result.json()["evidence"] == evidence
    assert (
        client.patch(
            f"/api/v1/applications/{aid}", json={"status": "postulado"}
        ).status_code
        == 409
    )
    seeded.dispose()
    with Session(seeded) as db:
        assert db.get(Application, aid).status == "descartado"
        reminders = list(db.scalars(select(Reminder)))
        assert len(reminders) == 1 and not reminders[0].pending
    logs = client.get(f"/api/v1/profiles/{cid}/activity").json()
    changes = [l for l in logs if l["action"] == "cambio_estado"]
    assert len(changes) == 3
    assert [l["created_at"] for l in logs] == sorted(l["created_at"] for l in logs)
    assert {"perfil", "postulacion", "seguimiento"} <= {l["agent"] for l in logs}
    assert "Demo" not in json.dumps(logs)
    assert len(client.get(f"/api/v1/profiles/{cid}/applications").json()) == 1
    assert client.delete(f"/api/v1/profiles/{cid}").status_code == 204
    with Session(seeded) as db:
        for model in [Candidate, Profile, Application, Reminder, AgentLog]:
            # Ingesta global permanece, sin información de candidato.
            query = select(func.count()).select_from(model)
            if model is AgentLog:
                query = query.where(AgentLog.candidate_id.is_not(None))
            assert db.scalar(query) == 0
        assert db.scalar(select(func.count()).select_from(Vacancy)) == 18


def test_reminder_and_errors(seeded):
    cid = profile()
    app = apply(cid).json()
    reminders = client.get(f"/api/v1/profiles/{cid}/reminders").json()
    assert len(reminders) == 1 and reminders[0]["pending"]
    assert reminders[0]["due_at"] > app["created_at"]
    assert apply(cid, True, "demo-99").status_code == 404
    assert apply("a" * 32).status_code == 404
    assert (
        client.patch(
            "/api/v1/applications/" + "a" * 32, json={"status": "descartado"}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f'/api/v1/applications/{app["id"]}', json={"status": "inventado"}
        ).status_code
        == 422
    )


def test_cors_for_update_delete():
    for method in ["PUT", "PATCH", "DELETE"]:
        r = client.options(
            "/api/v1/profiles",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": method,
            },
        )
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    r = client.options(
        "/api/v1/profiles",
        headers={
            "Origin": "https://other.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.status_code == 400


def test_migration_down_up(tmp_path):
    from app.database import make_engine
    from sqlalchemy import inspect

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = f'sqlite:///{tmp_path / "migration.db"}'
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = make_engine(config.attributes["database_url"])
    assert "profiles" in inspect(engine).get_table_names()
    engine.dispose()


def test_extraction_retry_preserves_edits(database, tmp_path, monkeypatch):
    from reportlab.pdfgen import canvas
    from io import BytesIO

    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    fake = Mock(return_value=CandidateProfile(name="Extraído", skills=["Python"]))
    monkeypatch.setattr(main, "extract_candidate_profile", fake)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(40, 700, "CV ficticio")
    pdf.save()
    doc = client.post(
        "/api/v1/cv/upload",
        files={"file": ("cv.pdf", buffer.getvalue(), "application/pdf")},
    ).json()["document_id"]
    path = f"/api/v1/cv/{doc}/profile"
    first = client.post(path, json={"consent_external_processing": True})
    assert first.status_code == 200
    cid = first.json()["candidate_id"]
    client.put(f"/api/v1/profiles/{cid}", json={"name": "Corregido"})
    second = client.post(path, json={"consent_external_processing": True})
    assert second.json()["profile"]["name"] == "Corregido"
    assert second.json()["candidate_id"] == cid
    assert fake.call_count == 1


def test_failed_provider_manual_fallback(database, tmp_path, monkeypatch):
    from reportlab.pdfgen import canvas
    from io import BytesIO

    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_candidate_profile",
        Mock(side_effect=RuntimeError("not configured")),
    )
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(40, 700, "CV ficticio")
    pdf.save()
    doc = client.post(
        "/api/v1/cv/upload",
        files={"file": ("cv.pdf", buffer.getvalue(), "application/pdf")},
    ).json()["document_id"]
    assert (
        client.post(
            f"/api/v1/cv/{doc}/profile", json={"consent_external_processing": True}
        ).status_code
        == 503
    )
    assert (
        client.post("/api/v1/profiles", json={"name": "Manual"}).json()["source"]
        == "manual"
    )


def test_integrated_pdf_graph_to_followup(seeded, tmp_path, monkeypatch):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from app.services.profile_extractor import extract_candidate_profile

    class Model:
        def with_structured_output(self, schema, method):
            assert method == "json_schema"
            return self

        def invoke(self, messages):
            assert "CV ficticio Python" in messages[-1].content
            return {"name": "Demo integrada", "skills": ["Python"], "preferences": None}

    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(
        main,
        "extract_candidate_profile",
        lambda text: extract_candidate_profile(text, llm=Model()),
    )
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(40, 700, "CV ficticio Python")
    pdf.save()
    uploaded = client.post(
        "/api/v1/cv/upload",
        files={"file": ("cv.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert uploaded.status_code == 201
    doc = uploaded.json()["document_id"]
    assert client.post(f"/api/v1/cv/{doc}/extract").status_code == 200
    assert (
        client.post(
            f"/api/v1/cv/{doc}/profile", json={"consent_external_processing": "true"}
        ).status_code
        == 422
    )
    generated = client.post(
        f"/api/v1/cv/{doc}/profile", json={"consent_external_processing": True}
    )
    assert generated.status_code == 200
    cid = generated.json()["candidate_id"]
    saved = client.get(f"/api/v1/profiles/{cid}").json()
    assert any(g["missing"] for g in saved["gaps"])
    data = saved["profile"]
    data["location"] = "Medellín"
    data["preferences"]["work_modes"] = ["remoto"]
    assert client.put(f"/api/v1/profiles/{cid}", json=data).status_code == 200
    recommendation = client.get(f"/api/v1/profiles/{cid}/recommendations").json()[0]
    applied = apply(cid, True, recommendation["vacancy"]["id"])
    assert applied.status_code == 201
    assert client.get(f"/api/v1/profiles/{cid}/reminders").json()[0]["pending"]
    assert {"perfil", "vacantes", "postulacion", "seguimiento"} == {
        l["agent"] for l in client.get(f"/api/v1/profiles/{cid}/activity").json()
    }


def test_invalid_provider_output_is_controlled(tmp_path, monkeypatch):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from pydantic import ValidationError

    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)

    def invalid(text):
        return CandidateProfile.model_validate({"years_experience": -1})

    monkeypatch.setattr(main, "extract_candidate_profile", invalid)
    b = BytesIO()
    p = canvas.Canvas(b)
    p.drawString(40, 700, "Ficticio")
    p.save()
    doc = client.post(
        "/api/v1/cv/upload", files={"file": ("cv.pdf", b.getvalue(), "application/pdf")}
    ).json()["document_id"]
    assert (
        client.post(
            f"/api/v1/cv/{doc}/profile", json={"consent_external_processing": True}
        ).status_code
        == 502
    )
