"""
Initial DB Migration with Users, Roles, and Refresh Tokens

Revision ID: init_migration_001
Revises:
Create Date: 2026-07-06 12:45:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'init_migration_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index('ix_roles_id', 'roles', ['id'])
    op.create_index('ix_roles_name', 'roles', ['name'])

    # 2. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(150), unique=True, nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('role_id', sa.String(36), sa.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])

    # 3. Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('token', sa.String(512), unique=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), default=False, nullable=False),
        sa.Column('revoked_reason', sa.String(255), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'])

    # Seed Default Roles
    op.execute(
        "INSERT INTO roles (id, name, description, created_at, updated_at) VALUES "
        "('r1', 'SUPER_ADMIN', 'Super Admin with absolute control', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
        "('r2', 'ADMIN', 'Administrator manage doctor receptionist profiles', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
        "('r3', 'RECEPTIONIST', 'Reception desk manager for scheduling and bills', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
        "('r4', 'DOCTOR', 'Doctor manage patient consultations & prescriptions', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
        "('r5', 'PATIENT', 'Patient profiles for scheduling and history', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )

    # Seed initial SUPER_ADMIN user:
    # email: sunny@gmail.com, username: superadmin, password: sunny (hashed via bcrypt)
    # Hashed value of 'sunny' is '$2b$12$4v0FqjVn4w9P8uX.wW8VReL6K44g4/2Ym3W2l3XvXw6z1g8x7v1O2'
    op.execute(
        "INSERT INTO users (id, email, username, hashed_password, is_active, role_id, created_at, updated_at) VALUES "
        "('u1', 'sunny@gmail.com', 'superadmin', "
        "'$2b$12$4v0FqjVn4w9P8uX.wW8VReL6K44g4/2Ym3W2l3XvXw6z1g8x7v1O2', "
        "1, 'r1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
    )

def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('roles')
