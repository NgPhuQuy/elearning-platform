"""Remove obsolete course certificate flag.

Revision ID: c3d4e5f6a7b8
Revises: b92e15823c10
"""

from alembic import op


revision = "c3d4e5f6a7b8"
down_revision = "b92e15823c10"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("course", "has_certificate")


def downgrade():
    import sqlalchemy as sa

    op.add_column(
        "course",
        sa.Column("has_certificate", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
