"""add_organization_usage_table

Revision ID: cafa7e63a60e
Revises: 42993e819a6f
Create Date: 2026-10-07 21:13:31.008995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cafa7e63a60e'
down_revision: Union[str, Sequence[str], None] = '42993e819a6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create organization_usage table."""
    op.create_table(
        'organization_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('used >= 0', name='ck_organization_usage_used_non_negative'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'metric', 'period_start', name='uq_org_usage_metric_period'),
    )
    op.create_index(op.f('ix_organization_usage_id'), 'organization_usage', ['id'], unique=False)
    op.create_index(op.f('ix_organization_usage_organization_id'), 'organization_usage', ['organization_id'], unique=False)
    op.create_index(op.f('ix_organization_usage_metric'), 'organization_usage', ['metric'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Drop organization_usage table."""
    op.drop_index(op.f('ix_organization_usage_metric'), table_name='organization_usage')
    op.drop_index(op.f('ix_organization_usage_organization_id'), table_name='organization_usage')
    op.drop_index(op.f('ix_organization_usage_id'), table_name='organization_usage')
    op.drop_table('organization_usage')
