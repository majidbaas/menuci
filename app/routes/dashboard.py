import os
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import jdatetime
from app.models.plan_option import PlanOption
from app.services.subscription import get_subscription_state


from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request
)

from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.business import Business
from app.models.category import Category
from app.models.product import Product
from app.models.subscription import Subscription
from app.models.plan import Plan


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)


@dashboard_bp.route("/")
@login_required
def index():

    # =========================================
    # کسب‌وکارهای کاربر
    # =========================================

    businesses = db.session.scalars(
        db.select(Business)
        .where(
            Business.user_id == current_user.id
        )
        .order_by(
            Business.created_at.desc()
        )
    ).all()

    # =========================================
    # آمار هر کسب‌وکار
    # =========================================

    businesses_data = []

    for business in businesses:

        products_count = db.session.scalar(
            db.select(func.count(Product.id))
            .where(
                Product.business_id == business.id
            )
        ) or 0

        categories_count = db.session.scalar(
            db.select(func.count(Category.id))
            .where(
                Category.business_id == business.id
            )
        ) or 0

        businesses_data.append({
            "business": business,
            "products_count": products_count,
            "categories_count": categories_count
        })

    # =========================================
    # وضعیت اشتراک
    # =========================================

    subscription_state = get_subscription_state(
        current_user.id
    )

    subscription = subscription_state["subscription"]
    subscription_status = subscription_state["state"]

    subscription_days_remaining = subscription_state[
        "days_remaining"
    ]

    grace_end_date = subscription_state[
        "grace_end_date"
    ]

    # =========================================
    # وضعیت انقضا
    # =========================================

    subscription_expired = (
        subscription_status in (
            "grace_period",
            "archived"
        )
    )

    # =========================================
    # هشدار نزدیک بودن انقضا
    # =========================================

    subscription_expiring_soon = (
        subscription_status == "active"
        and 0 < subscription_days_remaining <= 3
    )

    # =========================================
    # تبدیل تاریخ پایان اشتراک به شمسی
    # =========================================

    subscription_end_date_jalali = None

    if subscription:

        end_date = subscription.end_date

        if end_date.tzinfo is None:
            end_date = end_date.replace(
                tzinfo=timezone.utc
            )

        subscription_end_date_jalali = (
            jdatetime.datetime.fromgregorian(
                datetime=end_date
            ).strftime("%Y/%m/%d")
        )

    # =========================================
    # تاریخ پایان دوره مهلت تمدید
    # =========================================

    grace_end_date_jalali = None

    if grace_end_date:

        grace_end_date = grace_end_date

        if grace_end_date.tzinfo is None:
            grace_end_date = grace_end_date.replace(
                tzinfo=timezone.utc
            )

        grace_end_date_jalali = (
            jdatetime.datetime.fromgregorian(
                datetime=grace_end_date
            ).strftime("%Y/%m/%d")
        )

    # =========================================
    # آخرین درخواست اشتراک
    # =========================================

    latest_subscription = db.session.scalar(
        db.select(Subscription)
        .where(
            Subscription.user_id == current_user.id
        )
        .order_by(
            Subscription.created_at.desc()
        )
    )

    # =========================================
    # وضعیت درخواست در حال بررسی
    # =========================================

    # =========================================
    # وضعیت درخواست در حال بررسی
    # =========================================

    pending_subscription = None

    if latest_subscription:

        if latest_subscription.status == "pending_review":
            pending_subscription = latest_subscription

    # =========================================
    # آمار کلی کاربر
    # =========================================

    businesses_count = len(businesses)

    categories_total = sum(
        item["categories_count"]
        for item in businesses_data
    )

    products_total = sum(
        item["products_count"]
        for item in businesses_data
    )

    # =========================================
    # ارسال اطلاعات به داشبورد
    # =========================================

    return render_template(
        "dashboard/index.html",
        user=current_user,
        profile_notice_dismissed=current_user.profile_notice_dismissed,
        guide_notice_dismissed=current_user.guide_notice_dismissed,
        businesses=businesses,
        businesses_data=businesses_data,

        # اشتراک
        subscription=subscription,
        subscription_status=subscription_status,
        subscription_days_remaining=subscription_days_remaining,
        subscription_end_date_jalali=subscription_end_date_jalali,
        subscription_expiring_soon=subscription_expiring_soon,

        # دوره مهلت تمدید
        grace_end_date=grace_end_date,
        grace_end_date_jalali=grace_end_date_jalali,

        # آخرین درخواست اشتراک
        latest_subscription=latest_subscription,
        pending_subscription=pending_subscription,

        # وضعیت انقضا
        subscription_expired=subscription_expired,

        # آمار
        businesses_count=businesses_count,
        categories_total=categories_total,
        products_total=products_total
    )
    
    
    
 # =========================================
# بررسی خودکار وضعیت درخواست اشتراک
# =========================================

@dashboard_bp.route("/subscription/status")
@login_required
def subscription_status():

    latest_subscription = db.session.scalar(
        db.select(Subscription)
        .where(
            Subscription.user_id == current_user.id
        )
        .order_by(
            Subscription.created_at.desc()
        )
    )

    if latest_subscription is None:
        return {
            "exists": False
        }

    return {
        "exists": True,
        "id": latest_subscription.id,
        "status": latest_subscription.status,
        "admin_message": latest_subscription.admin_message or ""
    }   
# =========================================
# عدم نمایش دوباره کارت تکمیل اطلاعات
# =========================================

@dashboard_bp.route(
    "/dismiss-profile-notice",
    methods=["POST"]
)
@login_required
def dismiss_profile_notice():

    current_user.profile_notice_dismissed = True

    db.session.commit()

    return redirect(
        url_for("dashboard.index")
    )


