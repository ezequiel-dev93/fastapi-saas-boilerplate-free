"""add_organization_api_keys_and_drop_legacy_user_keys

Revision ID: 6504e82721c0
Revises: e6cacfecc701
Create Date: 2026-10-07 19:17:02.461655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6504e82721c0'
down_revision: Union[str, Sequence[str], None] = 'e6cacfecc701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create organization_api_keys and drop legacy user keys."""
    # 1. Create organization_api_keys table
    op.create_table(
        'organization_api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_prefix', sa.String(length=24), nullable=False),
        sa.Column('hashed_key', sa.String(length=64), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organization_api_keys_id'), 'organization_api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_organization_api_keys_organization_id'), 'organization_api_keys', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_api_keys_key_prefix'), 'organization_api_keys', ['key_prefix'], unique=False)
    op.create_index(op.f('ix_organization_api_keys_hashed_key'), 'organization_api_keys', ['hashed_key'], unique=True)

    # 2. Drop legacy API key columns from user_settings (with batch op for SQLite compatibility)
    with op.batch_alter_table('user_settings') as batch_op:
        batch_op.drop_column('api_key_hash')
        batch_op.drop_column('api_key_prefix')
        batch_op.drop_column('api_key_created_at')


def downgrade() -> None:
    """Downgrade schema: Restore legacy user_settings columns and drop organization_api_keys."""
    with op.batch_alter_table('user_settings') as batch_op:
        batch_op.add_column(sa.Column('api_key_created_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('api_key_prefix', sa.String(length=12), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('api_key_hash', sa.String(length=64), nullable=False, server_default=''))

    op.drop_index(op.f('ix_organization_api_keys_hashed_key'), table_name='organization_api_keys')
    op.drop_index(op.f('ix_organization_api_keys_key_prefix'), table_name='organization_api_keys')
    op.drop_index(op.f('ix_organization_api_keys_organization_id'), table_name='organization_api_keys')
    op.drop_index(op.f('ix_organization_api_keys_id'), table_name='organization_api_keys')
    op.drop_table('organization_api_keys')

