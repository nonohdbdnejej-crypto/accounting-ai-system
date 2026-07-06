"""
أدوات التعامل مع المبالغ المالية (Decimal بدل float)

ليه مش float؟
لأن float بيمثّل الأرقام العشرية بالنظام الثنائي، فمبالغ زي 0.1 أو 33.33
بتتخزن بقيمة تقريبية مش مظبوطة 100%. في نظام محاسبي، الفروق الصغيرة دي
بتتراكم عبر آلاف القيود وممكن تخلي ميزان المراجعة "يقرب" يتوازن من غير
ما يكون متوازن فعليًا. الحل: Decimal في كل حسابات الفلوس من أول ما
القيمة بتدخل النظام (من الفورم أو الـ API) لحد ما بتتخزن في قاعدة البيانات.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")


class InvalidAmountError(Exception):
    """القيمة المدخلة مش رقم صحيح يمكن التعامل معه كمبلغ مالي"""
    pass


def to_decimal(value):
    """
    يحوّل أي قيمة (None / str / int / float / Decimal) لـ Decimal بأمان.

    - None أو "" -> Decimal("0")
    - string ("100", "99.99") -> تحويل مباشر ودقيق 100%
    - float -> بيتحول عن طريق str() الأول عشان نتجنب أخطاء تمثيل الفلوت
      (مثلاً Decimal(0.1) لوحدها بيديك رقم طويل مش 0.1 بالظبط،
       لكن Decimal(str(0.1)) بيديك 0.1 بالظبط)
    """
    if value is None or value == "":
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        if isinstance(value, float):
            return Decimal(str(value))
        return Decimal(str(value)) if isinstance(value, str) else Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidAmountError(f"القيمة '{value}' مش رقم صحيح")


def quantize_money(value):
    """تقريب لأقرب قرش (خانتين عشريتين) - التقريب المحاسبي القياسي (Half-Up)"""
    return to_decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
