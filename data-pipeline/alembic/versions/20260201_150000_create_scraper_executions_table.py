"""create scraper_executions table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('scraper_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scraper_name', sa.String(length=100), nullable=False),
        sa.Column('source_country', sa.String(length=10), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('RUNNING', 'SUCCESS', 'FAILED', name='executionstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), nullable=True),
        sa.Column('records_inserted', sa.Integer(), nullable=True),
        sa.Column('records_skipped', sa.Integer(), nullable=True),
        sa.Column('output_file', sa.String(length=500), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scraper_executions_scraper_name', 'scraper_executions', ['scraper_name'])


def downgrade() -> None:
    op.drop_index('ix_scraper_executions_scraper_name', 'scraper_executions')
    op.drop_table('scraper_executions')
    op.execute("DROP TYPE IF EXISTS executionstatus")
