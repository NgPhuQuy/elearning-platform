"""add has_certificate to course table

Revision ID: b92e15823c10
Revises: a87f23734bff
Create Date: 2026-09-21 18:28:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b92e15823c10'
down_revision = 'a87f23734bff'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('course', sa.Column('has_certificate', sa.Boolean(), nullable=True, server_default=sa.text('0')))


def downgrade():
    op.drop_column('course', 'has_certificate')

