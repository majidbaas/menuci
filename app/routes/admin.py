 
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from app.extensions import db
from sqlalchemy import func
from app.models import Plan, PlanOption, Subscription, User, PasswordResetRequest
from app.models.business import Business
import jdatetime
admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


@admin_bp.before_request
@login_required
def admin_required():
    if not current_user.is_admin:
        from flask import abort

        abort(403)

@admin_bp.route("/")
def index():

    pending_subscriptions_count = db.session.scalar(
        db.select(func.count(Subscription.id))
        .where(
            Subscription.status == "pending_review"
        )
    ) or 0

    pending_password_reset_count = db.session.scalar(
        db.select(func.count(PasswordResetRequest.id))
        .where(
            PasswordResetRequest.status == "pending"
        )
    ) or 0

    return render_template(
        "admin/index.html",
        pending_subscriptions_count=pending_subscriptions_count,
        pending_password_reset_count=pending_password_reset_count
    )


@admin_bp.route("/notification-counts")
def notification_counts():

    pending_subscriptions_count = db.session.scalar(
        db.select(func.count(Subscription.id))
        .where(
            Subscription.status == "pending_review"
        )
    ) or 0

    pending_password_reset_count = db.session.scalar(
        db.select(func.count(PasswordResetRequest.id))
        .where(
            PasswordResetRequest.status == "pending"
        )
    ) or 0

    return {
        "pending_subscriptions_count": pending_subscriptions_count,
        "pending_password_reset_count": pending_password_reset_count
    }

@admin_bp.route("/plans")
def plans():
    plans = db.session.scalars(
        db.select(Plan).order_by(Plan.id)
    ).all()

    plan_options = {}

    if plans:
        plan_ids = [plan.id for plan in plans]

        options = db.session.scalars(
            db.select(PlanOption)
            .where(
                PlanOption.plan_id.in_(plan_ids),
                PlanOption.is_active.is_(True)
            )
            .order_by(
                PlanOption.plan_id,
                PlanOption.duration_days
            )
        ).all()

        for option in options:
            plan_options.setdefault(option.plan_id, []).append(option)

@admin_bp.route("/subscriptions")
def subscriptions():

    subscriptions = db.session.scalars(
        db.select(Subscription)
        .order_by(
            Subscription.created_at.desc()
        )
    ).all()

    subscription_dates = {}

    for subscription in subscriptions:

        if subscription.created_at:

            subscription_dates[subscription.id] = (
                jdatetime.datetime.fromgregorian(
                    datetime=subscription.created_at
                ).strftime("%Y/%m/%d")
            )

        else:

            subscription_dates[subscription.id] = "—"

    return render_template(
        "admin/subscriptions.html",
        subscriptions=subscriptions,
        subscription_dates=subscription_dates
    )
    
    
    
@admin_bp.route("/subscriptions/<int:subscription_id>/receipt")
def subscription_receipt(subscription_id):

    subscription = db.session.get(
        Subscription,
        subscription_id
    )

    if subscription is None:
        from flask import abort

        abort(404)

    if not subscription.payment_receipt:
        from flask import abort

        abort(404)

    return redirect(
        url_for(
            "static",
            filename=f"uploads/payments/{subscription.payment_receipt}"
        )
    )

