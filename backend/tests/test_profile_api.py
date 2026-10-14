
from io import BytesIO
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import main
from app.models.candidate_profile import CandidateProfile


client = TestClient(main.app)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return tmp_path


def create_test_pdf():
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, "Sofia Rios")
    pdf.drawString(72, 720, "Desarrolladora Backend")
    pdf.drawString(72, 690, "Python FastAPI PostgreSQL")
    pdf.save()

    return buffer.getvalue()


def upload_document():
    response = client.post(
        "/api/v1/cv/upload",
        files={
            "file": (
                "cv-ficticio.pdf",
                create_test_pdf(),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    return response.json()["document_id"]


def test_generate_profile_successfully(storage, monkeypatch):
    fake_profile = CandidateProfile(
        name="Sofia Rios",
        target_role="Desarrolladora Backend",
        skills=["Python", "FastAPI", "PostgreSQL"],
    )

    fake_extractor = Mock(return_value=fake_profile)

    monkeypatch.setattr(
        main,
        "extract_candidate_profile",
        fake_extractor,
    )

    document_id = upload_document()

    response = client.post(
        f"/api/v1/cv/{document_id}/profile",
        json={"consent_external_processing": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_id"] == document_id
    assert data["status"] == "structured"
    assert data["profile"]["name"] == "Sofia Rios"
    assert "FastAPI" in data["profile"]["skills"]

    fake_extractor.assert_called_once()


def test_profile_requires_consent(storage, monkeypatch):
    fake_extractor = Mock()

    monkeypatch.setattr(
        main,
        "extract_candidate_profile",
        fake_extractor,
    )

    document_id = upload_document()

    response = client.post(
        f"/api/v1/cv/{document_id}/profile",
        json={"consent_external_processing": False},
    )

    assert response.status_code == 403

    fake_extractor.assert_not_called()


def test_profile_invalid_document_id(storage):
    response = client.post(
        "/api/v1/cv/invalid-id/profile",
        json={"consent_external_processing": True},
    )

    assert response.status_code == 422


def test_profile_document_not_found(storage):
    document_id = "a" * 32

    response = client.post(
        f"/api/v1/cv/{document_id}/profile",
        json={"consent_external_processing": True},
    )

    assert response.status_code == 404


def test_profile_ai_unavailable(storage, monkeypatch):
    fake_extractor = Mock(
        side_effect=RuntimeError(
            "El servicio de IA no esta configurado."
        )
    )

    monkeypatch.setattr(
        main,
        "extract_candidate_profile",
        fake_extractor,
    )

    document_id = upload_document()

    response = client.post(
        f"/api/v1/cv/{document_id}/profile",
        json={"consent_external_processing": True},
    )

    assert response.status_code == 503
