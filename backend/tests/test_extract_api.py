
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import main

client = TestClient(main.app)


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return tmp_path


def create_test_pdf():
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, "Sofia Rios")
    pdf.drawString(72, 720, "Python FastAPI PostgreSQL")
    pdf.save()

    return buffer.getvalue()


def test_upload_and_extract(storage):
    upload = client.post(
        "/api/v1/cv/upload",
        files={
            "file": (
                "cv.pdf",
                create_test_pdf(),
                "application/pdf",
            )
        },
    )

    assert upload.status_code == 201

    document_id = upload.json()["document_id"]

    response = client.post(
        f"/api/v1/cv/{document_id}/extract"
    )

    assert response.status_code == 200

    data = response.json()

    assert "Sofia Rios" in data["text"]
    assert "Python FastAPI PostgreSQL" in data["text"]
    assert data["status"] == "extracted"
    assert data["characters"] == len(data["text"])


def test_document_not_found(storage):
    document_id = "a" * 32

    response = client.post(
        f"/api/v1/cv/{document_id}/extract"
    )

    assert response.status_code == 404


def test_invalid_document_id(storage):
    response = client.post(
        "/api/v1/cv/invalid-id/extract"
    )

    assert response.status_code == 422
  
