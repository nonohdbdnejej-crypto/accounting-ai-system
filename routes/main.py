"""لوحة التحكم الرئيسية - ملخص عام"""
from flask import Blueprint, render_template
from flask_login import login_required
from database import fetch_one

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    stats = {}
    stats["total_receivable"] = fetch_one(
        "select coalesce(sum(balance),0) as v from account_balances where code = '1300'"
    )["v"]
    stats["total_payable"] = fetch_one(
        "select coalesce(sum(balance),0) as v from account_balances where code = '2100'"
    )["v"]
    stats["cash_balance"] = fetch_one(
        "select coalesce(sum(balance),0) as v from account_balances where code in ('1100','1200')"
    )["v"]
    stats["invoice_count"] = fetch_one("select count(*) as v from invoices")["v"]
    return render_template("dashboard.html", stats=stats)
