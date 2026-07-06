"""اختبارات models/invoices.py - حساب الإجماليات"""
import sys
import os
import pytest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.invoices import calculate_invoice_totals


class TestCalculateInvoiceTotals:
    def test_single_item_no_tax(self):
        items = [{"quantity": 2, "unit_price": 100}]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate=0)
        assert subtotal == Decimal("200.00")
        assert tax == Decimal("0.00")
        assert total == Decimal("200.00")

    def test_single_item_with_tax(self):
        items = [{"quantity": 1, "unit_price": 1000}]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate=14)
        assert subtotal == Decimal("1000.00")
        assert tax == Decimal("140.00")
        assert total == Decimal("1140.00")

    def test_multiple_items(self):
        items = [
            {"quantity": 2, "unit_price": 50},   # 100
            {"quantity": 3, "unit_price": 30},   # 90
        ]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate=0)
        assert subtotal == Decimal("190.00")
        assert total == Decimal("190.00")

    def test_fractional_quantity(self):
        items = [{"quantity": 1.5, "unit_price": 20}]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate=0)
        assert subtotal == Decimal("30.00")

    def test_empty_items_returns_zero(self):
        subtotal, tax, total = calculate_invoice_totals([], tax_rate=14)
        assert subtotal == Decimal("0.00")
        assert tax == Decimal("0.00")
        assert total == Decimal("0.00")

    def test_tax_rounding(self):
        # 33.33 كـ string/float بيتحول لـ Decimal بدقة (مش زي float العادي)
        items = [{"quantity": 1, "unit_price": "33.33"}]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate=14)
        assert subtotal == Decimal("33.33")
        # 33.33 * 14% = 4.6662 -> بيتقرب لأقرب قرش (half-up) = 4.67
        assert tax == Decimal("4.67")
        assert total == Decimal("38.00")

    def test_string_inputs_from_form(self):
        # القيم الجاية من فورم HTML بتبقى strings
        items = [{"quantity": "2", "unit_price": "19.99"}]
        subtotal, tax, total = calculate_invoice_totals(items, tax_rate="0")
        assert subtotal == Decimal("39.98")
