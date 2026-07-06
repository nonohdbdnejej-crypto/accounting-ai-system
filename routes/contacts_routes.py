"""مسارات العملاء والموردين (Contacts)"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
import models.contacts as contacts_model
import models.accounts as accounts_model
import models.audit as audit_model
from utils.validators import validate_email, validate_phone
from utils.permissions import can_edit, admin_only

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")


@contacts_bp.route("/")
@login_required
def index():
    contacts = contacts_model.list_contacts()
    return render_template("contacts.html", contacts=contacts)


@contacts_bp.route("/create", methods=["POST"])
@login_required
@can_edit
def create():
    email = request.form.get("email")
    phone = request.form.get("phone")

    if email and not validate_email(email):
        flash("البريد الإلكتروني غير صحيح", "error")
        return redirect(url_for("contacts.index"))

    if phone and not validate_phone(phone):
        flash("رقم الهاتف غير صحيح (لازم 10 أرقام على الأقل)", "error")
        return redirect(url_for("contacts.index"))

    contact = contacts_model.create_contact(
        name=request.form["name"],
        type_=request.form["type"],
        phone=phone,
        email=email,
        address=request.form.get("address"),
        tax_number=request.form.get("tax_number"),
        opening_balance=request.form.get("opening_balance") or 0,
    )
    audit_model.log_action(current_user.id, "create", "contact", contact["id"])
    flash("تم إضافة العميل/المورد بنجاح", "success")
    return redirect(url_for("contacts.index"))


@contacts_bp.route("/<contact_id>/edit", methods=["POST"])
@login_required
@can_edit
def edit(contact_id):
    contacts_model.update_contact(
        contact_id,
        name=request.form["name"],
        type=request.form["type"],
        phone=request.form.get("phone"),
        email=request.form.get("email"),
        address=request.form.get("address"),
    )
    audit_model.log_action(current_user.id, "update", "contact", contact_id)
    flash("تم تعديل البيانات", "success")
    return redirect(url_for("contacts.index"))


@contacts_bp.route("/<contact_id>/delete", methods=["POST"])
@login_required
@admin_only
def delete(contact_id):
    contacts_model.delete_contact(contact_id)
    audit_model.log_action(current_user.id, "delete", "contact", contact_id)
    flash("تم الحذف", "success")
    return redirect(url_for("contacts.index"))


@contacts_bp.route("/<contact_id>/statement")
@login_required
def statement(contact_id):
    contact = contacts_model.get_contact(contact_id)
    data = contacts_model.get_contact_statement(contact_id)
    return render_template("contact_statement.html", contact=contact, data=data)
