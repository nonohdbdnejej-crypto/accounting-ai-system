"""
اختبارات منطق القيد المزدوج (Double-Entry Validation)
دي أهم اختبارات في المشروع كله - لو دي فشلت يبقى في مشكلة خطيرة في المحاسبة
"""
import sys
import os
import pytest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.journal import (
    calculate_balance, validate_lines, UnbalancedEntryError,
    reverse_lines, reverse_journal_entry, CannotReverseError,
)


class TestCalculateBalance:
    def test_balanced_entry(self):
        lines = [
            {"debit": 100, "credit": 0},
            {"debit": 0, "credit": 100},
        ]
        total_debit, total_credit, is_balanced = calculate_balance(lines)
        assert total_debit == Decimal("100.00")
        assert total_credit == Decimal("100.00")
        assert is_balanced is True

    def test_unbalanced_entry(self):
        lines = [
            {"debit": 100, "credit": 0},
            {"debit": 0, "credit": 50},
        ]
        total_debit, total_credit, is_balanced = calculate_balance(lines)
        assert is_balanced is False

    def test_multi_line_balanced_entry(self):
        # فاتورة فيها ضريبة: مدين واحد وسطرين دائن
        lines = [
            {"debit": 114, "credit": 0},
            {"debit": 0, "credit": 100},
            {"debit": 0, "credit": 14},
        ]
        total_debit, total_credit, is_balanced = calculate_balance(lines)
        assert total_debit == Decimal("114.00")
        assert total_credit == Decimal("114.00")
        assert is_balanced is True

    def test_floating_point_rounding(self):
        # مشكلة شائعة: 0.1 + 0.2 != 0.3 بالنظام الثنائي (float)
        # باستخدام Decimal (عن طريق to_decimal اللي بتحوّل float عبر str() أول)
        # المفروض يتوازن بالظبط من غير ما نعتمد على round() تقريبي
        lines = [
            {"debit": 0.1, "credit": 0},
            {"debit": 0.2, "credit": 0},
            {"debit": 0, "credit": 0.3},
        ]
        _, _, is_balanced = calculate_balance(lines)
        assert is_balanced is True

    def test_string_amounts_from_form(self):
        # القيم الجاية من فورم HTML بتبقى strings - لازم تتوازن بالظبط
        lines = [
            {"debit": "33.33", "credit": 0},
            {"debit": "33.33", "credit": 0},
            {"debit": "33.34", "credit": 0},
            {"debit": 0, "credit": "100.00"},
        ]
        _, _, is_balanced = calculate_balance(lines)
        assert is_balanced is True


class TestValidateLines:
    def test_valid_entry_passes(self):
        lines = [
            {"account_id": "a1", "debit": 100, "credit": 0},
            {"account_id": "a2", "debit": 0, "credit": 100},
        ]
        validate_lines(lines)  # ما ينفعش يرمي استثناء

    def test_empty_lines_raises(self):
        with pytest.raises(UnbalancedEntryError):
            validate_lines([])

    def test_unbalanced_raises(self):
        lines = [
            {"account_id": "a1", "debit": 100, "credit": 0},
            {"account_id": "a2", "debit": 0, "credit": 50},
        ]
        with pytest.raises(UnbalancedEntryError):
            validate_lines(lines)

    def test_zero_amount_entry_raises(self):
        lines = [
            {"account_id": "a1", "debit": 0, "credit": 0},
            {"account_id": "a2", "debit": 0, "credit": 0},
        ]
        with pytest.raises(UnbalancedEntryError):
            validate_lines(lines)

    def test_negative_amount_raises(self):
        lines = [
            {"account_id": "a1", "debit": -50, "credit": 0},
            {"account_id": "a2", "debit": 0, "credit": -50},
        ]
        with pytest.raises(UnbalancedEntryError):
            validate_lines(lines)

    def test_same_line_debit_and_credit_raises(self):
        # سطر واحد مش ممكن يكون مدين ودائن في نفس الوقت
        lines = [
            {"account_id": "a1", "debit": 50, "credit": 50},
        ]
        with pytest.raises(UnbalancedEntryError):
            validate_lines(lines)

    def test_sale_invoice_with_tax_pattern(self):
        # نفس نمط القيد التلقائي اللي بيتعمل عند إنشاء فاتورة مبيعات فيها ضريبة
        subtotal, tax = 1000, 140
        lines = [
            {"account_id": "receivable", "debit": subtotal + tax, "credit": 0},
            {"account_id": "sales", "debit": 0, "credit": subtotal},
            {"account_id": "tax_payable", "debit": 0, "credit": tax},
        ]
        validate_lines(lines)  # لازم يعدي من غير مشاكل


class TestReverseLines:
    """
    اختبارات دالة عكس القيد (بديل الحذف النهائي).
    عكس القيد لازم يفضل متوازن هو نفسه، وبيبدّل مدين/دائن كل سطر.
    """

    def test_reverse_swaps_debit_and_credit(self):
        lines = [
            {"account_id": "cash", "debit": 100, "credit": 0, "description": "قبض نقدي"},
            {"account_id": "receivable", "debit": 0, "credit": 100, "description": "سداد عميل"},
        ]
        reversed_lines = reverse_lines(lines)
        assert reversed_lines[0]["account_id"] == "cash"
        assert reversed_lines[0]["debit"] == Decimal("0")
        assert reversed_lines[0]["credit"] == Decimal("100")
        assert reversed_lines[1]["debit"] == Decimal("100")
        assert reversed_lines[1]["credit"] == Decimal("0")

    def test_reversed_lines_are_still_balanced(self):
        lines = [
            {"account_id": "a1", "debit": 114, "credit": 0},
            {"account_id": "a2", "debit": 0, "credit": 100},
            {"account_id": "a3", "debit": 0, "credit": 14},
        ]
        reversed_lines = reverse_lines(lines)
        validate_lines(reversed_lines)  # لازم يعدي - العكس لازم يكون متوازن برضه

    def test_reversed_description_is_marked(self):
        lines = [{"account_id": "a1", "debit": 50, "credit": 0, "description": "إيجار المكتب"}]
        reversed_lines = reverse_lines(lines)
        assert "عكس" in reversed_lines[0]["description"]
        assert "إيجار المكتب" in reversed_lines[0]["description"]
