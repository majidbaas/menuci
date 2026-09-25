"""add username and mobile to users

Revision ID: 3d9fd728838b
Revises: 95e9e4276b28
Create Date: 2026-09-17 18:34:26.418809

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d9fd728838b'
down_revision = '95e9e4276b28'
branch_labels = None
depends_on = None


def upgrade():
    # ابتدا username را موقتاً nullable اضافه می‌کنیم
    # چون ممکن است در دیتابیس کاربران قدیمی وجود داشته باشند.
    with op.batch_alter_table('users', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'username',
                sa.String(length=100),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'mobile',
                sa.String(length=20),
                nullable=True
            )
        )

        batch_op.create_index(
            batch_op.f('ix_users_mobile'),
            ['mobile'],
            unique=True
        )

        batch_op.create_index(
            batch_op.f('ix_users_username'),
            ['username'],
            unique=True
        )


def downgrade():

    with op.batch_alter_table('users', schema=None) as batch_op:

        batch_op.drop_index(
            batch_op.f('ix_users_username')
        )

        batch_op.drop_index(
            batch_op.f('ix_users_mobile')
        )

        batch_op.drop_column('mobile')
        batch_op.drop_column('username')