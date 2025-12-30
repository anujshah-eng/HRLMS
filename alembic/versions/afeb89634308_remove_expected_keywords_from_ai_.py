"""remove expected_keywords from ai_interview_questions

Revision ID: afeb89634308
Revises: e05712be3260
Create Date: 2025-12-30 15:24:10.876499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afeb89634308'
down_revision: Union[str, Sequence[str], None] = 'e05712be3260'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop expected_keywords column from ai_interview_questions table."""
    op.drop_column('ai_interview_questions', 'expected_keywords')


def downgrade() -> None:
    """Restore expected_keywords column."""
    op.add_column('ai_interview_questions', 
        sa.Column('expected_keywords', sa.String(length=500), nullable=True)
    )
