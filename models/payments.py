"""موديل المقبوضات والمدفوعات (Payments) - مرتبط بقيد يومية تلقائي"""
from database import fetch_all, fetch_one, get_cursor
from models.journal import create_journal_entry
from utils.money import to_decimal

DEFAULT_ACCOUNT_CODES = {
    "receivable": "1300",
    "payable": "2100",
}


def _get_account_id_by_code(code):
    row = fetch_one("select id from accounts where code = %s", (code,))
    return row["id"] if row else None


def create_payment(type_, contact_id, amount, cash_account_id, payment_date,
                    invoice_id=None, method="cash", notes=None, created_by=None):
    """
    type_: 'receipt' (تحصيل من عميل) أو 'payment' (سداد لمورد)
    cash_account_id: حساب الخزينة أو البنك المستخدم
    """
    amount = to_decimal(amount)
    receivable_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["receivable"])
    payable_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["payable"])

    if type_ == "receipt":
        # مدين: الخزينة/البنك | دائن: العملاء
        lines = [
            {"account_id": cash_account_id, "debit": amount, "credit": 0,
             "description": "تحصيل من عميل"},
            {"account_id": receivable_id, "debit": 0, "credit": amount,
             "description": "سداد رصيد عميل"},
        ]
    else:
        # مدين: الموردون | دائن: الخزينة/البنك
        lines = [
            {"account_id": payable_id, "debit": amount, "credit": 0,
             "description": "سداد لمورد"},
            {"account_id": cash_account_id, "debit": 0, "credit": amount,
             "description": "دفع من الخزينة/البنك"},
        ]

    journal_entry_id = create_journal_entry(
        entry_date=payment_date,
        description=f"قيد {'تحصيل' if type_=='receipt' else 'سداد'} تلقائي",
        lines=lines,
        source_type="payment",
    )

    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            insert into payments
                (type, contact_id, invoice_id, amount, payment_date, method,
                 cash_account_id, journal_entry_id, notes, created_by)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning id
            """,
            (type_, contact_id, invoice_id, amount, payment_date, method,
             cash_account_id, journal_entry_id, notes, created_by),
        )
        payment = cur.fetchone()

        # لو مرتبط بفاتورة، حدّث حالتها لمدفوعة
        if invoice_id:
            cur.execute(
                "update invoices set status = 'paid' where id = %s", (invoice_id,)
            )

        return payment["id"]


def list_payments(type_=None, limit=50, offset=0):
    query = """
        select p.*, c.name as contact_name
        from payments p
        left join contacts c on c.id = p.contact_id
    """
    params = []
    if type_:
        query += " where p.type = %s"
        params.append(type_)
    query += " order by p.payment_date desc limit %s offset %s"
    params += [limit, offset]
    return fetch_all(query, params)
