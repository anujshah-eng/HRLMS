"""Add tenant_id to users table

Revision ID: add_tenant_to_users
Revises: f08a1c19d1af
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_tenant_to_users'
down_revision: Union[str, Sequence[str], None] = 'f08a1c19d1af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'tenants'
            ) THEN
                CREATE TABLE tenants (
                    id UUID PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    domain VARCHAR(200) UNIQUE NOT NULL
                );
            END IF;
        END$$;
        """
    ))

    # Add tenant_id column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('users_tenant_id_fkey', 'tenants', ['tenant_id'], ['id'])
        batch_op.create_index('ix_users_tenant_id', ['tenant_id'])

    # Ensure default tenant exists, then backfill: set tenant_id for existing users
    default_key = 'ace'
    default_name = 'acelucid'
    default_domain = 'acelucid.com'
    result = conn.execute(sa.text("select id from tenants where key = :k"), {"k": default_key})
    row = result.first()
    if row:
        default_tenant_id = row[0]
    else:
        # Insert default tenant
        import uuid as _uuid
        default_tenant_id = str(_uuid.uuid4())
        conn.execute(
            sa.text("insert into tenants (id, key, name, domain) values (:id, :key, :name, :domain)"),
            {"id": default_tenant_id, "key": default_key, "name": default_name, "domain": default_domain}
        )

    conn.execute(sa.text("update users set tenant_id = :tid where tenant_id is null"), {"tid": str(default_tenant_id)})

    # Set column non-null
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('tenant_id', nullable=False)

    # Enable RLS and add policies for users table
    conn.execute(sa.text("ALTER TABLE users ENABLE ROW LEVEL SECURITY"))
    conn.execute(sa.text(
        "CREATE POLICY users_tenant_isolation ON users USING (tenant_id::text = current_setting('app.tenant_id', true))"
    ))
    conn.execute(sa.text(
        "CREATE POLICY users_tenant_insert ON users FOR INSERT WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
    ))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    
    # Drop RLS policies
    conn.execute(sa.text("DROP POLICY IF EXISTS users_tenant_insert ON users"))
    conn.execute(sa.text("DROP POLICY IF EXISTS users_tenant_isolation ON users"))
    conn.execute(sa.text("ALTER TABLE users DISABLE ROW LEVEL SECURITY"))
    
    # Drop tenant_id column
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_tenant_id')
        batch_op.drop_constraint('users_tenant_id_fkey', type_='foreignkey')
        batch_op.drop_column('tenant_id')

 