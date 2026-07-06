"""
مسارات الفواتير (Invoices) - بيع وشراء
كل فاتورة بتتأكد يتولد لها قيد يومية تلقائي (شوف models/invoices.py)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
import models.invoices as invoices_model
import models.contacts as contacts_model
import models.products as products_model
import models.audit as audit_model
from utils.permissions import can_edit
from utils.pdf_export import generate_invoice_pdf
from utils.money import InvalidAmountError
from extensions import csrf

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")


# ---------- صفحات العرض (Views) ----------

@invoices_bp.route("/")
@login_required
def index():
    type_ = request.args.get("type")  # sale / purchase / None (الكل)
    invoices = invoices_model.list_invoices(type_=type_)
    return render_template("invoices.html", invoices=invoices, current_type=type_)


@invoices_bp.route("/new")
@login_required
def new():
    type_ = request.args.get("type", "sale")
    contacts = contacts_model.list_contacts(
        "client" if type_ == "sale" else "supplier"
    )
    products = products_model.list_products()
    return render_template("invoice_new.html", type=type_, contacts=contacts, products=products)


@invoices_bp.route("/<invoice_id>")
@login_required
def view(invoice_id):
    invoice = invoices_model.get_invoice(invoice_id)
    if not invoice:
        flash("الفاتورة غير موجودة", "error")
        return redirect(url_for("invoices.index"))
    return render_template("invoice_view.html", invoice=invoice)


@invoices_bp.route("/<invoice_id>/pdf")
@login_required
def download_pdf(invoice_id):
    invoice = invoices_model.get_invoice(invoice_id)
    if not invoice:
        flash("الفاتورة غير موجودة", "error")
        return redirect(url_for("invoices.index"))
    pdf_bytes = generate_invoice_pdf(invoice)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice['invoice_number']}.pdf"},
    )


# ---------- إنشاء فاتورة (Form POST) ----------

@invoices_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    type_ = request.form["type"]
    contact_id = request.form["contact_id"]
    invoice_date = request.form["invoice_date"]
    due_date = request.form.get("due_date") or None
    tax_rate = request.form.get("tax_rate") or 0
    notes = request.form.get("notes")

    product_ids = request.form.getlist("product_id[]")
    descriptions = request.form.getlist("item_description[]")
    quantities = request.form.getlist("quantity[]")
    unit_prices = request.form.getlist("unit_price[]")

    items = []
    for i in range(len(quantities)):
        if not quantities[i]:
            continue
        items.append({
            "product_id": product_ids[i] if i < len(product_ids) and product_ids[i] else None,
            "description": descriptions[i] if i < len(descriptions) else "",
            # بنمرر القيمة كـ string زي ما جاية من الفورم، والـ model هو اللي بيحوّلها
            # لـ Decimal (شوف utils/money.py) - عشان نتجنب أخطاء تقريب float
            "quantity": quantities[i],
            "unit_price": unit_prices[i],
        })

    if not items:
        flash("لازم تضيف بند واحد على الأقل في الفاتورة", "error")
        return redirect(url_for("invoices.new", type=type_))

    try:
        invoice_id = invoices_model.create_invoice(
            type_=type_,
            contact_id=contact_id,
            items=items,
            invoice_date=invoice_date,
            due_date=due_date,
            notes=notes,
            created_by=current_user.id,
            tax_rate=tax_rate,
        )
        audit_model.log_action(current_user.id, "create", "invoice", invoice_id, {"type": type_, "total": None})
        flash("تم إنشاء الفاتورة والقيد المحاسبي بنجاح", "success")
        return redirect(url_for("invoices.view", invoice_id=invoice_id))
    except InvalidAmountError as e:
        flash(str(e), "error")
        return redirect(url_for("invoices.new", type=type_))
    except Exception as e:
        flash(f"حصل خطأ أثناء إنشاء الفاتورة: {e}", "error")
        return redirect(url_for("invoices.new", type=type_))


# ---------- REST API (JSON) - لو هتربطها بفرونت React/Vue بعدين ----------

@invoices_bp.route("/api/list")
@csrf.exempt
@login_required
def api_list():
    type_ = request.args.get("type")
    invoices = invoices_model.list_invoices(type_=type_)
    return jsonify([dict(row) for row in invoices])


@invoices_bp.route("/api/<invoice_id>")
@csrf.exempt
@login_required
def api_get(invoice_id):
    invoice = invoices_model.get_invoice(invoice_id)
    if not invoice:
        return jsonify({"error": "الفاتورة غير موجودة"}), 404
    return jsonify(dict(invoice))


@invoices_bp.route("/api/create", methods=["POST"])
@csrf.exempt
@login_required
@can_edit
def api_create():
    """
    مثال body (JSON):
    {
        "type": "sale",
        "contact_id": "...",
        "invoice_date": "2026-07-06",
        "tax_rate": 14,
        "items": [
            {"product_id": "...", "description": "...", "quantity": 2, "unit_price": 100}
        ]
    }
    """
    data = request.get_json(force=True)
    try:
        invoice_id = invoices_model.create_invoice(
            type_=data["type"],
            contact_id=data["contact_id"],
            items=data["items"],
            invoice_date=data["invoice_date"],
            due_date=data.get("due_date"),
            notes=data.get("notes"),
            created_by=current_user.id,
            tax_rate=data.get("tax_rate", 0),
        )
        return jsonify({"success": True, "invoice_id": invoice_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
