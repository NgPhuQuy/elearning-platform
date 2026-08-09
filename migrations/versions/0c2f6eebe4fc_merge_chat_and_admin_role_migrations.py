"""merge chat and admin role migrations

Revision ID: 0c2f6eebe4fc
Revises: 264994eaf90f, b28a5bb370b2
Create Date: 2026-08-09 23:08:17.239338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c2f6eebe4fc'
down_revision = ('264994eaf90f', 'b28a5bb370b2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
