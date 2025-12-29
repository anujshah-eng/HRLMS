"""drop unused tables

Revision ID: fe220eb6178c
Revises: 262415033bae
Create Date: 2025-12-29 16:08:32.240218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe220eb6178c'
down_revision: Union[str, Sequence[str], None] = '262415033bae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop all unused tables that are not part of AI Interview Management."""
    # Drop tables in reverse dependency order to avoid foreign key constraints
    
    # Drop child tables first
    op.execute("DROP TABLE IF EXISTS materials CASCADE")
    op.execute("DROP TABLE IF EXISTS announcement_classroom_association CASCADE")
    op.execute("DROP TABLE IF EXISTS classroom_items CASCADE")
    op.execute("DROP TABLE IF EXISTS classroom_members CASCADE")
    op.execute("DROP TABLE IF EXISTS user_content_visits CASCADE")
    op.execute("DROP TABLE IF EXISTS student_batches CASCADE")
    op.execute("DROP TABLE IF EXISTS teacher_departments CASCADE")
    op.execute("DROP TABLE IF EXISTS tenant_invites CASCADE")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS user_subscriptions CASCADE")
    op.execute("DROP TABLE IF EXISTS tenant_invitations CASCADE")
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS teacher_notifications CASCADE")
    op.execute("DROP TABLE IF EXISTS usage_alerts CASCADE")
    op.execute("DROP TABLE IF EXISTS usage_aggregations CASCADE")
    op.execute("DROP TABLE IF EXISTS refresh_tokens CASCADE")
    
    # Drop parent tables
    op.execute("DROP TABLE IF EXISTS announcements CASCADE")
    op.execute("DROP TABLE IF EXISTS classrooms CASCADE")
    op.execute("DROP TABLE IF EXISTS batches CASCADE")
    op.execute("DROP TABLE IF EXISTS teachers CASCADE")
    op.execute("DROP TABLE IF EXISTS departments CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS usage_quotas CASCADE")
    op.execute("DROP TABLE IF EXISTS subscription_plans CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_events CASCADE")
    op.execute("DROP TABLE IF EXISTS roles CASCADE")
    op.execute("DROP TABLE IF EXISTS designations CASCADE")
    op.execute("DROP TABLE IF EXISTS tenants CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    # Cannot restore dropped tables
    pass