@admin_bp.route("/plans/create", methods=["GET", "POST"])
def create_plan():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        price_30_text = request.form.get("price_30", "").strip()
        price_90_text = request.form.get("price_90", "").strip()
        price_180_text = request.form.get("price_180", "").strip()

        max_businesses_text = request.form.get(
            "max_businesses",
            ""
        ).strip()

        max_categories_text = request.form.get(
            "max_categories",
            ""
        ).strip()

        max_products_text = request.form.get(
            "max_products",
            ""
        ).strip()

        if not name:

            flash(
                "نام پلن الزامی است.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text
            )

        existing_plan = db.session.scalar(
            db.select(Plan).where(
                Plan.name == name
            )
        )

        if existing_plan:

            flash(
                "پلنی با این نام قبلاً وجود دارد.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text
            )

        try:

            price_30 = int(
                price_30_text.replace(",", "") or 0
            )

            price_90 = int(
                price_90_text.replace(",", "") or 0
            )

            price_180 = int(
                price_180_text.replace(",", "") or 0
            )

            max_businesses = int(
                max_businesses_text
            )

            max_categories = int(
                max_categories_text
            )

            max_products = int(
                max_products_text
            )

        except ValueError:

            flash(
                "مقادیر عددی را به‌درستی وارد کنید.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text
            )

        if (
            price_30 < 0
            or price_90 < 0
            or price_180 < 0
            or max_businesses <= 0
            or max_categories <= 0
            or max_products <= 0
        ):

            flash(
                "مقادیر عددی باید معتبر باشند.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text
            )

        # -------------------------------------------------
        # ایجاد پلن
        # -------------------------------------------------
        #
        # فعلاً برای سازگاری با ساختار قدیمی جدول Plan:
        # price = قیمت ۱ ماهه
        # duration_days = 30
        #
        # قیمت‌های واقعی اشتراک در PlanOption ذخیره می‌شوند.
        # -------------------------------------------------

        plan = Plan(
            name=name,
            description=description or None,
            price=price_30,
            duration_days=30,
            max_businesses=max_businesses,
            max_categories=max_categories,
            max_products=max_products,
            is_active=True
        )

        db.session.add(plan)

        # -------------------------------------------------
        # ذخیره گزینه‌های مدت و قیمت اشتراک
        # -------------------------------------------------

        plan_options = [

            PlanOption(
                plan=plan,
                duration_days=30,
                price=price_30,
                is_active=True
            ),

            PlanOption(
                plan=plan,
                duration_days=90,
                price=price_90,
                is_active=True
            ),

            PlanOption(
                plan=plan,
                duration_days=180,
                price=price_180,
                is_active=True
            )

        ]

        db.session.add_all(plan_options)

        db.session.commit()

        flash(
            "پلن با موفقیت ایجاد شد.",
            "success"
        )

        return redirect(
            url_for("admin.plans")
        )

    return render_template(
        "admin/plan_form.html"
    )
    
@admin_bp.route(
    "/plans/<int:plan_id>/edit",
    methods=["GET", "POST"]
)
def edit_plan(plan_id):

    plan = db.session.get(
        Plan,
        plan_id
    )

    if plan is None:

        from flask import abort

        abort(404)

    plan_options = db.session.scalars(
        db.select(PlanOption)
        .where(
            PlanOption.plan_id == plan.id,
            PlanOption.is_active.is_(True)
        )
        .order_by(
            PlanOption.duration_days.asc()
        )
    ).all()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price_30_text = request.form.get(
            "price_30",
            ""
        ).strip()

        price_90_text = request.form.get(
            "price_90",
            ""
        ).strip()

        price_180_text = request.form.get(
            "price_180",
            ""
        ).strip()

        max_businesses_text = request.form.get(
            "max_businesses",
            ""
        ).strip()

        max_categories_text = request.form.get(
            "max_categories",
            ""
        ).strip()

        max_products_text = request.form.get(
            "max_products",
            ""
        ).strip()

        if not name:

            flash(
                "نام پلن الزامی است.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                plan=plan,
                plan_options=plan_options,
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text,
                form_title="ویرایش پلن"
            )

        existing_plan = db.session.scalar(
            db.select(Plan)
            .where(
                Plan.name == name,
                Plan.id != plan.id
            )
        )

        if existing_plan:

            flash(
                "پلنی با این نام قبلاً وجود دارد.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                plan=plan,
                plan_options=plan_options,
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text,
                form_title="ویرایش پلن"
            )

        try:

            price_30 = int(
                price_30_text.replace(",", "") or 0
            )

            price_90 = int(
                price_90_text.replace(",", "") or 0
            )

            price_180 = int(
                price_180_text.replace(",", "") or 0
            )

            max_businesses = int(
                max_businesses_text
            )

            max_categories = int(
                max_categories_text
            )

            max_products = int(
                max_products_text
            )

        except ValueError:

            flash(
                "مقادیر عددی را به‌درستی وارد کنید.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                plan=plan,
                plan_options=plan_options,
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text,
                form_title="ویرایش پلن"
            )

        if (
            price_30 < 0
            or price_90 < 0
            or price_180 < 0
            or max_businesses <= 0
            or max_categories <= 0
            or max_products <= 0
        ):

            flash(
                "مقادیر عددی باید معتبر باشند.",
                "error"
            )

            return render_template(
                "admin/plan_form.html",
                plan=plan,
                plan_options=plan_options,
                name=name,
                description=description,
                price_30=price_30_text,
                price_90=price_90_text,
                price_180=price_180_text,
                max_businesses=max_businesses_text,
                max_categories=max_categories_text,
                max_products=max_products_text,
                form_title="ویرایش پلن"
            )

        # -------------------------------------------------
        # به‌روزرسانی اطلاعات پلن
        # -------------------------------------------------

        plan.name = name

        plan.description = (
            description
            or None
        )

        # -------------------------------------------------
        # این دو فیلد قدیمی فعلاً در دیتابیس باقی می‌مانند
        # تا به ساختار فعلی برنامه آسیبی وارد نشود.
        #
        # مقدار price = قیمت ۱ ماهه
        # مقدار duration_days = 30
        # -------------------------------------------------

        plan.price = price_30

        plan.duration_days = 30

        plan.max_businesses = max_businesses

        plan.max_categories = max_categories

        plan.max_products = max_products

        # -------------------------------------------------
        # به‌روزرسانی گزینه‌های ۱، ۳ و ۶ ماهه
        # -------------------------------------------------

        options = {
            30: price_30,
            90: price_90,
            180: price_180
        }

        for duration_days_option, option_price in options.items():

            option = db.session.scalar(
                db.select(PlanOption)
                .where(
                    PlanOption.plan_id == plan.id,
                    PlanOption.duration_days == duration_days_option
                )
            )

            if option is None:

                option = PlanOption(
                    plan_id=plan.id,
                    duration_days=duration_days_option,
                    price=option_price,
                    is_active=True
                )

                db.session.add(option)

            else:

                option.price = option_price
                option.is_active = True

        db.session.commit()

        flash(
            "پلن با موفقیت ویرایش شد.",
            "success"
        )

        return redirect(
            url_for("admin.plans")
        )

    return render_template(
        "admin/plan_form.html",
        plan=plan,
        plan_options=plan_options,
        form_title="ویرایش پلن"
    )
    
