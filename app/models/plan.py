from datetime import datetime, timezone

from app.extensions import db


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    price = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False
    )

    max_businesses = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    max_categories = db.Column(
        db.Integer,
        nullable=False,
        default=10
    )

    max_products = db.Column(
        db.Integer,
        nullable=False,
        default=50
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Plan {self.name}>"