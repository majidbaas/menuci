from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from sqlalchemy import func
from datetime import datetime, timezone
import os
import uuid
import re
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

from app.extensions import db
from app.models.business import Business
from app.models.category import Category
from app.models.product import Product
from app.models.subscription import Subscription
from app.services.subscription import get_subscription_state
from app.business_types import (
    get_business_type_choices,
    get_business_type
)
from app.services.qr_service import (
    generate_qr_code,
    generate_qr_card
)

business_bp = Blueprint(
    "business",
    __name__,
    url_prefix="/business"
)


# =========================================================
# انواع مجاز کسب‌وکار
# =========================================================

ALLOWED_BUSINESS_TYPES = {
    "restaurant",
    "cafe",
    "fastfood",
    "juice",
    "pastry",
    "bakery",
    "beauty",
    "shop",
    "pharmacy",
    "services",
    "other"
}


# =========================================================
# بررسی امکان تغییر اطلاعات کسب‌وکار
# =========================================================

def check_business_editable(business):
    """
    بررسی می‌کند که کاربر اجازه تغییر اطلاعات
    کسب‌وکار را دارد یا خیر.

    فقط زمانی اجازه تغییر داریم که اشتراک فعال باشد.
    در دوره ۱۰ روزه پس از انقضا، کسب‌وکار قابل مشاهده است
    اما هیچ تغییری روی آن مجاز نیست.
    """

    subscription_state = get_subscription_state(
        business.user_id
    )

    if subscription_state["state"] == "active":
        return True

    return False

# =========================================================
# محصولات
# =========================================================

@business_bp.route("/<int:business_id>/products")
@login_required
def products(business_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:
        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )
        return redirect(
            url_for("dashboard.index")
        )

    products = db.session.scalars(
        db.select(Product)
        .where(
            Product.business_id == business.id
        )
        .order_by(
            Product.sort_order,
            Product.id
        )
    ).all()

    return render_template(
        "business/products.html",
        business=business,
        products=products
    )


# =========================================================
# صفحه مدیریت کسب‌وکار
# =========================================================

from sqlalchemy import func


@business_bp.route(
    "/<int:business_id>/manage"
)
@login_required
def manage(business_id):

    # -----------------------------------------------------
    # پیدا کردن کسب‌وکار و بررسی مالکیت
    # -----------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # -----------------------------------------------------
    # تعداد محصولات
    # -----------------------------------------------------

    products_count = db.session.scalar(
        db.select(
            func.count(Product.id)
        ).where(
            Product.business_id == business.id
        )
    ) or 0

    # -----------------------------------------------------
    # تعداد دسته‌بندی‌ها
    # -----------------------------------------------------

    categories_count = db.session.scalar(
        db.select(
            func.count(Category.id)
        ).where(
            Category.business_id == business.id
        )
    ) or 0

    # -----------------------------------------------------
    # نمایش صفحه
    # -----------------------------------------------------

    return render_template(
        "business/manage.html",
        business=business,
        products_count=products_count,
        categories_count=categories_count
    )
    
    
# =========================================================
# QR Code
# =========================================================

@business_bp.route("/<int:business_id>/qr")
@login_required
def qr_code(business_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:
        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )
        return redirect(
            url_for("dashboard.index")
        )

    # آدرس صفحه عمومی کسب‌وکار
    public_url = url_for(
        "public.business_page",
        slug=business.slug,
        _external=True
    )

    # نام فایل QR
    filename = f"business_{business.id}.png"

    # ساخت QR
    qr_path = generate_qr_code(
        public_url,
        filename
    )

    return render_template(
        "business/qr.html",
        business=business,
        qr_path=qr_path,
        public_url=public_url,
        business_config=get_business_type(business.business_type)
    ) 
    
   # =========================================================
# Download QR Code
# =========================================================

@business_bp.route("/<int:business_id>/qr/download")
@login_required
def download_qr_code(business_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:
        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )
        return redirect(
            url_for("dashboard.index")
        )

    qr_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "qr"
    )

    filename = f"business_{business.id}.png"

    file_path = os.path.join(
        qr_folder,
        filename
    )

 
    public_url = url_for(
        "public.business_page",
        slug=business.slug,
        _external=True
    )

    generate_qr_card(
        public_url,
        business.name,
        business.business_type,
        filename
    )

    from flask import send_file

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{business.slug}-qr.png",
        mimetype="image/png"
    )
 

# =========================================================
# ایجاد کسب‌وکار
# =========================================================

