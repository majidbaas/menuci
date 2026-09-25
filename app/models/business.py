from datetime import datetime, timezone

from app.extensions import db


class Business(db.Model):
    __tablename__ = "businesses"
    
    
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )
    business_type = db.Column(
        db.String(50),
        nullable=True
    )
    
    slug = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True
    )

    logo = db.Column(
        db.String(255),
        nullable=True
    )

    banner = db.Column(
        db.String(255),
        nullable=True
    )
    primary_color = db.Column(
        db.String(7),
        nullable=True
    )
    description = db.Column(
        db.Text,
        nullable=True
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    address = db.Column(
        db.Text,
        nullable=True
    )

    latitude = db.Column(
        db.Float,
        nullable=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True
    )

    working_hours = db.Column(
        db.Text,
        nullable=True
    )

    instagram = db.Column(
        db.String(255),
        nullable=True
    )

    telegram = db.Column(
        db.String(255),
        nullable=True
    )

    website = db.Column(
        db.String(255),
        nullable=True
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
    user = db.relationship(
        "User",
        back_populates="businesses"
    )

    def __repr__(self):
        return f"<Business {self.name}>"