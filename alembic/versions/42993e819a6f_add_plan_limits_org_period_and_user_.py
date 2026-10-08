"""add_plan_limits_org_period_and_user_deleted_at

Revision ID: 42993e819a6f
Revises: 6504e82721c0
Create Date: 2026-10-07 21:02:54.025918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42993e819a6f'
down_revision: Union[str, Sequence[str], None] = '6504e82721c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add limits to plans, periods to orgs, and deleted_at to users."""
    with op.batch_alter_table('subscription_plans') as batch_op:
        batch_op.add_column(sa.Column('limits', sa.JSON(), nullable=False, server_default='{}'))

    with op.batch_alter_table('organizations') as batch_op:
        batch_op.add_column(sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_profiles_deleted_at'), ['deleted_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema: remove limits, periods, and deleted_at columns."""
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_profiles_deleted_at'))
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('organizations') as batch_op:
        batch_op.drop_column('current_period_end')
        batch_op.drop_column('current_period_start')

    with op.batch_alter_table('subscription_plans') as batch_op:
        batch_op.drop_column('limits')
