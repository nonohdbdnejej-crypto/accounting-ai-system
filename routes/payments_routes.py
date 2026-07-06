"""
مسارات المصروفات والمقبوضات والمدفوعات (Expenses & Payments)
المصروفات هنا بتتعامل كقيد يومية مباشر على حساب مصروف + الخزينة/البنك
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import models.payments as payments_model
import models.contacts as contacts_model
import models.accounts as accounts_model
import models.audit as audit_model
from models.journal import create_journal_entry, UnbalancedEntryError
from database import fetch_one
from utils.validators import validate_positive_amount
from utils.money import InvalidAmountError
from utils.permissions import can_edit
from extensions import csrf

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


# ---------- صفحات العرض ----------

@payments_bp.route("/")
@login_required
def index():
    type_ = request.args.get("type")  # receipt / payment
    payments = payments_model.list_payments(type_=type_)
    return render_template("payments.html", payments=payments, current_type=type_)


@payments_bp.route("/new")
@login_required
def new():
    type_ = request.args.get("type", "receipt")
    contacts = contacts_model.list_contacts(
        "client" if type_ == "receipt" else "supplier"
    )
    cash_accounts = [a for a in accounts_model.list_accounts() if a["code"] in ("1100", "1200")]
    return render_template("payment_new.html", type=type_, contacts=contacts, cash_accounts=cash_accounts)


@payments_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    if not validate_positive_amount(request.form.get("amount")):
        flash("المبلغ لازم يكون رقم أكبر من صفر", "error")
        return redirect(url_for("payments.new", type=request.form.get("type")))

    try:
        payment_id = payments_model.create_payment(
            type_=request.form["type"],
            contact_id=request.form.get("contact_id") or None,
            amount=request.form["amount"],
            cash_account_id=request.form["cash_account_id"],
            payment_date=request.form["payment_date"],
            invoice_id=request.form.get("invoice_id") or None,
            method=request.form.get("method", "cash"),
            notes=request.form.get("notes"),
            created_by=current_user.id,
        )
        audit_model.log_action(current_user.id, "create", "payment", payment_id)
        flash("تم تسجيل العملية والقيد المحاسبي بنجاح", "success")
    except InvalidAmountError as e:
        flash(str(e), "error")
        return redirect(url_for("payments.new", type=request.form.get("type")))
    except Exception as e:
        flash(f"حصل خطأ: {e}", "error")
        return redirect(url_for("payments.new", type=request.form.get("type")))

    return redirect(url_for("payments.index"))


# ---------- المصروفات العامة (إيجار، رواتب، مصروفات إدارية...) ----------

@payments_bp.route("/expenses/new")
@login_required
@can_edit
def new_expense():
    expense_accounts = [
        a for a in accounts_model.list_accounts() if a["type"] == "expense"
    ]
    cash_accounts = [a for a in accounts_model.list_accounts() if a["code"] in ("1100", "1200")]
    return render_template(
        "expense_new.html", expense_accounts=expense_accounts, cash_accounts=cash_accounts
    )


@payments_bp.route("/expenses/create", methods=["POST"])
@login_required
@can_edit
def create_expense():
    """
    مصروف عادي: مدين حساب المصروف | دائن الخزينة/البنك
    """
    if not validate_positive_amount(request.form.get("amount")):
        flash("المبلغ لازم يكون رقم أكبر من صفر", "error")
        return redirect(url_for("payments.new_expense"))

    expense_account_id = request.form["expense_account_id"]
    cash_account_id = request.form["cash_account_id"]
    amount = request.form["amount"]  # هيتحول لـ Decimal جوه create_journal_entry
    expense_date = request.form["expense_date"]
    description = request.form.get("description", "مصروف")

    lines = [
        {"account_id": expense_account_id, "debit": amount, "credit": 0, "description": description},
        {"account_id": cash_account_id, "debit": 0, "credit": amount, "description": "دفع نقدي/بنكي"},
    ]

    try:
        entry_id = create_journal_entry(
            entry_date=expense_date,
            description=description,
            lines=lines,
            source_type="expense",
            created_by=current_user.id,
        )
        audit_model.log_action(current_user.id, "create", "expense", entry_id, {"amount": str(amount)})
        flash("تم تسجيل المصروف بنجاح", "success")
    except (UnbalancedEntryError, InvalidAmountError) as e:
        flash(str(e), "error")

    return redirect(url_for("payments.new_expense"))


# ---------- REST API (JSON) ----------

@payments_bp.route("/api/list")
@csrf.exempt
@login_required
def api_list():
    type_ = request.args.get("type")
    return jsonify([dict(row) for row in payments_model.list_payments(type_=type_)])


@payments_bp.route("/api/create", methods=["POST"])
@csrf.exempt
@login_required
@can_edit
def api_create():
    """
    مثال body (JSON):
    {
        "type": "receipt",
        "contact_id": "...",
        "amount": 500,
        "cash_account_id": "...",
        "payment_date": "2026-07-06",
        "method": "cash"
    }
    """
    data = request.get_json(force=True)
    try:
        payment_id = payments_model.create_payment(
            type_=data["type"],
            contact_id=data.get("contact_id"),
            amount=data["amount"],
            cash_account_id=data["cash_account_id"],
            payment_date=data["payment_date"],
            invoice_id=data.get("invoice_id"),
            method=data.get("method", "cash"),
            notes=data.get("notes"),
            created_by=current_user.id,
        )
        return jsonify({"success": True, "payment_id": payment_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@payments_bp.route("/api/expenses/create", methods=["POST"])
@csrf.exempt
@login_required
@can_edit
def api_create_expense():
    data = request.get_json(force=True)
    lines = [
        {"account_id": data["expense_account_id"], "debit": data["amount"], "credit": 0,
         "description": data.get("description", "مصروف")},
        {"account_id": data["cash_account_id"], "debit": 0, "credit": data["amount"],
         "description": "دفع نقدي/بنكي"},
    ]
    try:
        entry_id = create_journal_entry(
            entry_date=data["expense_date"],
            description=data.get("description", "مصروف"),
            lines=lines,
            source_type="expense",
            created_by=current_user.id,
        )
        return jsonify({"success": True, "journal_entry_id": entry_id}), 201
    except UnbalancedEntryError as e:
        return jsonify({"success": False, "error": str(e)}), 400
