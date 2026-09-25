from datetime import datetime, timezone, timedelta
import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from app.extensions import db
from app.models import User, Plan, Subscription, PasswordResetRequest


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not first_name or not last_name:

            flash(
                "نام و نام خانوادگی الزامی است.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        if not username or not password:

            flash(
                "نام کاربری و رمز عبور الزامی است.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        # -------------------------------------------------
        # اعتبارسنجی نام کاربری
        # فقط حروف انگلیسی، اعداد، _ و -
        # -------------------------------------------------

        if not re.fullmatch(
            r"[A-Za-z0-9_-]+",
            username
        ):

            flash(
                "نام کاربری فقط می‌تواند شامل حروف انگلیسی، عدد، _ و - باشد و نباید فاصله داشته باشد.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        if password != confirm_password:

            flash(
                "تکرار رمز عبور صحیح نیست.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        # -------------------------------------------------
        # بررسی تکراری نبودن نام کاربری
        # -------------------------------------------------

        existing_user = db.session.scalar(
            db.select(User)
            .where(
                User.username == username
            )
        )

        if existing_user:

            flash(
                "این نام کاربری قبلاً ثبت شده است.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        # -------------------------------------------------
        # پیدا کردن پلن رایگان
        # -------------------------------------------------

        free_plan = db.session.scalar(
            db.select(Plan)
            .where(
                Plan.name == "رایگان",
                Plan.is_active.is_(True)
            )
        )

        if free_plan is None:

            flash(
                "پلن رایگان در سیستم تعریف نشده است. لطفاً با مدیر سایت تماس بگیرید.",
                "error"
            )

            return render_template(
                "auth/register.html",
                first_name=first_name,
                last_name=last_name,
                username=username
            )

        # -------------------------------------------------
        # ایجاد کاربر
        # -------------------------------------------------

        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username
        )

        user.set_password(password)

        db.session.add(user)

        # -------------------------------------------------
        # ایجاد اشتراک رایگان برای کاربر
        # -------------------------------------------------

        start_date = datetime.now(timezone.utc)

        end_date = start_date + timedelta(
            days=free_plan.duration_days
        )

        subscription = Subscription(
            user=user,
            plan=free_plan,
            start_date=start_date,
            end_date=end_date,
            status="active",
            is_active=True
        )

        db.session.add(subscription)

        # -------------------------------------------------
        # ذخیره کاربر و اشتراک
        # -------------------------------------------------

        db.session.commit()

        # -------------------------------------------------
        # ورود خودکار کاربر
        # -------------------------------------------------

        login_user(user)

        flash(
            f"سلام {user.first_name}، خوش آمدی!",
            "success"
        )

        return redirect(
            url_for("dashboard.index")
        )

    return render_template(
        "auth/register.html"
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = db.session.scalar(
            db.select(User)
            .where(
                User.username == username
            )
        )

        if user is None or not user.check_password(password):

            flash(
                "نام کاربری یا رمز عبور اشتباه است.",
                "error"
            )

            return render_template(
                "auth/login.html",
                username=username
            )

        if not user.is_active:

            flash(
                "حساب شما غیرفعال است.",
                "error"
            )

            return render_template(
                "auth/login.html",
                username=username
            )

        login_user(user)

        flash(
            f"سلام {user.first_name}، خوش آمدی!",
            "success"
        )

        return redirect(
            url_for("dashboard.index")
        )

    return render_template(
        "auth/login.html"
    )





@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard.index")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        if not username or not mobile:

            flash(
                "نام کاربری و شماره موبایل را وارد کنید.",
                "error"
            )

            return render_template(
                "auth/forgot_password.html",
                username=username,
                mobile=mobile
            )

        # -------------------------------------------------
        # پیدا کردن کاربر با نام کاربری و شماره موبایل
        # -------------------------------------------------

        user = db.session.scalar(
            db.select(User)
            .where(
                User.username == username,
                User.mobile == mobile
            )
        )

        if user is None:

            flash(
                "اطلاعات واردشده با حساب کاربری شما مطابقت ندارد.",
                "error"
            )

            return render_template(
                "auth/forgot_password.html",
                username=username,
                mobile=mobile
            )

        # -------------------------------------------------
        # بررسی درخواست قبلی در حال بررسی
        # -------------------------------------------------

        existing_request = db.session.scalar(
            db.select(PasswordResetRequest)
            .where(
                PasswordResetRequest.user_id == user.id,
                PasswordResetRequest.status == "pending"
            )
        )

        if existing_request:

            flash(
                "درخواست بازیابی رمز شما قبلاً ثبت شده و در حال بررسی است.",
                "info"
            )

            return render_template(
                "auth/forgot_password.html",
                username=username,
                mobile=mobile
            )

        # -------------------------------------------------
        # ثبت درخواست جدید
        # -------------------------------------------------

        reset_request = PasswordResetRequest(
            user_id=user.id,
            status="pending"
        )

        db.session.add(reset_request)
        db.session.commit()

        flash(
            "درخواست بازیابی رمز عبور شما با موفقیت ثبت شد. پس از بررسی، رمز جدید برای شما ارسال خواهد شد.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/forgot_password.html"
    )

@auth_bp.route("/logout")
def logout():

    logout_user()

    return redirect(
        url_for("public.home")
    )


# =========================================================
# حساب کاربری
# =========================================================

@auth_bp.route("/account", methods=["GET", "POST"])
def account():

    if not current_user.is_authenticated:

        return redirect(
            url_for("auth.login")
        )

    if request.method == "POST":

        form_type = request.form.get(
            "form_type",
            ""
        )

        # -------------------------------------------------
        # ویرایش اطلاعات حساب
        # -------------------------------------------------

        if form_type == "profile":

            first_name = request.form.get(
                "first_name",
                ""
            ).strip()

            last_name = request.form.get(
                "last_name",
                ""
            ).strip()

            username = request.form.get(
                "username",
                ""
            ).strip().lower()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            mobile = request.form.get(
                "mobile",
                ""
            ).strip()

            if not first_name or not last_name:

                flash(
                    "نام و نام خانوادگی الزامی است.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            if not username:

                flash(
                    "نام کاربری الزامی است.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            if not re.fullmatch(
                r"[A-Za-z0-9_-]+",
                username
            ):

                flash(
                    "نام کاربری فقط می‌تواند شامل حروف انگلیسی، عدد، _ و - باشد و نباید فاصله داشته باشد.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            # -------------------------------------------------
            # بررسی تکراری نبودن username
            # -------------------------------------------------

            existing_user = db.session.scalar(
                db.select(User)
                .where(
                    User.username == username,
                    User.id != current_user.id
                )
            )

            if existing_user:

                flash(
                    "این نام کاربری قبلاً استفاده شده است.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            # -------------------------------------------------
            # بررسی تکراری نبودن email
            # -------------------------------------------------

            if email:

                existing_email = db.session.scalar(
                    db.select(User)
                    .where(
                        User.email == email,
                        User.id != current_user.id
                    )
                )

                if existing_email:

                    flash(
                        "این ایمیل قبلاً برای حساب دیگری ثبت شده است.",
                        "error"
                    )

                    return redirect(
                        url_for("auth.account")
                    )

            # -------------------------------------------------
            # بررسی تکراری نبودن mobile
            # -------------------------------------------------

            if mobile:

                existing_mobile = db.session.scalar(
                    db.select(User)
                    .where(
                        User.mobile == mobile,
                        User.id != current_user.id
                    )
                )

                if existing_mobile:

                    flash(
                        "این شماره موبایل قبلاً برای حساب دیگری ثبت شده است.",
                        "error"
                    )

                    return redirect(
                        url_for("auth.account")
                    )

            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.username = username
            current_user.email = email or None
            current_user.mobile = mobile or None

            db.session.commit()

            flash(
                "اطلاعات حساب با موفقیت ذخیره شد.",
                "success"
            )

            return redirect(
                url_for("auth.account")
            )

        # -------------------------------------------------
        # تغییر رمز عبور
        # -------------------------------------------------

        if form_type == "password":

            current_password = request.form.get(
                "current_password",
                ""
            )

            new_password = request.form.get(
                "new_password",
                ""
            )

            confirm_password = request.form.get(
                "confirm_password",
                ""
            )

            if not current_password:

                flash(
                    "رمز عبور فعلی را وارد کنید.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            if not current_user.check_password(
                current_password
            ):

                flash(
                    "رمز عبور فعلی صحیح نیست.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            if not new_password:

                flash(
                    "رمز عبور جدید را وارد کنید.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            if new_password != confirm_password:

                flash(
                    "تکرار رمز عبور جدید صحیح نیست.",
                    "error"
                )

                return redirect(
                    url_for("auth.account")
                )

            current_user.set_password(
                new_password
            )

            db.session.commit()

            flash(
                "رمز عبور با موفقیت تغییر کرد.",
                "success"
            )

            return redirect(
                url_for("auth.account")
            )

        flash(
            "درخواست نامعتبر است.",
            "error"
        )

        return redirect(
            url_for("auth.account")
        )

    return render_template(
        "auth/account.html"
    )