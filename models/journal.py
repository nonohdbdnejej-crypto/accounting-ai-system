"""
موديل القيود اليومية (Journal Entries)
القاعدة الذهبية: مجموع المدين لازم يساوي مجموع الدائن في كل قيد

ملحوظة مهمة: كل الحسابات هنا بتستخدم Decimal (مش float) عشان نتجنب
أخطاء التقريب الثنائي اللي ممكن تخلي قيد "يقرب" يتوازن من غير ما يكون
متوازن فعليًا. شوف utils/money.py لتفاصيل أكتر.
"""
from database import fetch_all, fetch_one, execute, get_cursor
from utils.money import to_decimal, quantize_money, InvalidAmountError
from decimal import Decimal


class UnbalancedEntryError(Exception):
    """لما القيد مش متوازن (مدين != دائن)"""
    pass


def calculate_balance(lines):
    """
    دالة نقية (pure function) بترجع (total_debit, total_credit, is_balanced)
    من غير أي اتصال بقاعدة البيانات - عشان تبقى قابلة للاختبار بسهولة.
    بترجع Decimal مقرّبة لخانتين عشريتين.
    """
    total_debit = sum((to_decimal(l.get("debit", 0)) for l in lines), Decimal("0"))
    total_credit = sum((to_decimal(l.get("credit", 0)) for l in lines), Decimal("0"))
    total_debit = quantize_money(total_debit)
    total_credit = quantize_money(total_credit)
    is_balanced = total_debit == total_credit
    return total_debit, total_credit, is_balanced


def validate_lines(lines):
    """
    بتتأكد إن القيد سليم: متوازن، مش فاضي، ومفيش سطر فيه صفر في الاتنين.
    بترمي UnbalancedEntryError لو في مشكلة، وإلا بترجع من غير حاجة.
    """
    if not lines:
        raise UnbalancedEntryError("لازم يكون فيه سطر واحد على الأقل في القيد")

    total_debit, total_credit, is_balanced = calculate_balance(lines)

    if not is_balanced:
        raise UnbalancedEntryError(
            f"القيد غير متوازن: مدين {total_debit} != دائن {total_credit}"
        )

    if total_debit == 0:
        raise UnbalancedEntryError("لا يمكن إنشاء قيد بقيمة صفر")

    for line in lines:
        debit = to_decimal(line.get("debit", 0))
        credit = to_decimal(line.get("credit", 0))
        if debit < 0 or credit < 0:
            raise UnbalancedEntryError("لا يمكن أن تكون قيمة مدين أو دائن سالبة")
        if debit > 0 and credit > 0:
            raise UnbalancedEntryError("لا يمكن أن يكون نفس السطر مدين ودائن في نفس الوقت")


