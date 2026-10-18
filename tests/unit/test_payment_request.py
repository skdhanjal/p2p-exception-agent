import re

from app.payment_request import POLICY_APPROVAL, build_instruction

INVOICE = {
    "invoice_number": "INV-2001",
    "po_number": "PO-7701",
    "total_amount": 441.0,
    "currency": "USD",
}
CASE = {"checks": {"check_vendor": {"vendor_id": "V-1001", "vendor_status": "active"}}}


def test_automatic_approval_uses_the_policy_reference():
    inst = build_instruction("AUTO_APPROVE", INVOICE, CASE, True)
    assert inst["approval_id"] == POLICY_APPROVAL
    assert inst["dry_run"] is True


def test_human_approval_gets_a_stable_reference():
    first = build_instruction("APPROVED", INVOICE, CASE, True)
    second = build_instruction("APPROVED", INVOICE, CASE, True)
    assert first["approval_id"] == second["approval_id"]
    assert re.fullmatch(r"APR-\d{6}", first["approval_id"])
    assert first["approval_id"] != POLICY_APPROVAL


def test_nothing_else_is_ever_paid():
    for key in ("HOLD", "REJECTED", "NEEDS_MANUAL_REVIEW", None):
        assert build_instruction(key, INVOICE, CASE, True) is None


def test_unknown_or_inactive_vendor_is_never_paid():
    unknown = {"checks": {"check_vendor": {"flags": ["vendor_not_found"]}}}
    inactive = {
        "checks": {"check_vendor": {"vendor_id": "V-1004", "vendor_status": "on_hold"}}
    }
    assert build_instruction("APPROVED", INVOICE, unknown, True) is None
    assert build_instruction("APPROVED", INVOICE, inactive, True) is None


def test_idempotency_key_is_stable_and_valid():
    inst = build_instruction("AUTO_APPROVE", INVOICE, CASE, True)
    assert re.fullmatch(r"[A-Za-z0-9\-_]{8,64}", inst["idempotency_key"])
    again = build_instruction("AUTO_APPROVE", INVOICE, CASE, True)
    assert inst["idempotency_key"] == again["idempotency_key"]
