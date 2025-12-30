"""transfer users to usage_aggregations (NO-OP - feature removed)

Revision ID: usage_aggregations_setup
Revises: transfer_users_to_subscriptions
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'usage_aggregations_setup'
down_revision = 'transfer_users_to_subscriptions'
branch_labels = None
depends_on = None

def upgrade():
    # NO-OP: Usage aggregations feature has been removed from this application
    # This migration is kept for version history but does nothing
    pass

def downgrade():
    # NO-OP: Nothing to downgrade
    pass
