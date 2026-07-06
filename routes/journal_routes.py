"""مسارات القيود اليومية (Journal Entries)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models.journal as journal_model
import models.accounts as accounts_model
import models.audit as audit_model
from utils.permissions import can_edit
from utils.money import InvalidAmountError

journal_bp = Blueprint("journal", __name__, url_prefix="/journal")


@journal_bp.route("/")
@login_required
def index():
    entries = journal_model.list_journal_entries()
    return render_template("journal.html", entries=entries)


@journal_bp.route("/new")
@login_required
@can_edit
def new():
    accounts = accounts_model.list_accounts()
    return render_template("journal_new.html", accounts=accounts)


@journal_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    account_ids = request.form.getlist("account_id[]")
    debits = request.form.getlist("debit[]")
    credits = request.form.getlist("credit[]")
    descriptions = request.form.getlist("line_description[]")

    lines = []
    for i in range(len(account_ids)):
        if not account_ids[i]:
            continue
        lines.append({
            "account_id": account_ids[i],
            # بنمررهم كـ string والـ model بيحوّلهم لـ Decimal بدقة (utils/money.py)
            "debit": debits[i] or 0,
            "credit": credits[i] or 0,
            "description": descriptions[i] if i < len(descriptions) else "",
        })

    try:
        entry_id = journal_model.create_journal_entry(
            entry_date=request.form["entry_date"],
            description=request.form.get("description"),
            lines=lines,
            reference=request.form.get("reference"),
            created_by=current_user.id,
        )
        audit_model.log_action(current_user.id, "create", "journal_entry", entry_id)
        flash("تم إنشاء القيد بنجاح", "success")
    except (journal_model.UnbalancedEntryError, InvalidAmountError) as e:
        flash(str(e), "error")
        return redirect(url_for("journal.new"))

    return redirect(url_for("journal.index"))


@journal_bp.route("/<entry_id>")
@login_required
def view(entry_id):
    entry = journal_model.get_journal_entry(entry_id)
    if not entry:
        flash("القيد غير موجود", "error")
        return redirect(url_for("journal.index"))
    return render_template("journal_view.html", entry=entry)


@journal_bp.route("/<entry_id>/reverse", methods=["POST"])
@login_required
@can_edit
def reverse(entry_id):
    """
    عكس القيد بدل حذفه نهائيًا: بينشئ قيد جديد بمدين/دائن معكوسين
    عشان يلغي الأثر المالي مع الحفاظ على القيد الأصلي في السجل (audit trail).
    """
    reason = request.form.get("reason")
    try:
        reversal_id = journal_model.reverse_journal_entry(
            entry_id, reason=reason, created_by=current_user.id
        )
        audit_model.log_action(
            current_user.id, "reverse", "journal_entry", entry_id,
            {"reversal_entry_id": reversal_id, "reason": reason},
        )
        flash("تم عكس القيد بنجاح - القيد الأصلي محفوظ في السجل مع قيد عكسي جديد", "success")
        return redirect(url_for("journal.view", entry_id=reversal_id))
    except journal_model.CannotReverseError as e:
        flash(str(e), "error")
        return redirect(url_for("journal.view", entry_id=entry_id))
