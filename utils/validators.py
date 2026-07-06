"""أدوات التحقق من صحة البيانات (Validators)"""
import re
from utils.money import to_decimal, InvalidAmountError


def validate_email(email):
    """التحقق من صيغة البريد الإلكتروني"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """التحقق من رقم الهاتف (10 أرقام على الأقل بعد إزالة الرموز)"""
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10


def validate_positive_amount(value):
    """التحقق من إن القيمة رقم وموجبة (للمبالغ المالية) - باستخدام Decimal"""
    try:
        return to_decimal(value) > 0
    except InvalidAmountError:
        return False


def validate_currency(currency):
    """التحقق من كود العملة"""
    valid_currencies = ['EGP', 'SAR', 'AED', 'USD', 'EUR', 'GBP']
    return bool(currency) and currency.upper() in valid_currencies