@admin_bp.route("/subscriptions/<int:subscription_id>/approve", methods=["POST"])
def approve_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)

    if subscription is None:
        from flask import abort
        abort(404)

    if subscription.status != "pending_review":
        flash("این اشتراک در وضعیت قابل تأیید نیست.", "error")
        return redirect(url_for("admin.subscriptions"))

    # پیام اختیاری مدیریت
    admin_message = request.form.get("admin_message", "").strip()

    if admin_message:
        subscription.admin_message = admin_message

    now = datetime.now(timezone.utc)

    subscription.start_date = now

    if subscription.plan_option:
        subscription.end_date = (
            now + timedelta(days=subscription.plan_option.duration_days)
        )
    else:
        subscription.end_date = (
            now + timedelta(days=subscription.plan.duration_days)
        )

    old_subscriptions = db.session.scalars(
        db.select(Subscription).where(
            Subscription.user_id == subscription.user_id,
            Subscription.id != subscription.id,
            Subscription.status == "active",
            Subscription.is_active.is_(True)
        )
    ).all()

    for old_subscription in old_subscriptions:
        old_subscription.is_active = False

    subscription.status = "active"
    subscription.is_active = True

    businesses = db.session.scalars(
        db.select(Business).where(
            Business.user_id == subscription.user_id
        )
    ).all()

    for business in businesses:
        business.is_active = True

    db.session.commit()

    flash(
        "اشتراک با موفقیت تأیید و فعال شد.",
        "success"
    )

    return redirect(url_for("admin.subscriptions"))
    
    
    
@admin_bp.route("/subscriptions/<int:subscription_id>/reject", methods=["POST"])
def reject_subscription(subscription_id):
    subscription = db.session.get(Subscription, subscription_id)

    if subscription is None:
        from flask import abort
        abort(404)

    if subscription.status != "pending_review":
        flash("این اشتراک در وضعیت قابل رد کردن نیست.", "error")
        return redirect(url_for("admin.subscriptions"))

    # پیام رد باید حتماً توسط مدیریت وارد شود
    admin_message = request.form.get("admin_message", "").strip()

    if not admin_message:
        flash(
            "برای رد کردن رسید، وارد کردن دلیل رد الزامی است.",
            "error"
        )
        return redirect(url_for("admin.subscriptions"))

    subscription.admin_message = admin_message
    subscription.status = "rejected"
    subscription.is_active = False

    db.session.commit()

    flash(
        "رسید پرداخت رد شد و پیام مدیریت برای کاربر ثبت گردید.",
        "warning"
    )

    return redirect(url_for("admin.subscriptions"))
# =========================================================
# مدیریت کاربران و اشتراک‌ها
# =========================================================


@admin_bp.route("/users")
def users():
    users = db.session.scalars(
        db.select(User)
        .order_by(User.id.desc())
    ).all()

    user_data = []

    for user in users:
        subscription = db.session.scalar(
            db.select(Subscription)
            .where(
                Subscription.user_id == user.id
            )
            .order_by(
                Subscription.created_at.desc()
            )
        )

        businesses = db.session.scalars(
            db.select(Business)
            .where(
                Business.user_id == user.id
            )
        ).all()

        user_data.append({
            "user": user,
            "subscription": subscription,
            "businesses": businesses
        })

    return render_template(
        "admin/users.html",
        user_data=user_data
    )








