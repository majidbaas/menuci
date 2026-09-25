from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Category


category_bp = Blueprint(
    "category",
    __name__,
    url_prefix="/dashboard/categories"
)


@category_bp.route("/")
@login_required
def index():
    business = current_user.business

    if not business:
        flash("ابتدا اطلاعات کسب‌وکار خود را تکمیل کنید.", "warning")
        return redirect(url_for("business.edit"))

    categories = (
        Category.query
        .filter_by(business_id=business.id)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )

    return render_template(
        "dashboard/categories.html",
        business=business,
        categories=categories
    )


@category_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    business = current_user.business

    if not business:
        flash("ابتدا اطلاعات کسب‌وکار خود را تکمیل کنید.", "warning")
        return redirect(url_for("business.edit"))

    if request.method == "POST":

        # ---------------------------------------------------------
        # بررسی امکان تغییر
        # ---------------------------------------------------------

        from app.routes.business import check_business_editable

        if not check_business_editable(business):
            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان ایجاد دسته‌بندی وجود ندارد.",
                "error"
            )
            return redirect(url_for("category.index"))

        # ---------------------------------------------------------
        # اطلاعات فرم
        # ---------------------------------------------------------

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("نام دسته‌بندی الزامی است.", "danger")
            return render_template(
                "dashboard/category_form.html",
                category=None
            )

        category = Category(
            business_id=business.id,
            name=name,
            description=description or None
        )

        db.session.add(category)
        db.session.commit()

        flash("دسته‌بندی با موفقیت ایجاد شد.", "success")
        return redirect(url_for("category.index"))

    return render_template(
        "dashboard/category_form.html",
        category=None
    )

@category_bp.route("/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def edit(category_id):
    business = current_user.business

    if not business:
        flash("ابتدا اطلاعات کسب‌وکار خود را تکمیل کنید.", "warning")
        return redirect(url_for("business.edit"))

    category = Category.query.filter_by(
        id=category_id,
        business_id=business.id
    ).first_or_404()

    if request.method == "POST":

        # ---------------------------------------------------------
        # بررسی امکان تغییر
        # ---------------------------------------------------------

        from app.routes.business import check_business_editable

        if not check_business_editable(business):
            flash(
                "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان ویرایش دسته‌بندی وجود ندارد.",
                "error"
            )
            return redirect(url_for("category.index"))

        # ---------------------------------------------------------
        # اطلاعات فرم
        # ---------------------------------------------------------

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("نام دسته‌بندی الزامی است.", "danger")
            return render_template(
                "dashboard/category_form.html",
                category=category
            )

        category.name = name
        category.description = description or None

        db.session.commit()

        flash("دسته‌بندی با موفقیت ویرایش شد.", "success")
        return redirect(url_for("category.index"))

    return render_template(
        "dashboard/category_form.html",
        category=category
    )
@category_bp.route("/<int:category_id>/delete", methods=["POST"])
@login_required
def delete(category_id):
    business = current_user.business

    if not business:
        flash("ابتدا اطلاعات کسب‌وکار خود را تکمیل کنید.", "warning")
        return redirect(url_for("business.edit"))

    category = Category.query.filter_by(
        id=category_id,
        business_id=business.id
    ).first_or_404()

    # ---------------------------------------------------------
    # بررسی امکان تغییر
    # ---------------------------------------------------------

    from app.routes.business import check_business_editable

    if not check_business_editable(business):
        flash(
            "اشتراک شما منقضی شده است. در دوره مهلت تمدید، امکان حذف دسته‌بندی وجود ندارد.",
            "error"
        )
        return redirect(url_for("category.index"))

    # ---------------------------------------------------------
    # حذف
    # ---------------------------------------------------------

    db.session.delete(category)
    db.session.commit()

    flash("دسته‌بندی با موفقیت حذف شد.", "success")
    return redirect(url_for("category.index"))