# =========================================
# عدم نمایش دوباره کارت آموزش
# =========================================

@dashboard_bp.route(
    "/dismiss-guide-notice",
    methods=["POST"]
)
@login_required
def dismiss_guide_notice():

    current_user.guide_notice_dismissed = True

    db.session.commit()

    return redirect(
        url_for("dashboard.index")
    )
# =========================================
# صفحه تمدید / ارتقای اشتراک
# =========================================
@dashboard_bp.route("/subscription")
@login_required
def subscription():

    plans = db.session.scalars(
        db.select(Plan)
        .where(Plan.is_active.is_(True))
        .order_by(Plan.price.asc())
    ).all()

    for plan in plans:
        plan.options = db.session.scalars(
            db.select(PlanOption)
            .where(
                PlanOption.plan_id == plan.id,
                PlanOption.is_active.is_(True)
            )
            .order_by(PlanOption.duration_days.asc())
        ).all()

    return render_template(
        "dashboard/subscription.html",
        plans=plans,
        current_subscription=None
    )

# =========================================
# صفحه پرداخت اشتراک
# =========================================
@dashboard_bp.route("/subscription/payment/<int:option_id>")
@login_required
def subscription_payment(option_id):

    option = db.session.scalar(
        db.select(PlanOption)
        .where(
            PlanOption.id == option_id,
            PlanOption.is_active.is_(True)
        )
    )

    if option is None:
        abort(404)

    plan = db.session.get(
        Plan,
        option.plan_id
    )

    if plan is None or not plan.is_active:
        abort(404)

    # اگر قبلاً برای همین گزینه فیش ارسال شده
    pending_review_subscription = db.session.scalar(
        db.select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.plan_option_id == option.id,
            Subscription.status == "pending_review"
        )
        .order_by(
            Subscription.created_at.desc()
        )
    )

    if pending_review_subscription:

        flash(
            "رسید پرداخت شما قبلاً ارسال شده و در انتظار بررسی مدیریت است.",
            "warning"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # نکته مهم:
    # در این مرحله هیچ Subscription ساخته نمی‌شود.
    # درخواست فقط بعد از ارسال فیش ساخته خواهد شد.

    return render_template(
        "dashboard/subscription_payment.html",
        plan=plan,
        option=option,
        subscription=None
    )
# =========================================
# ثبت و ارسال رسید پرداخت اشتراک
# =========================================

@dashboard_bp.route(
    "/subscription/payment/<int:option_id>/submit",
    methods=["POST"]
)
@login_required
def start_subscription_payment(option_id):

    option = db.session.scalar(
        db.select(PlanOption)
        .where(
            PlanOption.id == option_id,
            PlanOption.is_active.is_(True)
        )
    )

    if option is None:
        abort(404)

    plan = db.session.get(
        Plan,
        option.plan_id
    )

    if plan is None or not plan.is_active:
        abort(404)

    # اگر قبلاً فیش ارسال شده، درخواست جدید نساز
    pending_review_subscription = db.session.scalar(
        db.select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.plan_option_id == option.id,
            Subscription.status == "pending_review"
        )
        .order_by(
            Subscription.created_at.desc()
        )
    )

    if pending_review_subscription:

        flash(
            "رسید پرداخت شما قبلاً ارسال شده و در انتظار بررسی مدیریت است.",
            "warning"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # دریافت فایل فیش
    receipt_file = request.files.get("payment_receipt")

    if receipt_file is None or receipt_file.filename == "":

        flash(
            "لطفاً تصویر فیش پرداخت را انتخاب کنید.",
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.subscription_payment",
                option_id=option.id
            )
        )

    # بررسی فرمت فایل
    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    original_filename = receipt_file.filename

    extension = (
        original_filename
       .rsplit(".", 1)[-1]
       .lower()
        if "." in original_filename
        else ""
    )

    if extension not in allowed_extensions:

        flash(
            "فرمت تصویر فیش باید JPG، JPEG، PNG یا WEBP باشد.",
            "warning"
        )

        return redirect(
            url_for(
                "dashboard.subscription_payment",
                option_id=option.id
            )
        )

    # ==================================================
    # از اینجا به بعد، چون فیش معتبر است، درخواست ساخته می‌شود
    # ==================================================

    now = datetime.now(timezone.utc)

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        plan_option_id=option.id,
        start_date=now,
        end_date=now,
        status="pending_review",
        is_active=False
    )

    db.session.add(subscription)

    # برای گرفتن ID درخواست قبل از ساخت نام فایل
    db.session.flush()

    # ساخت پوشه آپلود فیش
    upload_folder = os.path.join(
        "app",
        "static",
        "uploads",
        "payments"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    # نام یکتا برای فایل فیش
    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    filename = (
        f"receipt_{current_user.id}_"
        f"{subscription.id}_"
        f"{timestamp}."
        f"{extension}"
    )

    receipt_file.save(
        os.path.join(
            upload_folder,
            filename
        )
    )

    # توضیحات اختیاری
    payment_description = request.form.get(
        "payment_description"
    )

    subscription.payment_receipt = filename

    subscription.payment_description = (
        payment_description
        if payment_description
        else None
    )

    subscription.payment_submitted_at = (
        datetime.now(timezone.utc)
    )

    subscription.status = "pending_review"
    subscription.is_active = False

    db.session.commit()

    flash(
        "فیش پرداخت با موفقیت ارسال شد و درخواست شما در انتظار بررسی مدیریت است.",
        "success"
    )

    return redirect(
        url_for("dashboard.index")
    )