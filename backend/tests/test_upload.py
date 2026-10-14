
import pytest
import main

from fastapi.testclient import TestClient

client = TestClient(main.app)

URL = "/api/v1/cv/upload"


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return tmp_path


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_pdf(storage):
    from io import BytesIO
    from reportlab.pdfgen import canvas
    buffer = BytesIO()
    document = canvas.Canvas(buffer)
    document.drawString(72, 750, "CV de prueba con texto seleccionable")
    document.save()
    pdf = buffer.getvalue()

    response = client.post(
        URL,
        files={
            "file": (
                "cv.pdf",
                pdf,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "cv.pdf"
    assert data["size_bytes"] == len(pdf)

    saved_file = storage / (
        data["document_id"] + ".pdf"
    )

    assert saved_file.exists()
    assert saved_file.read_bytes() == pdf


def test_reject_invalid_extension(storage):
    response = client.post(
        URL,
        files={
            "file": (
                "cv.txt",
                b"Texto de prueba",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert list(storage.iterdir()) == []


def test_reject_invalid_pdf_header(storage):
    response = client.post(
        URL,
        files={
            "file": (
                "falso.pdf",
                b"Esto no es un PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422
    assert list(storage.iterdir()) == []


def test_reject_large_pdf(storage):
    pdf = b"%PDF-" + b"A" * (5 * 1024 * 1024)

    response = client.post(
        URL,
        files={
            "file": (
                "grande.pdf",
                pdf,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert list(storage.iterdir()) == []


def test_missing_file():
    response = client.post(URL)

    assert response.status_code == 422
