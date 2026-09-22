from datetime import date, timedelta
from decimal import Decimal
from app.services.parser import parse_sms_regex
from app.services.spending import jar_contribution


def test_jar_contribution():
    assert jar_contribution(Decimal("251")) == Decimal("9.00")
    assert jar_contribution(Decimal("250")) == Decimal("0.00")
    assert jar_contribution(Decimal("99.50")) == Decimal("0.50")


def test_parse_upi_sms():
    text = "Rs.250.00 debited from A/c XX1234 on 07-Sep-26 to VPA swiggy@ybl. Ref No 123456789."
    parsed = parse_sms_regex(text)
    assert parsed is not None
    assert parsed["amount"] == Decimal("250.00")
    assert "swiggy" in parsed["merchant"].lower()
    assert parsed["txn_date"] == date(2026, 9, 7)
    assert parsed["category"] == "Food"


def test_parse_card_sms():
    text = "INR 1,200.00 spent on your HDFC Bank Card XX5678 at AMAZON on 07-09-26."
    parsed = parse_sms_regex(text)
    assert parsed is not None
    assert parsed["amount"] == Decimal("1200.00")
    assert "AMAZON" in parsed["merchant"].upper()
    assert parsed["category"] == "Shopping"
