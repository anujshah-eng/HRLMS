"""transfer users to user_subscriptions table

Revision ID: transfer_users_to_subscriptions
Revises: create_user_subscriptions
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

# revision identifiers, used by Alembic
revision = 'transfer_users_to_subscriptions'
down_revision = 'f08a1c19d1af'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # Get the Free Plan ID (assuming it exists from seed data)
    free_plan = conn.execute(text('''
        SELECT id FROM subscription_plans 
        WHERE name = 'Free Plan' 
        LIMIT 1
    ''')).fetchone()
    
    if not free_plan:
        print("Warning: Free Plan not found. Skipping user subscription creation.")
        print("Please run insert_default_subscription_plans() first.")
        return
    
    free_plan_id = free_plan[0]
    
    # Get all active users
    users = conn.execute(text('''
        SELECT user_id, tenant_id, created_at, is_active
        FROM users 
        WHERE is_active = true
    ''')).fetchall()
    
    if not users:
        print("No active users found to transfer.")
        return
    
    print(f"Found {len(users)} active users to create subscriptions for...")
    
    # For each user, create a user_subscription record
    for user in users:
        now = datetime.now(timezone.utc)
        
        # Check if user already has a subscription (in case of re-running)
        existing = conn.execute(text('''
            SELECT id FROM user_subscriptions 
            WHERE user_id = :user_id
        '''), {'user_id': user.user_id}).fetchone()
        
        if existing:
            print(f"User {user.user_id} already has a subscription, skipping...")
            continue
        
        # Determine subscription type based on tenant_id
        if user.tenant_id:
            # User belongs to a tenant - create tenant_member subscription
            subscription_type = 'tenant_member'
            plan_id = None  # Tenant members don't have individual plans
            status = None
            started_at = None
            expires_at = None
            tenant_role = 'admin'  # Default role, can be updated later
            tenant_joined_at = user.created_at
            tenant_status = 'active'
        else:
            # Individual user - create individual subscription with Free Plan
            subscription_type = 'individual'
            plan_id = free_plan_id
            status = 'active'
            started_at = user.created_at or now
            expires_at = None  # Free plan doesn't expire
            tenant_role = None
            tenant_joined_at = None
            tenant_status = None
        
        # Generate a new UUID for the id column
        subscription_id = uuid.uuid4()
        
        # Insert user_subscription record
        conn.execute(text('''
            INSERT INTO user_subscriptions (
                id,
                user_id,
                subscription_type,
                tenant_id,
                plan_id,
                status,
                started_at,
                expires_at,
                tenant_role,
                tenant_joined_at,
                tenant_status,
                allow_quota_fallback,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                :id,
                :user_id,
                :subscription_type,
                :tenant_id,
                :plan_id,
                :status,
                :started_at,
                :expires_at,
                :tenant_role,
                :tenant_joined_at,
                :tenant_status,
                false,
                true,
                :created_at,
                :updated_at
            )
        '''), {
            'id': subscription_id,
            'user_id': user.user_id,
            'subscription_type': subscription_type,
            'tenant_id': user.tenant_id,
            'plan_id': plan_id,
            'status': status,
            'started_at': started_at,
            'expires_at': expires_at,
            'tenant_role': tenant_role,
            'tenant_joined_at': tenant_joined_at,
            'tenant_status': tenant_status,
            'created_at': user.created_at or now,
            'updated_at': now
        })
        
        print(f"Created {subscription_type} subscription for user {user.user_id}")
    
    # Commit the transaction
    conn.commit()
    print(f"\nSuccessfully created subscriptions for {len(users)} users!")

def downgrade():
    conn = op.get_bind()
    
    # Delete all user_subscriptions that were created during this migration
    # We'll keep subscriptions that might have been manually created
    conn.execute(text('''
        DELETE FROM user_subscriptions 
        WHERE created_at <= updated_at + INTERVAL '5 seconds'
        AND (
            subscription_type = 'individual' 
            OR subscription_type = 'tenant_member'
        )
    '''))
    
    conn.commit()
    print("Rolled back user subscription transfers.")