"""drop interview_rounds and target_companies tables

Revision ID: e05712be3260
Revises: fe220eb6178c
Create Date: 2025-12-29 16:20:18.990910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e05712be3260'
down_revision: Union[str, Sequence[str], None] = 'fe220eb6178c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop interview_rounds and target_companies tables."""
    op.execute("DROP TABLE IF EXISTS interview_rounds CASCADE")
    op.execute("DROP TABLE IF EXISTS target_companies CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    # Cannot restore dropped tables
    pass
