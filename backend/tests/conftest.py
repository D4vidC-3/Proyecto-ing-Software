"""Cada prueba usa SQLite en disco migrada, nunca la BD de demostración."""

import pytest
from alembic import command
from alembic.config import Config
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import make_engine, get_db


@pytest.fixture(autouse=True)
def database(tmp_path_factory, monkeypatch):
    import main

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path_factory.mktemp("uploads"))
    # Fallar antes de cualquier transporte real, incluso si se filtra una clave.
    from groq._base_client import SyncAPIClient, AsyncAPIClient

    def no_provider(*args, **kwargs):
        raise AssertionError("Pytest no permite llamadas reales a Groq")

    monkeypatch.setattr(SyncAPIClient, "request", no_provider)
    monkeypatch.setattr(AsyncAPIClient, "request", no_provider)
    url = f'sqlite:///{tmp_path_factory.mktemp("database") / "test.db"}'
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    engine = make_engine(url)

    def session():
        with Session(engine) as db:
            yield db

    main.app.dependency_overrides[get_db] = session
    from app.services.execution_trace import extraction_context

    def simulated_context():
        return {**extraction_context(), "execution_mode": "simulated", "metadata_status": "test_context"}

    main.app.dependency_overrides[extraction_context] = simulated_context
    yield engine
    main.app.dependency_overrides.clear()
    engine.dispose()