@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        from flask import abort
        abort(404)

    # جلوگیری از غیرفعال کردن حساب ادمینی که با آن وارد شده‌ایم
    if user.id == current_user.id and user.is_active:
        flash("نمی‌توانید حساب کاربری خودتان را غیرفعال کنید.", "warning")
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active

    # اگر کاربر آرشیو شد، تمام کسب‌وکارهای او هم آرشیو شوند
    if not user.is_active:
        businesses = db.session.scalars(
            db.select(Business)
            .where(Business.user_id == user.id)
        ).all()

        for business in businesses:
            business.is_active = False

    db.session.commit()

    if user.is_active:
        flash(
            f"کاربر «{user.username}» دوباره فعال شد.",
            "success"
        )
    else:
        flash(
            f"کاربر «{user.username}» آرشیو شد و تمام کسب‌وکارهای او نیز غیرفعال شدند.",
            "warning"
        )

    return redirect(url_for("admin.users"))
@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
def toggle_user_admin(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        from flask import abort
        abort(404)

    # جلوگیری از خارج کردن خودمان از حالت ادمین
    if user.id == current_user.id and user.is_admin:
        flash("نمی‌توانید دسترسی ادمین خودتان را حذف کنید.", "warning")
        return redirect(url_for("admin.users"))

    user.is_admin = not user.is_admin

    db.session.commit()

    if user.is_admin:
        flash(
            f"کاربر «{user.username}» اکنون ادمین است.",
            "success"
        )
    else:
        flash(
            f"دسترسی ادمین کاربر «{user.username}» حذف شد.",
            "warning"
        )

    return redirect(url_for("admin.users"))



# =========================================================
# درخواست‌های بازیابی رمز عبور
# =========================================================

@admin_bp.route("/password-reset-requests")
def password_reset_requests():

    reset_requests = db.session.scalars(
        db.select(PasswordResetRequest)
        .order_by(
            PasswordResetRequest.requested_at.desc()
        )
    ).all()

    return render_template(
        "admin/password_reset_requests.html",
        reset_requests=reset_requests
    )


@admin_bp.route(
    "/password-reset-requests/<int:request_id>/reset",
    methods=["GET", "POST"]
)
def reset_user_password(request_id):

    reset_request = db.session.get(
        PasswordResetRequest,
        request_id
    )

    if reset_request is None:
        from flask import abort

        abort(404)

    user = reset_request.user

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not new_password:

            flash(
                "رمز عبور جدید را وارد کنید.",
                "error"
            )

            return render_template(
                "admin/password_reset_form.html",
                reset_request=reset_request,
                user=user
            )

        if len(new_password) < 6:

            flash(
                "رمز عبور باید حداقل ۶ کاراکتر باشد.",
                "error"
            )

            return render_template(
                "admin/password_reset_form.html",
                reset_request=reset_request,
                user=user
            )

        if new_password != confirm_password:

            flash(
                "تکرار رمز عبور صحیح نیست.",
                "error"
            )

            return render_template(
                "admin/password_reset_form.html",
                reset_request=reset_request,
                user=user
            )

        # -----------------------------------------
        # تغییر رمز عبور
        # -----------------------------------------

        user.set_password(new_password)

        # -----------------------------------------
        # تکمیل درخواست بازیابی
        # -----------------------------------------

        reset_request.status = "completed"

        reset_request.completed_at = datetime.now(
            timezone.utc
        )

        db.session.commit()

        flash(
            f"رمز عبور کاربر «{user.username}» با موفقیت تغییر کرد.",
            "success"
        )

        return redirect(
            url_for(
                "admin.password_reset_requests"
            )
        )

    return render_template(
        "admin/password_reset_form.html",
        reset_request=reset_request,
        user=user
    )


# =========================================================
# فعال / غیرفعال کردن کسب‌وکار
# =========================================================

@admin_bp.route(
    "/businesses/<int:business_id>/toggle-active",
    methods=["POST"]
)
def toggle_business_active(business_id):

    business = db.session.get(
        Business,
        business_id
    )

    if business is None:
        from flask import abort

        abort(404)

    # تغییر وضعیت
    business.is_active = not business.is_active

    db.session.commit()

    if business.is_active:

        flash(
            f"کسب‌وکار «{business.name}» دوباره فعال شد.",
            "success"
        )

    else:

        flash(
            f"کسب‌وکار «{business.name}» غیرفعال شد و دیگر در صفحات عمومی نمایش داده نمی‌شود.",
            "warning"
        )

    return redirect(
        url_for("admin.users")
    )
@admin_bp.route(
    "/subscriptions/<int:subscription_id>/edit",
    methods=["GET", "POST"]
)
def edit_subscription(subscription_id):

    subscription = db.session.get(
        Subscription,
        subscription_id
    )

    if subscription is None:
        from flask import abort
        abort(404)

    if request.method == "POST":

        start_date_text = request.form.get(
            "start_date",
            ""
        ).strip()

        end_date_text = request.form.get(
            "end_date",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "active"
        ).strip()

        is_active = (
            request.form.get("is_active") == "1"
        )

        try:
            start_date = datetime.fromisoformat(
                start_date_text
            )

            end_date = datetime.fromisoformat(
                end_date_text
            )

            if start_date.tzinfo is None:
                start_date = start_date.replace(
                    tzinfo=timezone.utc
                )

            if end_date.tzinfo is None:
                end_date = end_date.replace(
                    tzinfo=timezone.utc
                )

        except ValueError:
            flash(
                "تاریخ وارد شده معتبر نیست.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_subscription",
                    subscription_id=subscription.id
                )
            )

        if end_date <= start_date:
            flash(
                "تاریخ پایان باید بعد از تاریخ شروع باشد.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_subscription",
                    subscription_id=subscription.id
                )
            )

        allowed_statuses = {
            "active",
            "pending_payment",
            "pending_review",
            "rejected"
        }

        if status not in allowed_statuses:
            status = "active"

        subscription.start_date = start_date
        subscription.end_date = end_date
        subscription.status = status
        subscription.is_active = is_active

        # اگر اشتراک فعال شد، کسب‌وکارهای کاربر هم فعال شوند.
        if status == "active" and is_active:

            businesses = db.session.scalars(
                db.select(Business).where(
                    Business.user_id == subscription.user_id
                )
            ).all()

            for business in businesses:
                business.is_active = True

        db.session.commit()

        flash(
            "اطلاعات اشتراک با موفقیت ویرایش شد.",
            "success"
        )

        return redirect(
            url_for(
                "admin.users"
            )
        )

    return render_template(
        "admin/subscription_edit.html",
        subscription=subscription
    )


