"""add source column to company and widen long_name to text

Revision ID: b2c3d4e5f6g7
Revises: fc2860874b57
Create Date: 2026-02-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'fc2860874b57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Widen company_long_name from VARCHAR(500) to TEXT
    op.alter_column('company', 'company_long_name',
                     type_=sa.Text(), existing_type=sa.String(500), existing_nullable=True)

    # Add source column to company
    op.add_column('company', sa.Column('source', sa.String(20), nullable=True))
    op.create_index('ix_company_source', 'company', ['source'])

    # Widen company_import_skip.company_long_name from VARCHAR(500) to TEXT
    op.alter_column('company_import_skip', 'company_long_name',
                     type_=sa.Text(), existing_type=sa.String(500), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('company_import_skip', 'company_long_name',
                     type_=sa.String(500), existing_type=sa.Text(), existing_nullable=True)

    op.drop_index('ix_company_source', 'company')
    op.drop_column('company', 'source')

    op.alter_column('company', 'company_long_name',
                     type_=sa.String(500), existing_type=sa.Text(), existing_nullable=True)
