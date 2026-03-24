"""Increase full_name column size in company_relation table

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # Change full_name from VARCHAR(500) to TEXT to handle long names
    op.alter_column(
        'company_relation',
        'full_name',
        existing_type=sa.String(500),
        type_=sa.Text(),
        existing_nullable=True
    )


def downgrade():
    # Revert back to VARCHAR(500)
    op.alter_column(
        'company_relation',
        'full_name',
        existing_type=sa.Text(),
        type_=sa.String(500),
        existing_nullable=True
    )
