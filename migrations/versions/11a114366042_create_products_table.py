"""create products table

Revision ID: 11a114366042
Revises: f22dfd0b020e
Create Date: 2026-08-18 12:00:26.597377

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "11a114366042"
down_revision = "f22dfd0b020e"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires batch mode for several ALTER TABLE operations.
    with op.batch_alter_table("products", schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                "business_id",
                sa.Integer(),
                nullable=False
            )
        )

        batch_op.add_column(
            sa.Column(
                "slug",
                sa.String(length=150),
                nullable=False
            )
        )

        batch_op.add_column(
            sa.Column(
                "is_available",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true()
            )
        )

        batch_op.alter_column(
            "category_id",
            existing_type=sa.INTEGER(),
            nullable=True
        )

        batch_op.alter_column(
            "price",
            existing_type=sa.INTEGER(),
            type_=sa.Numeric(
                precision=12,
                scale=2
            ),
            existing_nullable=False
        )

        batch_op.create_index(
            "ix_products_business_id",
            ["business_id"],
            unique=False
        )

        batch_op.create_foreign_key(
            "fk_products_category_id_categories",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL"
        )

        batch_op.create_foreign_key(
            "fk_products_business_id_businesses",
            "businesses",
            ["business_id"],
            ["id"],
            ondelete="CASCADE"
        )


def downgrade():

    with op.batch_alter_table("products", schema=None) as batch_op:

        batch_op.drop_constraint(
            "fk_products_business_id_businesses",
            type_="foreignkey"
        )

        batch_op.drop_constraint(
            "fk_products_category_id_categories",
            type_="foreignkey"
        )

        batch_op.drop_index(
            "ix_products_business_id"
        )

        batch_op.alter_column(
            "price",
            existing_type=sa.Numeric(
                precision=12,
                scale=2
            ),
            type_=sa.INTEGER(),
            existing_nullable=False
        )

        batch_op.alter_column(
            "category_id",
            existing_type=sa.INTEGER(),
            nullable=False
        )

        batch_op.drop_column("is_available")
        batch_op.drop_column("slug")
        batch_op.drop_column("business_id")