"""مسارات المنتجات والمخزون (Products)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models.products as products_model
import models.audit as audit_model
from utils.permissions import can_edit

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
@login_required
def index():
    products = products_model.list_products()
    low_stock = products_model.get_low_stock_products()
    return render_template("products.html", products=products, low_stock=low_stock)


@products_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    product = products_model.create_product(
        name=request.form["name"],
        sku=request.form.get("sku"),
        unit=request.form.get("unit", "قطعة"),
        cost_price=request.form.get("cost_price") or 0,
        sale_price=request.form.get("sale_price") or 0,
        quantity=request.form.get("quantity") or 0,
        reorder_level=request.form.get("reorder_level") or 0,
    )
    audit_model.log_action(current_user.id, "create", "product", product["id"])
    flash("تم إضافة المنتج بنجاح", "success")
    return redirect(url_for("products.index"))


@products_bp.route("/<product_id>/edit", methods=["POST"])
@login_required
@can_edit
def edit(product_id):
    products_model.update_product(
        product_id,
        name=request.form["name"],
        sku=request.form.get("sku"),
        cost_price=request.form.get("cost_price") or 0,
        sale_price=request.form.get("sale_price") or 0,
        reorder_level=request.form.get("reorder_level") or 0,
    )
    audit_model.log_action(current_user.id, "update", "product", product_id)
    flash("تم تعديل المنتج", "success")
    return redirect(url_for("products.index"))