def create_journal_entry(entry_date, description, lines, reference=None,
                          created_by=None, source_type="manual", source_id=None):
    """
    ينشئ قيد يومية جديد مع بنوده.

    lines: لسته من dict كل واحد فيهم:
        {"account_id": "...", "debit": 100, "credit": 0, "description": "..."}

    بيرفض القيد لو مش متوازن (مجموع المدين != مجموع الدائن)
    """
    validate_lines(lines)

    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            insert into journal_entries
                (entry_date, description, reference, source_type, source_id, created_by)
            values (%s, %s, %s, %s, %s, %s)
            returning id, entry_number
            """,
            (entry_date, description, reference, source_type, source_id, created_by),
        )
        entry = cur.fetchone()
        entry_id = entry["id"]

        for i, line in enumerate(lines):
            cur.execute(
                """
                insert into journal_entry_lines
                    (entry_id, account_id, debit, credit, description, line_order)
                values (%s, %s, %s, %s, %s, %s)
                """,
                (
                    entry_id,
                    line["account_id"],
                    to_decimal(line.get("debit", 0)),
                    to_decimal(line.get("credit", 0)),
                    line.get("description", ""),
                    i,
                ),
            )
        return entry_id


def get_journal_entry(entry_id):
    """يرجع القيد وبنوده مع أسماء الحسابات"""
    header = fetch_one(
        "select * from journal_entries where id = %s", (entry_id,)
    )
    if not header:
        return None
    lines = fetch_all(
        """
        select l.*, a.code as account_code, a.name as account_name
        from journal_entry_lines l
        join accounts a on a.id = l.account_id
        where l.entry_id = %s
        order by l.line_order
        """,
        (entry_id,),
    )
    header["lines"] = lines
    return header


def list_journal_entries(limit=50, offset=0):
    return fetch_all(
        """
        select je.*,
            (select sum(debit) from journal_entry_lines where entry_id = je.id) as total
        from journal_entries je
        order by je.entry_date desc, je.entry_number desc
        limit %s offset %s
        """,
        (limit, offset),
    )


class CannotReverseError(Exception):
    """القيد اتعكس قبل كده، أو مش موجود، أو محاولة عكس قيد عكسي"""
    pass


def reverse_lines(lines):
    """
    دالة نقية بترجع نسخة معكوسة من بنود القيد (مدين <-> دائن).
    ده أساس آلية "عكس القيد" - قابلة للاختبار من غير قاعدة بيانات.
    """
    result = []
    for l in lines:
        original_desc = (l.get("description") or "").strip()
        result.append({
            "account_id": l["account_id"],
            "debit": to_decimal(l.get("credit", 0)),
            "credit": to_decimal(l.get("debit", 0)),
            "description": f"عكس: {original_desc}" if original_desc else "قيد عكسي",
        })
    return result


def reverse_journal_entry(entry_id, reason=None, created_by=None):
    """
    بدل الحذف النهائي (اللي بيمسح الأثر المحاسبي)، النظام بيعمل "قيد عكسي":
    قيد جديد بنفس القيم بس مدين/دائن معكوسين، بيلغي أثر القيد الأصلي في
    ميزان المراجعة من غير ما يمسح تاريخه. ده أساسي للـ audit trail ولأي
    نظام محاسبي حقيقي (زي ما بيحصل في SAP / QuickBooks / Odoo).

    بيرفض عكس قيد اتعكس قبل كده، أو عكس القيد العكسي نفسه.
    """
    entry = get_journal_entry(entry_id)
    if not entry:
        raise CannotReverseError("القيد غير موجود")

    if entry.get("is_reversed"):
        raise CannotReverseError("القيد ده اتعكس قبل كده")

    if entry.get("source_type") == "reversal":
        raise CannotReverseError("مينفعش تعكس قيد عكسي أصلًا - ده هيرجع الوضع زي ما كان")

    new_lines = reverse_lines(entry["lines"])
    description = f"عكس القيد رقم {entry['entry_number']}"
    if reason:
        description += f" - السبب: {reason}"

    reversal_id = create_journal_entry(
        entry_date=entry_date_today_or_original(entry),
        description=description,
        lines=new_lines,
        reference=entry.get("reference"),
        created_by=created_by,
        source_type="reversal",
        source_id=entry_id,
    )

    execute(
        "update journal_entries set is_reversed = true, reversed_by_entry_id = %s where id = %s",
        (reversal_id, entry_id),
    )

    return reversal_id


def entry_date_today_or_original(entry):
    """قيد العكس بياخد نفس تاريخ القيد الأصلي (أبسط وأوضح للمحاسب عند المراجعة)"""
    return entry["entry_date"]


def delete_journal_entry(entry_id):
    """
    ملحوظة: الحذف النهائي للقيود المُرحّلة (posted) ممنوع دلوقتي عمدًا.
    أي قيد اتسجل هو جزء من التاريخ المالي، وحذفه بيكسر الـ audit trail
    ومبدأ إن كل عملية مالية لازم يكون ليها أثر واضح. استخدم reverse_journal_entry
    بدلًا من كده - بيعمل قيد عكسي بيلغي الأثر المالي مع الحفاظ على السجل.
    """
    raise CannotReverseError(
        "الحذف النهائي للقيود ممنوع (عشان الحفاظ على الأثر المحاسبي). "
        "استخدم خاصية 'عكس القيد' بدلًا من كده."
    )
