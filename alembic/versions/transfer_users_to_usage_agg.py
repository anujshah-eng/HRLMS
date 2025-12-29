"""transfer users to usage_aggregations

Revision ID: usage_aggregations_setup
Revises: transfer_users_to_subscriptions
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

# revision identifiers, used by Alembic
revision = 'usage_aggregations_setup'
down_revision = 'transfer_users_to_subscriptions'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    print("Starting user data migration to usage_aggregations...")
    
    # Check if data already exists to avoid duplicates
    existing_count = conn.execute(text(
        'SELECT COUNT(*) FROM usage_aggregations'
    )).scalar()
    
    if existing_count > 0:
        print(f"Found {existing_count} existing records in usage_aggregations")
        
        # Get user_ids that already have records
        existing_users = conn.execute(text('''
            SELECT DISTINCT user_id 
            FROM usage_aggregations 
            WHERE user_id IS NOT NULL
        ''')).fetchall()
        existing_user_ids = {str(row[0]) for row in existing_users}
        
        # Get all active users
        all_users = conn.execute(text('''
            SELECT user_id, tenant_id, created_at 
            FROM users 
            WHERE is_active = true
        ''')).fetchall()
        
        # Filter out users that already have records
        users = [u for u in all_users if str(u.user_id) not in existing_user_ids]
        
        if len(users) == 0:
            print("✓ All active users already have usage aggregation records")
            return
        else:
            print(f"Found {len(users)} new users to migrate (skipping {len(existing_user_ids)} existing)")
    else:
        # Get all active users
        users = conn.execute(text('''
            SELECT user_id, tenant_id, created_at 
            FROM users 
            WHERE is_active = true
        ''')).fetchall()
        print(f"Found {len(users)} active users to migrate")
    
    # Insert usage aggregation records for each user
    migrated_count = 0
    for user in users:
        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        # Calculate period_end (first day of next month)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            period_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        
        try:
            conn.execute(text('''
                INSERT INTO usage_aggregations (
                    id,
                    tenant_id,
                    user_id,
                    aggregation_type,
                    period_type,
                    period_start,
                    period_end,
                    total_active_classrooms,
                    students_enrolled_in_classrooms,
                    total_invites_sent,
                    quiz_creations,
                    total_questions_created,
                    ai_questions_generated,
                    ai_evaluations,
                    course_creations,
                    total_units_created,
                    ai_courses_generated,
                    material_uploads,
                    content_downloads,
                    storage_used_gb,
                    bandwidth_used_gb,
                    ai_tokens_consumed,
                    ai_generations_count,
                    active_users,
                    active_teachers,
                    active_students,
                    created_at,
                    updated_at
                ) VALUES (
                    gen_random_uuid(),
                    :tenant_id,
                    :user_id,
                    'individual',
                    'monthly',
                    :period_start,
                    :period_end,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0.000, 0.000, 0, 0,
                    1, 0, 0,
                    :created_at,
                    :updated_at
                )
            '''), {
                'tenant_id': user.tenant_id,
                'user_id': user.user_id,
                'period_start': period_start,
                'period_end': period_end,
                'created_at': user.created_at,
                'updated_at': datetime.now(timezone.utc)
            })
            conn.commit()
            migrated_count += 1
        except Exception as e:
            conn.rollback()
            print(f"Warning: Could not migrate user {user.user_id}: {str(e)}")
            continue
    
    print(f"Successfully migrated {migrated_count} users to usage_aggregations")

def downgrade():
    conn = op.get_bind()
    
    print("Rolling back user data migration from usage_aggregations...")
    
    # Delete only the records that were created by this migration
    # (records with aggregation_type='individual' and period_type='monthly')
    result = conn.execute(text('''
        DELETE FROM usage_aggregations 
        WHERE aggregation_type = 'individual' 
        AND period_type = 'monthly'
    '''))
    
    deleted_count = result.rowcount
    print(f"Deleted {deleted_count} usage aggregation records")