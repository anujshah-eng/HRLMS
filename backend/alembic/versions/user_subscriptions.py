"""transfer users to user_subscriptions table (NO-OP - subscriptions removed)

Revision ID: transfer_users_to_subscriptions
Revises: f08a1c19d1af
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'transfer_users_to_subscriptions'
down_revision = 'f08a1c19d1af'
branch_labels = None
depends_on = None

def upgrade():
    # NO-OP: Subscription features have been removed from this application
    # This migration is kept for version history but does nothing
    pass

def downgrade():
    # NO-OP: Nothing to downgrade
    pass
