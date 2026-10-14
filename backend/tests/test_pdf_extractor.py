
import pytest

from reportlab.pdfgen import canvas
from pypdf import PdfWriter

from app.services.pdf_extractor import extract_pdf_text


def test_extract_text_from_pdf(tmp_path):
    path = tmp_path / "cv.pdf"

    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 750, "Juan Perez")
    pdf.drawString(72, 720, "Experiencia: Desarrollador Python")
    pdf.drawString(72, 690, "Habilidades: Python, SQL, Git")
    pdf.save()

    text = extract_pdf_text(path)

    assert "Juan Perez" in text
    assert "Desarrollador Python" in text
    assert "Python, SQL, Git" in text


def test_reject_pdf_without_text(tmp_path):
    path = tmp_path / "blank.pdf"

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with path.open("wb") as file:
        writer.write(file)

    with pytest.raises(ValueError, match="No se encontró texto útil"):
        extract_pdf_text(path)


def test_reject_damaged_pdf(tmp_path):
    path = tmp_path / "damaged.pdf"
    path.write_bytes(b"%PDF-Documento-invalido")

    with pytest.raises(ValueError):
        extract_pdf_text(path)


def test_missing_pdf(tmp_path):
    path = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        extract_pdf_text(path)
