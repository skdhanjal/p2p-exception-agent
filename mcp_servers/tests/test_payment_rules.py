from common.payment_rules import check_payment

INVOICE = {"status": "approved", "total_amount": 420.0}
VENDOR = {"status": "active"}


def test_good_request_has_no_problems():
    assert check_payment(INVOICE, VENDOR, 420.0, "APR-000001") == []


def test_amount_must_match_invoice():
    problems = check_payment(INVOICE, VENDOR, 999.0, "APR-000001")
    assert "amount does not match the invoice total" in problems


def test_amount_cap_is_enforced():
    big = {"status": "approved", "total_amount": 50000.0}
    problems = check_payment(big, VENDOR, 50000.0, "APR-000001")
    assert any("exceeds the limit" in p for p in problems)


def test_unapproved_invoice_is_rejected():
    held = {"status": "on_hold", "total_amount": 420.0}
    problems = check_payment(held, VENDOR, 420.0, "APR-000001")
    assert any("not approved" in p for p in problems)


def test_inactive_vendor_is_rejected():
    problems = check_payment(INVOICE, {"status": "on_hold"}, 420.0, "APR-000001")
    assert "vendor is not active" in problems


def test_missing_invoice_and_bad_approval():
    problems = check_payment(None, VENDOR, 420.0, "approved-by-me")
    assert "invoice not found for this vendor" in problems
    assert "approval_id has an invalid format" in problems
