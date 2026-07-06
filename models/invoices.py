"""
موديل الفواتير (Invoices)
أهم حاجة هنا: كل فاتورة بتتأكد يتولد لها قيد يومية تلقائي بالقيد المزدوج
"""
from database import fetch_all, fetch_one, get_cursor
from models.journal import create_journal_entry
from models.products import adjust_stock
from utils.money import to_decimal, quantize_money
from decimal import Decimal

# أكواد الحسابات الافتراضية (لازم تتطابق مع sql/seed_accounts.sql)
DEFAULT_ACCOUNT_CODES = {
    "receivable": "1300",   # العملاء
    "payable": "2100",      # الموردون
    "sales_revenue": "4100",  # إيرادات المبيعات
    "cogs": "5100",         # تكلفة البضاعة المباعة
    "inventory": "1400",    # المخزون
    "tax_payable": "2200",  # ضرائب مستحقة
}


def _get_account_id_by_code(code):
    row = fetch_one("select id from accounts where code = %s", (code,))
    return row["id"] if row else None


def calculate_invoice_totals(items, tax_rate=0):
    """
    دالة نقية بترجع (subtotal, tax_total, total) كـ Decimal - قابلة للاختبار
    من غير قاعدة بيانات. بنستخدم Decimal بدل float عشان نتجنب أخطاء التقريب
    (شوف utils/money.py).
    """
    subtotal = sum(
        (to_decimal(i["quantity"]) * to_decimal(i["unit_price"]) for i in items),
        Decimal("0"),
    )
    subtotal = quantize_money(subtotal)
    tax_total = quantize_money(subtotal * to_decimal(tax_rate) / Decimal("100"))
    total = quantize_money(subtotal + tax_total)
    return subtotal, tax_total, total


def create_invoice(type_, contact_id, items, invoice_date, due_date=None,
                    notes=None, created_by=None, tax_rate=0):
    """
    type_: 'sale' أو 'purchase'
    items: [{"product_id": "...", "description": "...", "quantity": 2, "unit_price": 100}, ...]
    """
    subtotal, tax_total, total = calculate_invoice_totals(items, tax_rate)

    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            insert into invoices
                (type, contact_id, invoice_date, due_date, status, subtotal, tax_total, total, notes, created_by)
            values (%s, %s, %s, %s, 'confirmed', %s, %s, %s, %s, %s)
            returning id, invoice_number
            """,
            (type_, contact_id, invoice_date, due_date, subtotal, tax_total, total, notes, created_by),
        )
        invoice = cur.fetchone()
        invoice_id = invoice["id"]

        for item in items:
            quantity = to_decimal(item["quantity"])
            unit_price = to_decimal(item["unit_price"])
            line_total = quantize_money(quantity * unit_price)
            cur.execute(
                """
                insert into invoice_items
                    (invoice_id, product_id, description, quantity, unit_price, tax_rate, total)
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    invoice_id,
                    item.get("product_id"),
                    item.get("description", ""),
                    quantity,
                    unit_price,
                    tax_rate,
                    line_total,
                ),
            )
            # تحديث المخزون: بيع = نقص، شراء = زيادة
            if item.get("product_id"):
                delta = -quantity if type_ == "sale" else quantity
                adjust_stock(item["product_id"], delta)

    # إنشاء القيد المحاسبي التلقائي
    journal_entry_id = _create_invoice_journal_entry(
        invoice_id, type_, subtotal, tax_total, total, invoice_date, contact_id
    )

    with get_cursor(commit=True) as cur:
        cur.execute(
            "update invoices set journal_entry_id = %s where id = %s",
            (journal_entry_id, invoice_id),
        )

    return invoice_id


def _create_invoice_journal_entry(invoice_id, type_, subtotal, tax_total, total, invoice_date, contact_id):
    receivable_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["receivable"])
    payable_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["payable"])
    sales_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["sales_revenue"])
    cogs_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["cogs"])
    tax_id = _get_account_id_by_code(DEFAULT_ACCOUNT_CODES["tax_payable"])

    lines = []
    if type_ == "sale":
        # مدين: العملاء (بإجمالي شامل الضريبة) | دائن: إيرادات المبيعات + ضريبة مستحقة
        lines.append({"account_id": receivable_id, "debit": total, "credit": 0,
                       "description": f"فاتورة مبيعات #{invoice_id}"})
        lines.append({"account_id": sales_id, "debit": 0, "credit": subtotal,
                       "description": f"إيراد فاتورة #{invoice_id}"})
        if tax_total:
            lines.append({"account_id": tax_id, "debit": 0, "credit": tax_total,
                           "description": "ضريبة مبيعات"})
    else:  # purchase
        # مدين: المخزون/التكلفة | دائن: الموردون
        lines.append({"account_id": cogs_id, "debit": subtotal, "credit": 0,
                       "description": f"فاتورة مشتريات #{invoice_id}"})
        if tax_total:
            lines.append({"account_id": tax_id, "debit": tax_total, "credit": 0,
                           "description": "ضريبة مشتريات"})
        lines.append({"account_id": payable_id, "debit": 0, "credit": total,
                       "description": f"مستحق للمورد - فاتورة #{invoice_id}"})

    return create_journal_entry(
        entry_date=invoice_date,
        description=f"قيد {'مبيعات' if type_=='sale' else 'مشتريات'} تلقائي - فاتورة #{invoice_id}",
        lines=lines,
        source_type="invoice",
        source_id=invoice_id,
    )


def get_invoice(invoice_id):
    invoice = fetch_one(
        """
        select i.*, c.name as contact_name,
            (i.due_date is not null and i.due_date < current_date and i.status not in ('paid','cancelled')) as is_overdue
        from invoices i
        left join contacts c on c.id = i.contact_id
        where i.id = %s
        """,
        (invoice_id,),
    )
    if not invoice:
        return None
    invoice["items"] = fetch_all(
        "select * from invoice_items where invoice_id = %s", (invoice_id,)
    )
    return invoice


def list_invoices(type_=None, limit=50, offset=0):
    query = """
        select i.*, c.name as contact_name,
            (i.due_date is not null and i.due_date < current_date and i.status not in ('paid','cancelled')) as is_overdue
        from invoices i
        left join contacts c on c.id = i.contact_id
    """
    params = []
    if type_:
        query += " where i.type = %s"
        params.append(type_)
    query += " order by i.invoice_date desc, i.invoice_number desc limit %s offset %s"
    params += [limit, offset]
    return fetch_all(query, params)
