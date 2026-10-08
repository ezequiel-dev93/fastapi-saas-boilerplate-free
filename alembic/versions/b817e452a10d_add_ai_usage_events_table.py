"""add_ai_usage_events_table

Revision ID: b817e452a10d
Revises: cafa7e63a60e
Create Date: 2026-10-07 21:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b817e452a10d'
down_revision: Union[str, Sequence[str], None] = 'cafa7e63a60e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create ai_usage_events table (metadata-only audit)."""
    op.create_table(
        'ai_usage_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('api_key_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['api_key_id'], ['organization_api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_usage_events_id'), 'ai_usage_events', ['id'], unique=False)
    op.create_index(op.f('ix_ai_usage_events_request_id'), 'ai_usage_events', ['request_id'], unique=True)
    op.create_index(op.f('ix_ai_usage_events_organization_id'), 'ai_usage_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_events_user_id'), 'ai_usage_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_events_api_key_id'), 'ai_usage_events', ['api_key_id'], unique=False)
    op.create_index('ix_ai_usage_org_created', 'ai_usage_events', ['organization_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Drop ai_usage_events table."""
    op.drop_index('ix_ai_usage_org_created', table_name='ai_usage_events')
    op.drop_index(op.f('ix_ai_usage_events_api_key_id'), table_name='ai_usage_events')
    op.drop_index(op.f('ix_ai_usage_events_user_id'), table_name='ai_usage_events')
    op.drop_index(op.f('ix_ai_usage_events_organization_id'), table_name='ai_usage_events')
    op.drop_index(op.f('ix_ai_usage_events_request_id'), table_name='ai_usage_events')
    op.drop_index(op.f('ix_ai_usage_events_id'), table_name='ai_usage_events')
    op.drop_table('ai_usage_events')
