"""Add tenant_id to users table (NO-OP - users table not in HRLMS)

Revision ID: add_tenant_to_users
Revises: f08a1c19d1af
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_tenant_to_users'
down_revision: Union[str, Sequence[str], None] = 'f08a1c19d1af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # NO-OP: Users table doesn't exist in HRLMS (AI Interview Management only)
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # NO-OP: Nothing to downgrade
    pass