# =========================================================
# ابزارهای تست سریع وضعیت اشتراک
# =========================================================

@admin_bp.route("/subscriptions/<int:subscription_id>/test-state/<string:state>", methods=["POST"])
def test_subscription_state(subscription_id, state):
    subscription = db.session.get(Subscription, subscription_id)

    if subscription is None:
        abort(404)

    now = datetime.now(timezone.utc)

    # برای اینکه تست دقیقاً روی همین اشتراک انجام شود،
    # سایر اشتراک‌های فعال این کاربر را موقتاً غیرفعال می‌کنیم.
    other_active_subscriptions = db.session.scalars(
        db.select(Subscription).where(
            Subscription.user_id == subscription.user_id,
            Subscription.id != subscription.id,
            Subscription.status == "active",
            Subscription.is_active.is_(True)
        )
    ).all()

    for old_subscription in other_active_subscriptions:
        old_subscription.is_active = False

    if state == "active":
        subscription.start_date = now - timedelta(days=1)
        subscription.end_date = now + timedelta(days=30)
        subscription.status = "active"
        subscription.is_active = True

        businesses = db.session.scalars(
            db.select(Business).where(
                Business.user_id == subscription.user_id
            )
        ).all()

        for business in businesses:
            business.is_active = True

        message = "اشتراک برای تست به حالت فعال تغییر کرد."

    elif state == "grace":
        subscription.start_date = now - timedelta(days=31)
        subscription.end_date = now - timedelta(days=1)
        subscription.status = "active"
        subscription.is_active = True

        businesses = db.session.scalars(
            db.select(Business).where(
                Business.user_id == subscription.user_id
            )
        ).all()

        for business in businesses:
            business.is_active = True

        message = "اشتراک برای تست وارد دوره مهلت ۱۰ روزه شد."

    elif state == "archive":
        subscription.start_date = now - timedelta(days=41)
        subscription.end_date = now - timedelta(days=11)
        subscription.status = "active"
        subscription.is_active = True

        businesses = db.session.scalars(
            db.select(Business).where(
                Business.user_id == subscription.user_id
            )
        ).all()

        for business in businesses:
            business.is_active = False

        message = "اشتراک برای تست به وضعیت آرشیو تغییر کرد."

    else:
        flash("وضعیت تست معتبر نیست.", "error")
        return redirect(url_for("admin.users"))

    db.session.commit()

    flash(message, "success")
    return redirect(url_for("admin.users"))