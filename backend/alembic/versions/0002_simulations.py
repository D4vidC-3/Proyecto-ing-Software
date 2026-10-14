"""Separación mínima de simulaciones; no inventa fechas de contratación."""
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None
INITIAL = "00000000000000000000000000000001"


def upgrade():
    simulations = op.create_table(
        "simulations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.bulk_insert(simulations, [{"id": INITIAL, "created_at": datetime.now(timezone.utc), "active": True}])
    op.create_index("uq_active_simulation", "simulations", ["active"], unique=True, sqlite_where=sa.text("active = 1"))
    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("simulation_id", sa.String(32), nullable=False, server_default=INITIAL))
        batch.add_column(sa.Column("hired_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_application_simulation", "simulations", ["simulation_id"], ["id"])
        batch.drop_constraint("uq_candidate_vacancy", type_="unique")
        batch.create_unique_constraint("uq_simulation_candidate_vacancy", ["simulation_id", "candidate_id", "vacancy_id"])


def downgrade():
    # No descartar ni fusionar postulaciones al volver al esquema anterior.
    duplicates = op.get_bind().execute(sa.text(
        "SELECT 1 FROM applications GROUP BY candidate_id, vacancy_id HAVING count(*) > 1 LIMIT 1"
    )).first()
    if duplicates:
        raise RuntimeError("No se puede revertir sin perder historial de simulaciones")
    with op.batch_alter_table("applications") as batch:
        batch.drop_constraint("uq_simulation_candidate_vacancy", type_="unique")
        batch.drop_constraint("fk_application_simulation", type_="foreignkey")
        batch.drop_column("simulation_id")
        batch.drop_column("hired_at")
        batch.create_unique_constraint("uq_candidate_vacancy", ["candidate_id", "vacancy_id"])
    op.drop_table("simulations")
