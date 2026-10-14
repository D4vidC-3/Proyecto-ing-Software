"""Contexto de operaciones nuevas; registros históricos sin atribución retroactiva."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_logs", sa.Column("operation_id", sa.String(32), nullable=True))
    op.add_column("agent_logs", sa.Column("execution_context", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("agent_logs") as batch:
        batch.drop_column("operation_id")
        batch.drop_column("execution_context")
