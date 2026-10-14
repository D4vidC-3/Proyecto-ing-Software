"""Validación local compartida por carga, extracción y generación de perfil."""
from contextlib import nullcontext
from pathlib import Path
from typing import BinaryIO
import zlib

from pypdf import PdfReader
from pypdf.errors import PyPdfError
from app.config import MAX_PDF_SIZE

MAX_PAGES = 10
MAX_TEXT_LENGTH = 20000


class PDFValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def extract_pdf_text(
    pdf_path: str | Path | BinaryIO, *, max_size_bytes: int = MAX_PDF_SIZE
) -> str:
    """Acepta una ruta existente o un temporal; nunca llama al proveedor de IA."""
    if isinstance(pdf_path, (str, Path)):
        path = Path(pdf_path)
        if not path.is_file():
            raise FileNotFoundError("El PDF no existe.")
        context = path.open("rb")
    else:
        context = nullcontext(pdf_path)

    with context as file:
        file.seek(0, 2)
        size = file.tell()
        if size == 0:
            raise PDFValidationError("El archivo está vacío (0 bytes). Selecciona un PDF con texto seleccionable.")
        if size > max_size_bytes:
            raise PDFValidationError(f"El PDF supera el límite configurado de {max_size_bytes} bytes.", 413)
        file.seek(0)
        if file.read(5) != b"%PDF-":
            raise PDFValidationError("El archivo no tiene una cabecera PDF válida. Cambiar la extensión no convierte una imagen en PDF.")
        file.seek(0)
        try:
            reader = PdfReader(file, strict=True)
            if reader.is_encrypted:
                raise PDFValidationError("El PDF está protegido con contraseña. Carga una copia sin protección y con texto seleccionable.")
            if len(reader.pages) > MAX_PAGES:
                raise PDFValidationError(f"El PDF supera el límite de {MAX_PAGES} páginas.")
            fragments = []
            length = 0
            for page in reader.pages:
                text = (page.extract_text() or "").strip()
                if text:
                    length += len(text) + (2 if fragments else 0)
                    if length > MAX_TEXT_LENGTH:
                        raise PDFValidationError("El texto extraído supera el límite de 20000 caracteres.")
                    fragments.append(text)
            result = "\n\n".join(fragments)
        except PDFValidationError:
            raise
        except (PyPdfError, ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError, zlib.error) as error:
            raise PDFValidationError("El documento PDF está dañado o no es válido. Carga otro PDF con texto seleccionable.") from error

    # No exigir datos de un CV completo: una palabra o un número ya es texto.
    if not any(character.isalnum() for character in result):
        raise PDFValidationError(
            "No se encontró texto útil. El PDF puede estar en blanco o contener solo imágenes. "
            "WORKINT no incluye OCR. Carga un PDF con texto seleccionable o crea el perfil manualmente."
        )
    return result
