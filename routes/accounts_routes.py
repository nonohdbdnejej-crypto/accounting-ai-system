"""مسارات دليل الحسابات (Chart of Accounts)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models.accounts as accounts_model
import models.audit as audit_model
from utils.permissions import can_edit, admin_only

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")


@accounts_bp.route("/")
@login_required
def index():
    accounts = accounts_model.list_accounts()
    return render_template("accounts.html", accounts=accounts)


@accounts_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    account = accounts_model.create_account(
        code=request.form["code"],
        name=request.form["name"],
        type_=request.form["type"],
        parent_id=request.form.get("parent_id") or None,
    )
    audit_model.log_action(
        current_user.id, "create", "account", account["id"],
        {"code": request.form["code"], "name": request.form["name"]},
    )
    flash("تم إنشاء الحساب بنجاح", "success")
    return redirect(url_for("accounts.index"))


@accounts_bp.route("/<account_id>/edit", methods=["POST"])
@login_required
@can_edit
def edit(account_id):
    accounts_model.update_account(
        account_id,
        code=request.form["code"],
        name=request.form["name"],
        type_=request.form["type"],
        parent_id=request.form.get("parent_id") or None,
    )
    audit_model.log_action(current_user.id, "update", "account", account_id)
    flash("تم تعديل الحساب", "success")
    return redirect(url_for("accounts.index"))


@accounts_bp.route("/<account_id>/deactivate", methods=["POST"])
@login_required
@admin_only
def deactivate(account_id):
    accounts_model.deactivate_account(account_id)
    audit_model.log_action(current_user.id, "delete", "account", account_id)
    flash("تم إلغاء تفعيل الحساب", "success")
    return redirect(url_for("accounts.index"))