@business_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():

    business_type_choices = get_business_type_choices()

    allowed_business_types = {
        item["value"]
        for item in business_type_choices
    }

    if request.method == "POST":

        # -------------------------------------------------
        # بررسی اشتراک فعال کاربر
        # -------------------------------------------------

        now = datetime.now(timezone.utc)

        subscription = db.session.scalar(
            db.select(Subscription)
            .where(
                Subscription.user_id == current_user.id,
                Subscription.is_active.is_(True),
                Subscription.end_date > now
            )
            .order_by(
                Subscription.end_date.desc()
            )
        )

        if subscription is None:

            flash(
                "اشتراک شما فعال نیست. برای ایجاد کسب‌وکار جدید، لطفاً اشتراک خود را تمدید یا ارتقا دهید.",
                "error"
            )

            return redirect(
                url_for("dashboard.index")
            )
        # -------------------------------------------------
        # بررسی سقف تعداد کسب‌وکار
        # -------------------------------------------------

        businesses_count = db.session.scalar(
            db.select(
                func.count(Business.id)
            ).where(
                Business.user_id == current_user.id
            )
        ) or 0

        if businesses_count >= subscription.plan.max_businesses:

            flash(
                f"سقف ایجاد کسب‌وکار در پلن «{subscription.plan.name}» "
                f"{subscription.plan.max_businesses} مورد است.",
                "error"
            )

            return redirect(
                url_for("dashboard.index")
            )

        # -------------------------------------------------
        # دریافت اطلاعات فرم
        # -------------------------------------------------

        name = request.form.get("name", "").strip()
        business_type = request.form.get("business_type", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        description = request.form.get("description", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        # -------------------------------------------------
        # اعتبارسنجی نوع کسب‌وکار
        # -------------------------------------------------

        if business_type not in allowed_business_types:

            flash(
                "لطفاً نوع کسب‌وکار را انتخاب کنید.",
                "error"
            )

            return render_template(
                "business/create.html",
                business_type_choices=business_type_choices
            )

        if not name:

            flash(
                "نام کسب‌وکار الزامی است.",
                "error"
            )

            return render_template(
                "business/create.html",
                business_type_choices=business_type_choices
            )

        if not slug:

            flash(
                "آدرس اختصاصی کسب‌وکار الزامی است.",
                "error"
            )

            return render_template(
                "business/create.html",
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # بررسی تکراری نبودن آدرس
        # -------------------------------------------------

        existing_business = db.session.scalar(
            db.select(Business)
            .where(Business.slug == slug)
        )

        if existing_business:

            flash(
                "این آدرس قبلاً استفاده شده است. یک آدرس دیگر انتخاب کنید.",
                "error"
            )

            return render_template(
                "business/create.html",
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # ایجاد کسب‌وکار
        # -------------------------------------------------

        business = Business(
            user_id=current_user.id,
            name=name,
            business_type=business_type,
            slug=slug,
            description=description or None,
            phone=phone or None,
            address=address or None
        )

        db.session.add(business)
        db.session.commit()

        flash(
            "کسب‌وکار با موفقیت ایجاد شد.",
            "success"
        )

        return redirect(
            url_for("dashboard.index")
        )

    return render_template(
        "business/create.html",
        business_type_choices=business_type_choices
    )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "business/create.html",
        business_type_choices=business_type_choices
    )
# =========================================================
# ویرایش کسب‌وکار
# =========================================================

@business_bp.route(
    "/edit/<int:business_id>",
    methods=["GET", "POST"]
)
@login_required
def edit(business_id):

    # -----------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # -----------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    business_type_choices = get_business_type_choices()

    allowed_business_types = {
        item["value"]
        for item in business_type_choices
    }

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        if not check_business_editable(business):

            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر اطلاعات کسب‌وکار وجود ندارد.",
                "error"
            )

            return redirect(
                url_for("dashboard.index")
            )

        name = request.form.get("name", "").strip()
        business_type = request.form.get("business_type", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        description = request.form.get("description", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        # -------------------------------------------------
        # اعتبارسنجی نوع کسب‌وکار
        # -------------------------------------------------

        if business_type not in allowed_business_types:

            flash(
                "لطفاً نوع کسب‌وکار را انتخاب کنید.",
                "error"
            )

            return render_template(
                "business/edit.html",
                business=business,
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # اعتبارسنجی نام
        # -------------------------------------------------

        if not name:

            flash(
                "نام کسب‌وکار الزامی است.",
                "error"
            )

            return render_template(
                "business/edit.html",
                business=business,
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # اعتبارسنجی Slug
        # -------------------------------------------------

        if not slug:

            flash(
                "آدرس اختصاصی الزامی است.",
                "error"
            )

            return render_template(
                "business/edit.html",
                business=business,
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # بررسی تکراری نبودن Slug
        # -------------------------------------------------

        existing_business = db.session.scalar(
            db.select(Business).where(
                Business.slug == slug,
                Business.id != business.id
            )
        )

        if existing_business:

            flash(
                "این آدرس قبلاً استفاده شده است.",
                "error"
            )

            return render_template(
                "business/edit.html",
                business=business,
                business_type_choices=business_type_choices
            )

        # -------------------------------------------------
        # بروزرسانی اطلاعات
        # -------------------------------------------------

        business.name = name
        business.business_type = business_type
        business.slug = slug
        business.description = description or None
        business.phone = phone or None
        business.address = address or None

        db.session.commit()

        flash(
            "اطلاعات کسب‌وکار با موفقیت بروزرسانی شد.",
            "success"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "business/edit.html",
        business=business,
        business_type_choices=business_type_choices
    )
    
    
    
 # =========================================================
# ظاهر صفحه عمومی کسب‌وکار
# =========================================================

@business_bp.route(
    "/<int:business_id>/appearance",
    methods=["GET", "POST"]
)
@login_required
def appearance(business_id):

    # -----------------------------------------------------
    # پیدا کردن کسب‌وکار و بررسی مالکیت
    # -----------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        if not check_business_editable(business):

            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر ظاهر کسب‌وکار وجود ندارد.",
                "error"
            )

            return redirect(
                url_for("dashboard.index")
            )

        primary_color = request.form.get(
            "primary_color",
            ""
        ).strip()

        # -------------------------------------------------
        # اگر رنگ وارد نشده باشد
        # -------------------------------------------------

        if not primary_color:

            flash(
                "لطفاً یک رنگ اصلی انتخاب کنید.",
                "error"
            )

            return render_template(
                "business/appearance.html",
                business=business
            )

        # -------------------------------------------------
        # بررسی فرمت HEX
        # -------------------------------------------------

      

        if not re.fullmatch(
            r"#[0-9A-Fa-f]{6}",
            primary_color
        ):

            flash(
                "رنگ انتخاب شده معتبر نیست.",
                "error"
            )

            return render_template(
                "business/appearance.html",
                business=business
            )

        # -------------------------------------------------
        # ذخیره
        # -------------------------------------------------

        business.primary_color = primary_color

        db.session.commit()

        flash(
            "ظاهر صفحه با موفقیت بروزرسانی شد.",
            "success"
        )

        return redirect(
            url_for(
                "business.appearance",
                business_id=business.id
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "business/appearance.html",
        business=business
    )
    
# =========================================================
# مدیریت لوگو و بنر کسب‌وکار
# =========================================================

@business_bp.route(
    "/<int:business_id>/appearance/images",
    methods=["POST"]
)
@login_required
def update_business_images(business_id):

    # -----------------------------------------------------
    # پیدا کردن کسب‌وکار و بررسی مالکیت
    # -----------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # -----------------------------------------------------
    # بررسی امکان تغییر
    # -----------------------------------------------------

    if not check_business_editable(business):

        flash(
            "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر تصاویر کسب‌وکار وجود ندارد.",
            "error"
        )

        return redirect(
            url_for(
                "business.appearance",
                business_id=business.id
            )
        )

    # -----------------------------------------------------
    # فایل لوگو
    # -----------------------------------------------------

    logo_file = request.files.get(
        "logo"
    )

    # -----------------------------------------------------
    # فایل بنر
    # -----------------------------------------------------

    banner_file = request.files.get(
        "banner"
    )

    # =====================================================
    # لوگو
    # =====================================================

    if logo_file and logo_file.filename:

        if not allowed_image(
            logo_file.filename
        ):

            flash(
                "فرمت لوگو مجاز نیست. "
                "فرمت‌های مجاز: JPG، JPEG، PNG و WEBP",
                "error"
            )

            return redirect(
                url_for(
                    "business.appearance",
                    business_id=business.id
                )
            )

        new_logo = save_business_image(
            logo_file,
            "businesses/logos"
        )

        if new_logo is None:

            flash(
                "حجم لوگو نباید بیشتر از ۵ مگابایت باشد.",
                "error"
            )

            return redirect(
                url_for(
                    "business.appearance",
                    business_id=business.id
                )
            )

        old_logo = business.logo

        business.logo = new_logo

        if old_logo:
            delete_business_image(
                "uploads/" + old_logo
                if not old_logo.startswith("uploads/")
                else old_logo
            )

    # =====================================================
    # بنر
    # =====================================================

    if banner_file and banner_file.filename:

        if not allowed_image(
            banner_file.filename
        ):

            flash(
                "فرمت بنر مجاز نیست. "
                "فرمت‌های مجاز: JPG، JPEG، PNG و WEBP",
                "error"
            )

            return redirect(
                url_for(
                    "business.appearance",
                    business_id=business.id
                )
            )

        new_banner = save_business_image(
            banner_file,
            "businesses/banners"
        )

        if new_banner is None:

            flash(
                "حجم بنر نباید بیشتر از ۵ مگابایت باشد.",
                "error"
            )

            return redirect(
                url_for(
                    "business.appearance",
                    business_id=business.id
                )
            )

        old_banner = business.banner

        business.banner = new_banner

        if old_banner:
            delete_business_image(
                "uploads/" + old_banner
                if not old_banner.startswith("uploads/")
                else old_banner
            )

    # =====================================================
    # ذخیره
    # =====================================================

    db.session.commit()

    flash(
        "تصاویر کسب‌وکار با موفقیت بروزرسانی شدند.",
        "success"
    )

    return redirect(
        url_for(
            "business.appearance",
            business_id=business.id
        )
    )    
    # =========================================================
# داشبورد کسب‌وکار
# =========================================================

@business_bp.route(
    "/<int:business_id>/dashboard"
)
@login_required
def dashboard(business_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:
        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )
        return redirect(
            url_for("dashboard.index")
        )

    products_count = db.session.scalar(
        db.select(
            db.func.count(Product.id)
        ).where(
            Product.business_id == business.id
        )
    ) or 0

    categories_count = db.session.scalar(
        db.select(
            db.func.count(Category.id)
        ).where(
            Category.business_id == business.id
        )
    ) or 0

    return render_template(
        "business/dashboard.html",
        business=business,
        products_count=products_count,
        categories_count=categories_count
    )
    
# =========================================================
# ایجاد محصول
# =========================================================

@business_bp.route(
    "/<int:business_id>/products/create",
    methods=["GET", "POST"]
)
@login_required
def create_product(business_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:
        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )
        return redirect(
            url_for("dashboard.index")
        )

    categories = db.session.scalars(
        db.select(Category)
        .where(
            Category.business_id == business.id,
            Category.is_active == True
        )
        .order_by(
            Category.sort_order,
            Category.id
        )
    ).all()

    if request.method == "POST":
        # -------------------------------------------------
        # بررسی اشتراک فعال و سقف تعداد محصولات
        # -------------------------------------------------

        now = datetime.now(timezone.utc)

        subscription = db.session.scalar(
            db.select(Subscription)
            .where(
                Subscription.user_id == current_user.id,
                Subscription.is_active.is_(True),
                Subscription.end_date > now
            )
            .order_by(
                Subscription.end_date.desc()
            )
        )

        if subscription is None:

            flash(
                "اشتراک شما فعال نیست. برای ایجاد محصول جدید، "
                "لطفاً اشتراک خود را تمدید یا ارتقا دهید.",
                "error"
            )

            return redirect(
                url_for(
                    "business.products",
                    business_id=business.id
                )
            )

        products_count = db.session.scalar(
            db.select(
                func.count(Product.id)
            ).where(
                Product.business_id == business.id
            )
        ) or 0

        if products_count >= subscription.plan.max_products:

            flash(
                f"سقف ایجاد محصول در پلن «{subscription.plan.name}» "
                f"{subscription.plan.max_products} مورد است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.products",
                    business_id=business.id
                )
            )
        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        sort_order = request.form.get(
            "sort_order",
            "0"
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        # =================================================
        # عکس محصول
        # =================================================

        image_file = request.files.get(
            "image"
        )

        # -------------------------------------------------
        # بررسی دسته‌بندی
        # -------------------------------------------------

        category = None

        if category_id:

            try:
                category_id = int(category_id)

            except ValueError:

                flash(
                    "دسته‌بندی انتخاب شده صحیح نیست.",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.create_product",
                        business_id=business.id
                    )
                )

            category = db.session.scalar(
                db.select(Category)
                .where(
                    Category.id == category_id,
                    Category.business_id == business.id,
                    Category.is_active == True
                )
            )

            if category is None:

                flash(
                    "دسته‌بندی انتخاب شده معتبر نیست.",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.create_product",
                        business_id=business.id
                    )
                )

        # -------------------------------------------------
        # بررسی نام
        # -------------------------------------------------

        if not name:

            flash(
                "نام محصول الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.create_product",
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # بررسی slug
        # -------------------------------------------------

        if not slug:

            flash(
                "آدرس اختصاصی محصول الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.create_product",
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # بررسی slug تکراری
        # -------------------------------------------------

        existing_product = db.session.scalar(
            db.select(Product)
            .where(
                Product.business_id == business.id,
                Product.slug == slug
            )
        )

        if existing_product:

            flash(
                "این آدرس برای یکی از محصولات این کسب‌وکار "
                "قبلاً استفاده شده است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.create_product",
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # تبدیل قیمت
        # -------------------------------------------------

        try:
            price = float(price or 0)

        except ValueError:

            flash(
                "قیمت وارد شده صحیح نیست.",
                "error"
            )

            return redirect(
                url_for(
                    "business.create_product",
                    business_id=business.id
                )
            )

        # -------------------------------------------------
        # تبدیل ترتیب
        # -------------------------------------------------

        try:
            sort_order = int(sort_order or 0)

        except ValueError:

            sort_order = 0

        # -------------------------------------------------
        # بررسی فرمت عکس
        # -------------------------------------------------

        image_path = None

        if image_file and image_file.filename:

            if not allowed_image(
                image_file.filename
            ):

                flash(
                    "فرمت عکس مجاز نیست. "
                    "فرمت‌های مجاز: JPG، JPEG، PNG و WEBP",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.create_product",
                        business_id=business.id
                    )
                )

            image_path = save_product_image(
                image_file
            )

        # -------------------------------------------------
        # ایجاد محصول
        # -------------------------------------------------

        product = Product(
            business_id=business.id,
            category_id=category.id if category else None,
            name=name,
            slug=slug,
            description=description or None,
            price=price,
            image=image_path,
            sort_order=sort_order
        )

        db.session.add(product)
        db.session.commit()

        flash(
            "محصول با موفقیت ایجاد شد.",
            "success"
        )

        return redirect(
            url_for(
                "business.products",
                business_id=business.id
            )
        )

    return render_template(
        "business/product_create.html",
        business=business,
        categories=categories
    )
 # =========================================================
# ویرایش محصول
# =========================================================

@business_bp.route(
    "/<int:business_id>/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_product(business_id, product_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    product = db.session.scalar(
        db.select(Product)
        .where(
            Product.id == product_id,
            Product.business_id == business.id
        )
    )

    if product is None:

        flash(
            "محصول موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for(
                "business.products",
                business_id=business.id
            )
        )

    categories = db.session.scalars(
        db.select(Category)
        .where(
            Category.business_id == business.id,
            Category.is_active == True
        )
        .order_by(
            Category.sort_order,
            Category.id
        )
    ).all()

    if request.method == "POST":

        if not check_business_editable(business):

            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر محصولات وجود ندارد.",
                "error"
            )

            return redirect(
                url_for("business.products", business_id=business.id)
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        sort_order = request.form.get(
            "sort_order",
            "0"
        ).strip()

        category_id = request.form.get(
            "category_id",
            ""
        ).strip()

        category = None

        # =================================================
        # عکس جدید
        # =================================================

        image_file = request.files.get(
            "image"
        )

        # -------------------------------------------------
        # بررسی دسته‌بندی
        # -------------------------------------------------

        if category_id:

            try:
                category_id = int(category_id)

            except ValueError:

                flash(
                    "دسته‌بندی انتخاب شده صحیح نیست.",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.edit_product",
                        business_id=business.id,
                        product_id=product.id
                    )
                )

            category = db.session.scalar(
                db.select(Category)
                .where(
                    Category.id == category_id,
                    Category.business_id == business.id,
                    Category.is_active == True
                )
            )

            if category is None:

                flash(
                    "دسته‌بندی انتخاب شده معتبر نیست.",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.edit_product",
                        business_id=business.id,
                        product_id=product.id
                    )
                )

        # -------------------------------------------------
        # بررسی نام
        # -------------------------------------------------

        if not name:

            flash(
                "نام محصول الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.edit_product",
                    business_id=business.id,
                    product_id=product.id
                )
            )

        # -------------------------------------------------
        # بررسی slug
        # -------------------------------------------------

        if not slug:

            flash(
                "آدرس اختصاصی محصول الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.edit_product",
                    business_id=business.id,
                    product_id=product.id
                )
            )

        # -------------------------------------------------
        # بررسی slug تکراری
        # -------------------------------------------------

        existing_product = db.session.scalar(
            db.select(Product)
            .where(
                Product.business_id == business.id,
                Product.slug == slug,
                Product.id != product.id
            )
        )

        if existing_product:

            flash(
                "این آدرس برای محصول دیگری استفاده شده است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.edit_product",
                    business_id=business.id,
                    product_id=product.id
                )
            )

        # -------------------------------------------------
        # تبدیل قیمت
        # -------------------------------------------------

        try:
            price = float(price or 0)

        except ValueError:

            flash(
                "قیمت وارد شده صحیح نیست.",
                "error"
            )

            return redirect(
                url_for(
                    "business.edit_product",
                    business_id=business.id,
                    product_id=product.id
                )
            )

        # -------------------------------------------------
        # تبدیل ترتیب
        # -------------------------------------------------

        try:
            sort_order = int(sort_order or 0)

        except ValueError:

            sort_order = 0

        # =================================================
        # آپلود عکس جدید
        # =================================================

        new_image_path = None

        if image_file and image_file.filename:

            if not allowed_image(
                image_file.filename
            ):

                flash(
                    "فرمت عکس مجاز نیست. "
                    "فرمت‌های مجاز: JPG، JPEG، PNG و WEBP",
                    "error"
                )

                return redirect(
                    url_for(
                        "business.edit_product",
                        business_id=business.id,
                        product_id=product.id
                    )
                )

            new_image_path = save_product_image(
                image_file
            )

        # -------------------------------------------------
        # بروزرسانی اطلاعات محصول
        # -------------------------------------------------

        product.name = name
        product.slug = slug
        product.description = description or None
        product.price = price
        product.sort_order = sort_order
        product.category_id = (
            category.id if category else None
        )

        # -------------------------------------------------
        # جایگزینی عکس
        # -------------------------------------------------

        if new_image_path:

            old_image_path = product.image

            product.image = new_image_path

            if old_image_path:
                delete_product_image(
                    old_image_path
                )

        db.session.commit()

        flash(
            "محصول با موفقیت بروزرسانی شد.",
            "success"
        )

        return redirect(
            url_for(
                "business.products",
                business_id=business.id
            )
        )

    return render_template(
        "business/product_edit.html",
        business=business,
        product=product,
        categories=categories
    )
    
    # =========================================================
# حذف محصول
# =========================================================

@business_bp.route(
    "/<int:business_id>/products/<int:product_id>/delete",
    methods=["POST"]
)
@login_required
def delete_product(business_id, product_id):

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    product = db.session.scalar(
        db.select(Product)
        .where(
            Product.id == product_id,
            Product.business_id == business.id
        )
    )

    if product is None:

        flash(
            "محصول موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for(
                "business.products",
                business_id=business.id
            )
        )

    if not check_business_editable(business):

        flash(
            "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان حذف محصول وجود ندارد.",
            "error"
        )

        return redirect(
            url_for(
                "business.products",
                business_id=business.id
            )
        )

    db.session.delete(product)
    db.session.commit()

    flash(
        "محصول با موفقیت حذف شد.",
        "success"
    )

    return redirect(
        url_for(
            "business.products",
            business_id=business.id
        )
    )
   



   
