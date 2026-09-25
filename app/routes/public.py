import colorsys

from flask import Blueprint, render_template

from app.extensions import db
from app.models.business import Business
from app.models.category import Category
from app.models.product import Product

from app.services.themes import get_theme
from app.services.subscription import get_subscription_state

from app.business_types import (
    get_business_type,
    get_business_type_choices
)


public_bp = Blueprint(
    "public",
    __name__
)


# =========================================================
# Build Business Theme
# =========================================================

def build_business_theme(business):

    # تم پیش‌فرض بر اساس نوع کسب‌وکار
    theme = get_theme(
        business.business_type
    )

    # اگر رنگ اختصاصی انتخاب نشده،
    # همان تم اصلی را برگردان
    if not business.primary_color:

        return {
            "primary": theme["primary"],
            "primary_dark": theme["primary"],
            "primary_light": theme["primary_light"],
            "background": theme["background"],
            "text": theme["text"],
            "muted": theme["muted"],
        }

    hex_color = business.primary_color.lstrip("#")

    # بررسی صحت رنگ
    if len(hex_color) != 6:

        return {
            "primary": theme["primary"],
            "primary_dark": theme["primary"],
            "primary_light": theme["primary_light"],
            "background": theme["background"],
            "text": theme["text"],
            "muted": theme["muted"],
        }

    try:

        r = int(
            hex_color[0:2],
            16
        ) / 255

        g = int(
            hex_color[2:4],
            16
        ) / 255

        b = int(
            hex_color[4:6],
            16
        ) / 255

    except ValueError:

        return {
            "primary": theme["primary"],
            "primary_dark": theme["primary"],
            "primary_light": theme["primary_light"],
            "background": theme["background"],
            "text": theme["text"],
            "muted": theme["muted"],
        }

    # تبدیل RGB به HLS
    h, l, s = colorsys.rgb_to_hls(
        r,
        g,
        b
    )

    # =====================================================
    # Primary
    # =====================================================

    primary = "#" + hex_color.upper()

    # =====================================================
    # Primary Dark
    # =====================================================

    dark_l = max(
        0.0,
        l * 0.72
    )

    dark_r, dark_g, dark_b = colorsys.hls_to_rgb(
        h,
        dark_l,
        s
    )

    primary_dark = "#{:02X}{:02X}{:02X}".format(
        round(dark_r * 255),
        round(dark_g * 255),
        round(dark_b * 255)
    )

    # =====================================================
    # Primary Light
    # =====================================================

    light_l = min(
        0.96,
        l + (0.90 - l) * 0.75
    )

    light_r, light_g, light_b = colorsys.hls_to_rgb(
        h,
        light_l,
        max(
            0.20,
            s * 0.65
        )
    )

    primary_light = "#{:02X}{:02X}{:02X}".format(
        round(light_r * 255),
        round(light_g * 255),
        round(light_b * 255)
    )

    # =====================================================
    # Final Theme
    # =====================================================

    return {
        "primary": primary,
        "primary_dark": primary_dark,
        "primary_light": primary_light,
        "background": theme["background"],
        "text": theme["text"],
        "muted": theme["muted"],
    }


# =========================================================
# Check Business Subscription Status
# =========================================================

def check_business_subscription(business):
    """
    وضعیت اشتراک صاحب کسب‌وکار را بررسی می‌کند.

    در دوره ۱۰ روزه:
        کسب‌وکار همچنان فعال می‌ماند.

    بعد از پایان دوره ۱۰ روزه:
        کسب‌وکار آرشیو می‌شود و دیگر عمومی نیست.
    """

    subscription_state = get_subscription_state(
        business.user_id
    )

    state = subscription_state["state"]

    # -----------------------------------------------------
    # دوره فعال یا دوره ۱۰ روزه
    # -----------------------------------------------------

    if state in ("active", "grace_period"):

        return True

    # -----------------------------------------------------
    # پایان دوره ۱۰ روزه
    # -----------------------------------------------------

    if state == "archived":

        if business.is_active:

            business.is_active = False

            db.session.commit()

        return False

    # -----------------------------------------------------
    # بدون اشتراک
    # -----------------------------------------------------

    return False


# =========================================================
# Public Home
# =========================================================

@public_bp.route("/")
def home():

    businesses = db.session.scalars(
        db.select(Business)
        .where(
            Business.is_active == True
        )
        .order_by(
            Business.created_at.desc()
        )
    ).all()

    businesses_with_type = []

    for business in businesses:

        # اگر دوره ۱۰ روزه تمام شده باشد،
        # کسب‌وکار همین‌جا آرشیو می‌شود.
        if not check_business_subscription(business):

            continue

        businesses_with_type.append(
            {
                "business": business,
                "type": get_business_type(
                    business.business_type
                )
            }
        )

    business_type_choices = get_business_type_choices()

    return render_template(
        "public/home.html",
        businesses=businesses_with_type,
        business_type_choices=business_type_choices
    )


# =========================================================
# Public Business Page
# =========================================================
@public_bp.route("/<slug>")
def business_page(slug):

     
    # =====================================================
    # پیدا کردن کسب‌وکار
    # =====================================================

    business = db.session.scalar(
        db.select(Business)
        .where(
            Business.slug == slug
        )
    )

    # -----------------------------------------------------
    # کسب‌وکار واقعاً وجود ندارد
    # -----------------------------------------------------

    if business is None:

        return render_template(
            "public/not_found.html"
        ), 404
    # -----------------------------------------------------
    # بررسی وضعیت اشتراک
    # -----------------------------------------------------

    if not check_business_subscription(business):

        return render_template(
            "public/archived.html",
            business=business
        )

    # -----------------------------------------------------
    # کسب‌وکار باید فعال باشد
    # -----------------------------------------------------

    if not business.is_active:

        return render_template(
            "public/archived.html",
            business=business
        )

    # =====================================================
    # ساخت تم نهایی کسب‌وکار
    # =====================================================

    theme = build_business_theme(
        business
    )

    # =====================================================
    # Categories
    # =====================================================

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

    # =====================================================
    # Products
    # =====================================================

    products = db.session.scalars(
        db.select(Product)
        .where(
            Product.business_id == business.id,
            Product.is_active == True,
            Product.is_available == True
        )
        .order_by(
            Product.sort_order,
            Product.id
        )
    ).all()

    # =====================================================
    # Products By Category
    # =====================================================

    products_by_category = {}

    for product in products:

        if product.category_id not in products_by_category:

            products_by_category[
                product.category_id
            ] = []

        products_by_category[
            product.category_id
        ].append(product)

    # =====================================================
    # Render
    # =====================================================

    return render_template(
        "public/business.html",

        business=business,

        categories=categories,

        products_by_category=products_by_category,

        theme=theme,

        business_config=get_business_type(
            business.business_type
        )
    )
    
    
# =========================================================
# Guide
# =========================================================

@public_bp.route("/guide")
def guide():

    return render_template(
        "guide/index.html"
    )
     
