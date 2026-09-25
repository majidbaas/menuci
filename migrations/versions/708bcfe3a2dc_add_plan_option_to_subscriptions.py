"""add plan option to subscriptions

Revision ID: 708bcfe3a2dc
Revises: 6d732c62ea10
Create Date: 2026-09-13 19:45:35.480367

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '708bcfe3a2dc'
down_revision = '6d732c62ea10'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'plan_option_id',
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_index(
            'ix_subscriptions_plan_option_id',
            ['plan_option_id'],
            unique=False
        )

        batch_op.create_foreign_key(
            'fk_subscriptions_plan_option_id',
            'plan_options',
            ['plan_option_id'],
            ['id'],
            ondelete='RESTRICT'
        )


def downgrade():

    with op.batch_alter_table('subscriptions', schema=None) as batch_op:

        batch_op.drop_constraint(
            'fk_subscriptions_plan_option_id',
            type_='foreignkey'
        )

        batch_op.drop_index(
            'ix_subscriptions_plan_option_id'
        )

        batch_op.drop_column(
            'plan_option_id'
        )