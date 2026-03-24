"""merge all heads

Revision ID: fc2860874b57
Revises: 49428a807577, d4e5f6g7h8i9
Create Date: 2026-02-09 20:00:38.121786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc2860874b57'
down_revision: Union[str, None] = ('49428a807577', 'd4e5f6g7h8i9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
