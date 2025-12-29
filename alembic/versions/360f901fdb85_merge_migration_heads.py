"""merge migration heads

Revision ID: 360f901fdb85
Revises: add_tenant_to_users, usage_aggregations_setup
Create Date: 2025-12-29 15:35:13.695920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '360f901fdb85'
down_revision: Union[str, Sequence[str], None] = ('add_tenant_to_users', 'usage_aggregations_setup')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
