from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Product, Business, Category


product_bp = Blueprint(
    "product",
    __name__,
    url_prefix="/dashboard/products"
)


@product_bp.route("/")
@login_required
def index():

    business = Business.query.filter_by(
        user_id=current_user.id
    ).first()

    if not business:
        return "برای این کاربر هنوز کسب‌وکاری ثبت نشده است."

    return render_template(
        "dashboard/products.html",
        business=business
    )

@product_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():

    business = Business.query.filter_by(
        user_id=current_user.id
    ).first()

    if not business:
        flash("ابتدا اطلاعات کسب‌وکار خود را ثبت کنید.", "warning")
        return redirect(url_for("business.create"))

    categories = Category.query.filter_by(
        business_id=business.id,
        is_active=True
    ).order_by(
        Category.sort_order.asc()
    ).all()

    if request.method == "POST":

        # ---------------------------------------------------------
        # بررسی امکان تغییر
        # ---------------------------------------------------------

        from app.routes.business import check_business_editable

        if not check_business_editable(business):
            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان ایجاد محصول وجود ندارد.",
                "error"
            )
            return redirect(url_for("product.index"))

        # ---------------------------------------------------------
        # اطلاعات فرم
        # ---------------------------------------------------------

        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip()
        description = request.form.get("description", "").strip()

        price = request.form.get("price", "0").strip()
        category_id = request.form.get("category_id")
        sort_order = request.form.get("sort_order", "0").strip()

        if not name:
            flash("نام محصول الزامی است.", "danger")
            return render_template(
                "dashboard/product_form.html",
                business=business,
                categories=categories
            )

        try:
            price = float(price or 0)
        except ValueError:
            flash("قیمت وارد شده معتبر نیست.", "danger")
            return render_template(
                "dashboard/product_form.html",
                business=business,
                categories=categories
            )

        try:
            sort_order = int(sort_order or 0)
        except ValueError:
            sort_order = 0

        product = Product(
            business_id=business.id,
            category_id=int(category_id) if category_id else None,
            name=name,
            slug=slug or name,
            description=description or None,
            price=price,
            is_available=True,
            is_active=True,
            sort_order=sort_order
        )

        db.session.add(product)
        db.session.commit()

        flash("محصول با موفقیت اضافه شد.", "success")

        return redirect(
            url_for("product.index")
        )

    return render_template(
        "dashboard/product_form.html",
        business=business,
        categories=categories
    )