from datetime import datetime, timezone

from app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

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

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # گزینه انتخاب‌شده اشتراک
    plan_option_id = db.Column(
        db.Integer,
        db.ForeignKey("plan_options.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )

    start_date = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    end_date = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    # وضعیت اشتراک
    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending_payment",
        index=True
    )

    # مسیر فایل رسید پرداخت
    payment_receipt = db.Column(
        db.String(255),
        nullable=True
    )

    # شماره پیگیری پرداخت
    payment_tracking_code = db.Column(
        db.String(100),
        nullable=True
    )

    # توضیحات کاربر درباره پرداخت
    payment_description = db.Column(
        db.Text,
        nullable=True
    )
        # پیام مدیریت درباره بررسی درخواست
    admin_message = db.Column(
        db.Text,
        nullable=True
    )
    # زمان ارسال رسید
    payment_submitted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
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

    # Relationships

    user = db.relationship(
        "User",
        back_populates="subscriptions"
    )

    plan = db.relationship(
        "Plan",
        backref="subscriptions"
    )

    plan_option = db.relationship(
        "PlanOption",
        backref="subscriptions"
    )

    def __repr__(self):
        return (
            f"<Subscription "
            f"user={self.user_id} "
            f"plan={self.plan_id} "
            f"option={self.plan_option_id} "
            f"status={self.status}>"
        )