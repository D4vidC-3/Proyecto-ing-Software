from alembic import context
from app.database import Base, DATABASE_URL, make_engine
from app.models import entities  # noqa: F401

config = context.config
from app.config import check_database, resolve_database_url

url = resolve_database_url(config.attributes.get("database_url", DATABASE_URL))
print(f"Alembic - base efectiva: {check_database(url)}", flush=True)
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    with engine.connect() as connection:
        # SQLite batch recrea applications. Desactivar FK solo en esta conexión
        # evita cascadas sobre recordatorios/logs; validar antes de confirmar.
        sqlite = connection.dialect.name == "sqlite"
        if sqlite:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
            connection.exec_driver_sql("BEGIN")
        context.configure(
            connection=connection, target_metadata=Base.metadata, compare_type=True,
            transactional_ddl=sqlite,
        )
        try:
            with context.begin_transaction():
                context.run_migrations()
            if sqlite and connection.exec_driver_sql("PRAGMA foreign_key_check").first():
                raise RuntimeError("La migración viola relaciones existentes; se revierte")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    engine.dispose()