# =========================================================
# لیست دسته‌بندی‌ها
# =========================================================

@business_bp.route(
    "/<int:business_id>/categories"
)
@login_required
def categories(business_id):

    # ---------------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # ---------------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ---------------------------------------------------------
    # دسته‌بندی‌های همین کسب‌وکار
    # ---------------------------------------------------------

    categories = db.session.scalars(
        db.select(Category)
        .where(
            Category.business_id == business.id
        )
        .order_by(
            Category.sort_order,
            Category.id
        )
    ).all()

    return render_template(
        "business/categories.html",
        business=business,
        categories=categories
    )
 # =========================================================
# ایجاد دسته‌بندی
# =========================================================

@business_bp.route(
    "/<int:business_id>/categories/create",
    methods=["GET", "POST"]
)
@login_required
def create_category(business_id):

    # ---------------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # ---------------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return {
                "success": False,
                "message": "کسب‌وکار موردنظر پیدا نشد."
            }, 404

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if request.method == "POST":

        # -----------------------------------------------------
        # بررسی اشتراک فعال کاربر
        # -----------------------------------------------------

        now = datetime.now(timezone.utc)

        subscription = db.session.scalar(
            db.select(Subscription)
            .where(
                Subscription.user_id == current_user.id,
                Subscription.is_active.is_(True),
                Subscription.end_date > now
            )
            .order_by(
                Subscription.end_date.desc()
            )
        )

        if subscription is None:

            message = (
                "اشتراک شما فعال نیست. برای ایجاد دسته‌بندی جدید، "
                "لطفاً اشتراک خود را تمدید یا ارتقا دهید."
            )

            if request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest":

                return {
                    "success": False,
                    "message": message
                }, 403

            flash(
                message,
                "error"
            )

            return redirect(
                url_for(
                    "business.categories",
                    business_id=business.id
                )
            )

        # -----------------------------------------------------
        # بررسی سقف تعداد دسته‌بندی
        # -----------------------------------------------------

        categories_count = db.session.scalar(
            db.select(
                func.count(Category.id)
            ).where(
                Category.business_id == business.id
            )
        ) or 0

        if categories_count >= subscription.plan.max_categories:

            message = (
                f"سقف ایجاد دسته‌بندی در پلن "
                f"«{subscription.plan.name}» "
                f"{subscription.plan.max_categories} مورد است."
            )

            if request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest":

                return {
                    "success": False,
                    "message": message
                }, 403

            flash(
                message,
                "error"
            )

            return redirect(
                url_for(
                    "business.categories",
                    business_id=business.id
                )
            )

        # -----------------------------------------------------
        # دریافت اطلاعات فرم
        # -----------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        sort_order = request.form.get(
            "sort_order",
            "0"
        ).strip()

        # -----------------------------------------------------
        # بررسی نام
        # -----------------------------------------------------

        if not name:

            if request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest":

                return {
                    "success": False,
                    "message": "نام دسته‌بندی الزامی است."
                }, 400

            flash(
                "نام دسته‌بندی الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.create_category",
                    business_id=business.id
                )
            )

        # -----------------------------------------------------
        # تبدیل ترتیب
        # -----------------------------------------------------

        try:

            sort_order = int(
                sort_order or 0
            )

        except ValueError:

            sort_order = 0

        # -----------------------------------------------------
        # ایجاد دسته‌بندی
        # -----------------------------------------------------

        category = Category(
            business_id=business.id,
            name=name,
            description=description or None,
            sort_order=sort_order,
            is_active=True
        )

        db.session.add(category)
        db.session.commit()

        # -----------------------------------------------------
        # پاسخ Popup
        # -----------------------------------------------------

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return {
                "success": True,
                "message": "دسته‌بندی با موفقیت ایجاد شد.",
                "category": {
                    "id": category.id,
                    "name": category.name
                }
            }

        # -----------------------------------------------------
        # صفحه مستقل
        # -----------------------------------------------------

        flash(
            "دسته‌بندی با موفقیت ایجاد شد.",
            "success"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # ---------------------------------------------------------
    # نمایش فرم
    # ---------------------------------------------------------

    return render_template(
        "business/category_create.html",
        business=business
    )
# =========================================================
# ویرایش دسته‌بندی
# =========================================================

@business_bp.route(
    "/<int:business_id>/categories/<int:category_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_category(business_id, category_id):

    # ---------------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # ---------------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ---------------------------------------------------------
    # پیدا کردن دسته‌بندی متعلق به همین کسب‌وکار
    # ---------------------------------------------------------

    category = db.session.scalar(
        db.select(Category).where(
            Category.id == category_id,
            Category.business_id == business.id
        )
    )

    if category is None:

        flash(
            "دسته‌بندی موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # =========================================================
    # POST
    # =========================================================

    if request.method == "POST":

        if not check_business_editable(business):

            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر دسته‌بندی‌ها وجود ندارد.",
                "error"
            )

            return redirect(
                url_for(
                    "business.categories",
                    business_id=business.id
                )
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        sort_order = request.form.get(
            "sort_order",
            "0"
        ).strip()

        # -----------------------------------------------------
        # بررسی نام
        # -----------------------------------------------------

        if not name:

            flash(
                "نام دسته‌بندی الزامی است.",
                "error"
            )

            return redirect(
                url_for(
                    "business.edit_category",
                    business_id=business.id,
                    category_id=category.id
                )
            )

        # -----------------------------------------------------
        # تبدیل ترتیب
        # -----------------------------------------------------

        try:

            sort_order = int(
                sort_order or 0
            )

        except ValueError:

            sort_order = 0

        # -----------------------------------------------------
        # بروزرسانی
        # -----------------------------------------------------

        category.name = name

        category.description = (
            description or None
        )

        category.sort_order = sort_order

        db.session.commit()

        flash(
            "دسته‌بندی با موفقیت بروزرسانی شد.",
            "success"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # =========================================================
    # GET
    # =========================================================

    return render_template(
        "business/category_edit.html",
        business=business,
        category=category
    )

# =========================================================
# حذف دسته‌بندی
# =========================================================

@business_bp.route(
    "/<int:business_id>/categories/<int:category_id>/delete",
    methods=["POST"]
)
@login_required
def delete_category(business_id, category_id):

    # ---------------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # ---------------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ---------------------------------------------------------
    # پیدا کردن دسته‌بندی متعلق به همین کسب‌وکار
    # ---------------------------------------------------------

    category = db.session.scalar(
        db.select(Category).where(
            Category.id == category_id,
            Category.business_id == business.id
        )
    )

    if category is None:

        flash(
            "دسته‌بندی موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # ---------------------------------------------------------
    # بررسی امکان تغییر
    # ---------------------------------------------------------

    if not check_business_editable(business):

        flash(
            "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان حذف دسته‌بندی وجود ندارد.",
            "error"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # ---------------------------------------------------------
    # حذف
    # ---------------------------------------------------------

    db.session.delete(category)
    db.session.commit()

    flash(
        "دسته‌بندی با موفقیت حذف شد.",
        "success"
    )

    return redirect(
        url_for(
            "business.categories",
            business_id=business.id
        )
    )
# =========================================================
# تنظیمات آپلود عکس محصول
# =========================================================

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_IMAGE_EXTENSIONS
    )


def save_product_image(file):

    if not file or not file.filename:
        return None

    if not allowed_image(file.filename):
        return None

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "products"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    original_name = secure_filename(
        file.filename
    )

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    file_path = os.path.join(
        upload_folder,
        filename
    )

    file.save(file_path)

    return f"uploads/products/{filename}"


def delete_product_image(image_path):

    if not image_path:
        return

    file_path = os.path.join(
        current_app.static_folder,
        image_path
    )

    if os.path.isfile(file_path):
        os.remove(file_path)

# =========================================================
# آپلود لوگو و بنر کسب‌وکار
# =========================================================

MAX_BUSINESS_IMAGE_SIZE = 5 * 1024 * 1024


def save_business_image(file, folder_name):
    """
    ذخیره امن تصویر لوگو یا بنر کسب‌وکار
    """

    if not file or not file.filename:
        return None

    # -----------------------------------------------------
    # بررسی فرمت
    # -----------------------------------------------------

    if not allowed_image(file.filename):
        return None

    # -----------------------------------------------------
    # بررسی حجم فایل
    # -----------------------------------------------------

    file.stream.seek(0, os.SEEK_END)

    file_size = file.stream.tell()

    file.stream.seek(0)

    if file_size > MAX_BUSINESS_IMAGE_SIZE:
        return None

    # -----------------------------------------------------
    # ساخت پوشه
    # -----------------------------------------------------

    upload_folder = os.path.join(
        current_app.static_folder,
        "uploads",
        folder_name
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    # -----------------------------------------------------
    # گرفتن پسوند امن
    # -----------------------------------------------------

    original_name = secure_filename(
        file.filename
    )

    if "." not in original_name:
        return None

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()

    # -----------------------------------------------------
    # نام تصادفی
    # -----------------------------------------------------

    filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    file_path = os.path.join(
        upload_folder,
        filename
    )

    # -----------------------------------------------------
    # ذخیره
    # -----------------------------------------------------

    file.save(file_path)

    return f"uploads/{folder_name}/{filename}"


def delete_business_image(image_path):
    """
    حذف تصویر لوگو یا بنر کسب‌وکار
    """

    if not image_path:
        return

    file_path = os.path.join(
        current_app.static_folder,
        image_path
    )

    if os.path.isfile(file_path):
        os.remove(file_path)
# =========================================================
# فعال / غیرفعال کردن دسته‌بندی
# =========================================================

@business_bp.route(
    "/<int:business_id>/categories/<int:category_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_category(business_id, category_id):

    # ---------------------------------------------------------
    # پیدا کردن کسب‌وکار متعلق به کاربر
    # ---------------------------------------------------------

    business = db.session.scalar(
        db.select(Business).where(
            Business.id == business_id,
            Business.user_id == current_user.id
        )
    )

    if business is None:

        flash(
            "کسب‌وکار موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # ---------------------------------------------------------
    # پیدا کردن دسته‌بندی متعلق به همین کسب‌وکار
    # ---------------------------------------------------------

    category = db.session.scalar(
        db.select(Category).where(
            Category.id == category_id,
            Category.business_id == business.id
        )
    )

    if category is None:

        flash(
            "دسته‌بندی موردنظر پیدا نشد.",
            "error"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )

    # ---------------------------------------------------------
    # تغییر وضعیت
    # ---------------------------------------------------------
    if not check_business_editable(business):

        flash(
            "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان تغییر وضعیت دسته‌بندی وجود ندارد.",
            "error"
        )

        return redirect(
            url_for(
                "business.categories",
                business_id=business.id
            )
        )
    category.is_active = not category.is_active

    db.session.commit()

    if category.is_active:

        flash(
            "دسته‌بندی فعال شد.",
            "success"
        )

    else:

        flash(
            "دسته‌بندی غیرفعال شد.",
            "success"
        )

    return redirect(
        url_for(
            "business.categories",
            business_id=business.id
        )
    )