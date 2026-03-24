"""create companies and company_relations tables

Revision ID: a1b2c3d4e5f6
Revises: 7364e076def2
Create Date: 2026-02-01 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7364e076def2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.String(length=20), nullable=False),  # JIB
        sa.Column('data_hash', sa.String(length=64), nullable=False),  # SHA256 hash
        sa.Column('company_short_name', sa.String(length=500), nullable=True),
        sa.Column('company_long_name', sa.String(length=500), nullable=True),
        sa.Column('municipality', sa.String(length=255), nullable=True),
        sa.Column('county', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('letter_of_activity', sa.String(length=10), nullable=True),
        sa.Column('activity_code', sa.String(length=50), nullable=True),
        sa.Column('activity_code_description', sa.String(length=500), nullable=True),
        sa.Column('registration_date', sa.DateTime(), nullable=True),
        sa.Column('is_public_entity', sa.Boolean(), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'data_hash', name='uq_company_id_data_hash')
    )
    op.create_index('ix_companies_company_id', 'companies', ['company_id'])

    # Create company_relations table
    op.create_table('company_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_record_id', sa.Integer(), nullable=False),
        sa.Column('data_hash', sa.String(length=64), nullable=False),
        sa.Column('relation_type_id', sa.Integer(), nullable=True),
        sa.Column('full_name', sa.String(length=500), nullable=True),
        sa.Column('share', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_record_id'], ['companies.id']),
        sa.UniqueConstraint('company_record_id', 'relation_type_id', 'full_name', 'data_hash',
                           name='uq_company_relation')
    )


def downgrade() -> None:
    # Drop company_relations first (has foreign key)
    op.drop_table('company_relations')
    op.drop_index('ix_companies_company_id', 'companies')
    op.drop_table('companies')
