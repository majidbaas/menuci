from datetime import datetime, timezone

from app.extensions import db


class PlanOption(db.Model):
    __tablename__ = "plan_options"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False
    )

    price = db.Column(
        db.Integer,
        nullable=False,
        default=0
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

    # Relationship
    plan = db.relationship(
        "Plan",
        backref=db.backref(
            "options",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return (
            f"<PlanOption plan={self.plan_id} "
            f"duration={self.duration_days} "
            f"price={self.price}>"
        )