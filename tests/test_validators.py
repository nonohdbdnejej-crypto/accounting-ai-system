"""اختبارات utils/validators.py"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import (
    validate_email, validate_phone, validate_positive_amount, validate_currency
)


class TestValidateEmail:
    @pytest.mark.parametrize("email", [
        "test@example.com", "user.name@sub.example.com", "a@b.co",
    ])
    def test_valid_emails(self, email):
        assert validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "not-an-email", "missing@domain", "@nodomain.com", "", None, "spaces in@email.com",
    ])
    def test_invalid_emails(self, email):
        assert validate_email(email) is False


class TestValidatePhone:
    @pytest.mark.parametrize("phone", [
        "01012345678", "+20 100 123 4567", "0100-123-4567",
    ])
    def test_valid_phones(self, phone):
        assert validate_phone(phone) is True

    @pytest.mark.parametrize("phone", ["123", "", None, "abc"])
    def test_invalid_phones(self, phone):
        assert validate_phone(phone) is False


class TestValidatePositiveAmount:
    @pytest.mark.parametrize("value", [1, 0.01, "100", "99.99"])
    def test_valid_amounts(self, value):
        assert validate_positive_amount(value) is True

    @pytest.mark.parametrize("value", [0, -1, "abc", None, "-50"])
    def test_invalid_amounts(self, value):
        assert validate_positive_amount(value) is False


class TestValidateCurrency:
    @pytest.mark.parametrize("currency", ["EGP", "usd", "SAR"])
    def test_valid_currencies(self, currency):
        assert validate_currency(currency) is True

    @pytest.mark.parametrize("currency", ["XXX", "", None])
    def test_invalid_currencies(self, currency):
        assert validate_currency(currency) is False
