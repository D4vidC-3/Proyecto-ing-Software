"""Esquema inicial MVP. Snapshot independiente de los modelos futuros."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(32),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("document_id", sa.String(32), unique=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "vacancies",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(32),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id", sa.String(32), sa.ForeignKey("vacancies.id"), nullable=False
        ),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.UniqueConstraint("candidate_id", "vacancy_id", name="uq_candidate_vacancy"),
    )
    op.create_index("ix_applications_candidate_id", "applications", ["candidate_id"])
    op.create_table(
        "reminders",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "application_id",
            sa.String(32),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("pending", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "agent_logs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "candidate_id",
            sa.String(32),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "application_id",
            sa.String(32),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
        ),
        sa.Column("agent", sa.String(40), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("result_ref", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_logs_candidate_id", "agent_logs", ["candidate_id"])
    op.create_index("ix_agent_logs_application_id", "agent_logs", ["application_id"])


def downgrade():
    for table in [
        "agent_logs",
        "reminders",
        "applications",
        "vacancies",
        "profiles",
        "candidates",
    ]:
        op.drop_table(table)
