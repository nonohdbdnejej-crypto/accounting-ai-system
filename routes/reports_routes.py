"""مسارات التقارير المالية (Reports)"""
from decimal import Decimal
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from database import fetch_all

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/trial-balance")
@login_required
def trial_balance():
    rows = fetch_all("select * from trial_balance")
    total_debit = sum((Decimal(r["total_debit"]) for r in rows), Decimal("0"))
    total_credit = sum((Decimal(r["total_credit"]) for r in rows), Decimal("0"))
    return render_template(
        "reports_trial_balance.html", rows=rows, total_debit=total_debit, total_credit=total_credit
    )


@reports_bp.route("/income-statement")
@login_required
def income_statement():
    revenues = fetch_all("select * from account_balances where type = 'revenue' order by code")
    expenses = fetch_all("select * from account_balances where type = 'expense' order by code")
    total_revenue = sum((Decimal(r["balance"]) for r in revenues), Decimal("0"))
    total_expense = sum((Decimal(r["balance"]) for r in expenses), Decimal("0"))
    net_profit = total_revenue - total_expense
    return render_template(
        "reports_income_statement.html",
        revenues=revenues, expenses=expenses,
        total_revenue=total_revenue, total_expense=total_expense, net_profit=net_profit,
    )


@reports_bp.route("/balance-sheet")
@login_required
def balance_sheet():
    assets = fetch_all("select * from account_balances where type = 'asset' order by code")
    liabilities = fetch_all("select * from account_balances where type = 'liability' order by code")
    equity = fetch_all("select * from account_balances where type = 'equity' order by code")
    total_assets = sum((Decimal(r["balance"]) for r in assets), Decimal("0"))
    total_liabilities = sum((Decimal(r["balance"]) for r in liabilities), Decimal("0"))
    total_equity = sum((Decimal(r["balance"]) for r in equity), Decimal("0"))
    return render_template(
        "reports_balance_sheet.html",
        assets=assets, liabilities=liabilities, equity=equity,
        total_assets=total_assets, total_liabilities=total_liabilities, total_equity=total_equity,
    )


# ---------- API JSON لعمل رسوم بيانية في الفرونت ----------

@reports_bp.route("/api/trial-balance")
@login_required
def api_trial_balance():
    return jsonify([dict(r) for r in fetch_all("select * from trial_balance")])


@reports_bp.route("/api/income-statement")
@login_required
def api_income_statement():
    revenues = fetch_all("select * from account_balances where type = 'revenue'")
    expenses = fetch_all("select * from account_balances where type = 'expense'")
    return jsonify({
        "revenues": [dict(r) for r in revenues],
        "expenses": [dict(r) for r in expenses],
    })


@reports_bp.route("/api/monthly-summary")
@login_required
def api_monthly_summary():
    """ملخص الإيرادات/المصروفات شهرياً لآخر 6 شهور (لرسم بياني)"""
    rows = fetch_all(
        """
        select
            to_char(je.entry_date, 'YYYY-MM') as month,
            sum(case when a.type = 'revenue' then l.credit - l.debit else 0 end) as revenue,
            sum(case when a.type = 'expense' then l.debit - l.credit else 0 end) as expense
        from journal_entry_lines l
        join journal_entries je on je.id = l.entry_id
        join accounts a on a.id = l.account_id
        where je.entry_date >= (current_date - interval '6 months')
        group by month
        order by month
        """
    )
    return jsonify([dict(r) for r in rows])


@reports_bp.route("/api/invoice-status-breakdown")
@login_required
def api_invoice_status_breakdown():
    """توزيع الفواتير حسب الحالة (لرسم بياني دائري)"""
    rows = fetch_all(
        "select status, count(*) as count from invoices group by status"
    )
    return jsonify([dict(r) for r in rows])
