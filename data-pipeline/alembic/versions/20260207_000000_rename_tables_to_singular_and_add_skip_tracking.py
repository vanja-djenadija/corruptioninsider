"""rename tables to singular and add company_import_skip

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables to singular form
    op.rename_table('awards_raw', 'award_raw')
    op.rename_table('companies', 'company')
    op.rename_table('company_relations', 'company_relation')
    op.rename_table('scraper_executions', 'scraper_execution')

    # Update foreign key constraint for company_relation
    op.drop_constraint('company_relations_company_record_id_fkey', 'company_relation', type_='foreignkey')
    op.create_foreign_key(
        'company_relation_company_record_id_fkey',
        'company_relation', 'company',
        ['company_record_id'], ['id']
    )

    # Update index names
    op.drop_index('ix_companies_company_id', 'company')
    op.create_index('ix_company_company_id', 'company', ['company_id'])

    op.drop_index('ix_scraper_executions_scraper_name', 'scraper_execution')
    op.create_index('ix_scraper_execution_scraper_name', 'scraper_execution', ['scraper_name'])

    # Create company_import_skip table
    op.create_table(
        'company_import_skip',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('import_batch_id', sa.String(length=50), nullable=False),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('company_id', sa.String(length=20), nullable=True),
        sa.Column('company_short_name', sa.String(length=500), nullable=True),
        sa.Column('company_long_name', sa.String(length=500), nullable=True),
        sa.Column('skip_reason', sa.String(length=100), nullable=False),
        sa.Column('skip_details', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('skipped_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_import_skip_import_batch_id', 'company_import_skip', ['import_batch_id'])
    op.create_index('ix_company_import_skip_skip_reason', 'company_import_skip', ['skip_reason'])


def downgrade() -> None:
    # Drop company_import_skip table
    op.drop_index('ix_company_import_skip_skip_reason', table_name='company_import_skip')
    op.drop_index('ix_company_import_skip_import_batch_id', table_name='company_import_skip')
    op.drop_table('company_import_skip')

    # Restore index names
    op.drop_index('ix_scraper_execution_scraper_name', 'scraper_execution')
    op.create_index('ix_scraper_executions_scraper_name', 'scraper_execution', ['scraper_name'])

    op.drop_index('ix_company_company_id', 'company')
    op.create_index('ix_companies_company_id', 'company', ['company_id'])

    # Restore foreign key constraint
    op.drop_constraint('company_relation_company_record_id_fkey', 'company_relation', type_='foreignkey')
    op.create_foreign_key(
        'company_relations_company_record_id_fkey',
        'company_relation', 'company',
        ['company_record_id'], ['id']
    )

    # Rename tables back to plural form
    op.rename_table('scraper_execution', 'scraper_executions')
    op.rename_table('company_relation', 'company_relations')
    op.rename_table('company', 'companies')
    op.rename_table('award_raw', 'awards_raw')
