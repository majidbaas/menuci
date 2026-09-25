from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.subscription import Subscription


GRACE_PERIOD_DAYS = 10


def get_now():
    return datetime.now(timezone.utc)


def normalize_datetime(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def get_latest_subscription(user_id):
    """
    آخرین اشتراک فعال واقعی کاربر را برمی‌گرداند.

    فقط اشتراکی در نظر گرفته می‌شود که:
    - status آن active باشد
    - is_active آن True باشد

    اشتراک‌های قدیمی که غیرفعال شده‌اند،
    دیگر به عنوان اشتراک فعلی انتخاب نمی‌شوند.
    """

    return db.session.scalar(
        db.select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
            Subscription.is_active.is_(True)
        )
        .order_by(
            Subscription.end_date.desc()
        )
    )


def get_subscription_state(user_id):
    """
    وضعیت اشتراک کاربر:

    active
        اشتراک هنوز اعتبار دارد.

    grace_period
        اشتراک منقضی شده ولی هنوز داخل مهلت ۱۰ روزه است.

    archived
        مهلت ۱۰ روزه تمام شده است.

    none
        کاربر اشتراک فعالی ندارد.
    """

    subscription = get_latest_subscription(user_id)

    if subscription is None:
        return {
            "subscription": None,
            "state": "none",
            "days_remaining": 0,
            "grace_end_date": None,
        }

    now = get_now()

    end_date = normalize_datetime(
        subscription.end_date
    )

    # =========================================
    # اشتراک هنوز فعال است
    # =========================================

    if end_date > now:

        remaining = end_date - now

        days_remaining = max(
            0,
            remaining.days
        )

        return {
            "subscription": subscription,
            "state": "active",
            "days_remaining": days_remaining,
            "grace_end_date": None,
        }

    # =========================================
    # شروع دوره مهلت ۱۰ روزه
    # =========================================

    grace_end_date = (
        end_date
        + timedelta(days=GRACE_PERIOD_DAYS)
    )

    # =========================================
    # هنوز داخل دوره مهلت هستیم
    # =========================================

    if now < grace_end_date:

        remaining = (
            grace_end_date - now
        )

        days_remaining = max(
            1,
            remaining.days
        )

        return {
            "subscription": subscription,
            "state": "grace_period",
            "days_remaining": days_remaining,
            "grace_end_date": grace_end_date,
        }

    # =========================================
    # دوره مهلت تمام شده
    # =========================================

    return {
        "subscription": subscription,
        "state": "archived",
        "days_remaining": 0,
        "grace_end_date": grace_end_date,
    }