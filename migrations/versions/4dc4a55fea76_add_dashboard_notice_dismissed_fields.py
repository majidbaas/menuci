"""add dashboard notice dismissed fields

Revision ID: 4dc4a55fea76
Revises: 34a99b3de013
Create Date: 2026-09-17

"""

from alembic import op
import sqlalchemy as sa


revision = "4dc4a55fea76"
down_revision = "34a99b3de013"
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table(
        "users",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "profile_notice_dismissed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        batch_op.add_column(
            sa.Column(
                "guide_notice_dismissed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )


def downgrade():

    with op.batch_alter_table(
        "users",
        schema=None
    ) as batch_op:

        batch_op.drop_column(
            "guide_notice_dismissed"
        )

        batch_op.drop_column(
            "profile_notice_dismissed"
        )