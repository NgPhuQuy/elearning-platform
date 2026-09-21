"""Restore course certificate setting.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

import sqlalchemy as sa
from alembic import op


revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "course",
        sa.Column("has_certificate", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade():
    op.drop_column("course", "has_certificate")
