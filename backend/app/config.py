"""Configuración local compartida por API, Alembic e ingesta."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=False)


def local_path(value):
    path = Path(value).expanduser()
    return (BACKEND_DIR / path).resolve() if not path.is_absolute() else path.resolve()


def resolve_database_url(value):
    url = make_url(value)
    if url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:"):
        url = url.set(database=str(local_path(url.database)))
    return url.render_as_string(hide_password=False)


def check_database(value):
    url = make_url(resolve_database_url(value))
    path = Path(url.database) if url.get_backend_name() == "sqlite" and url.database not in (None, "", ":memory:") else None
    if os.getenv("WORKINT_SCENARIOS") == "1" and path is not None:
        historical = BACKEND_DIR / "workint.db"
        if path.resolve() == historical.resolve() or (path.exists() and historical.exists() and path.samefile(historical)):
            raise RuntimeError("Operación detenida: la base histórica workint.db está protegida en modo escenarios")
    return str(path) if path else url.render_as_string(hide_password=True)


DATABASE_URL = resolve_database_url(os.getenv("WORKINT_DATABASE_URL", "sqlite:///workint.db"))
UPLOAD_DIR = local_path(os.getenv("WORKINT_UPLOAD_DIR", "uploads"))
VACANCIES_PATH = local_path(os.getenv("WORKINT_VACANCIES_PATH", "app/data/vacancies.json"))

# Límite compartido por la carga y la validación directa de documentos.
MAX_PDF_SIZE = int(os.getenv("WORKINT_MAX_PDF_BYTES", str(5 * 1024 * 1024)))
if MAX_PDF_SIZE <= 0:
    raise ValueError("WORKINT_MAX_PDF_BYTES debe ser un entero positivo")
