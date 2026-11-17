"""Offline attacks. Some fail until Steps 5 and 6 add the controls."""

import sys
from datetime import datetime, timedelta, timezone

import pytest
from google.genai import types

sys.path.insert(0, "mcp_servers")

from app import replies  # noqa: E402
from app.schemas import validate_invoice  # noqa: E402

PDF = b"%PDF-1.4 test"


def doc(mime, data):
    return types.Part.from_bytes(data=data, mime_type=mime)


# ---- Admission control (Step 5) ----------------------------------------
def admission():
    from app import admission as module

    return module


def test_oversized_upload_is_refused():
    big = doc("application/pdf", PDF + b"0" * (6 * 1024 * 1024))
    assert admission().check_parts([big])


def test_wrong_file_type_is_refused():
    assert admission().check_parts([doc("application/zip", b"PK\x03\x04")])


def test_spoofed_file_signature_is_refused():
    assert admission().check_parts([doc("application/pdf", b"MZ\x90")])


def test_referenced_files_are_refused():
    ref = types.Part(
        file_data=types.FileData(
            file_uri="gs://other-bucket/x.pdf", mime_type="application/pdf"
        )
    )
    assert admission().check_parts([ref])


def test_two_documents_are_refused():
    assert admission().check_parts(
        [doc("application/pdf", PDF), doc("application/pdf", PDF)]
    )


# ---- Size limits (Step 5) ----------------------------------------------
BASE = {
    "invoice_number": "INV-4001",
    "vendor_name": "Acme Supplies",
    "po_number": "PO-7701",
    "invoice_date": "2026-10-01",
    "currency": "USD",
    "subtotal": 4.2,
    "tax_amount": 0.0,
    "total_amount": 4.2,
    "bank_account_last4": None,
    "line_items": [
        {
            "description": "A4 paper ream",
            "quantity": 1,
            "unit_price": 4.2,
            "line_total": 4.2,
        }
    ],
}


def test_thousands_of_line_items_are_refused():
    line = BASE["line_items"][0]
    many = {
        **BASE,
        "line_items": [line] * 5000,
        "subtotal": 4.2 * 5000,
        "total_amount": 4.2 * 5000,
    }
    assert validate_invoice(many)[0] is None


def test_enormous_text_fields_are_refused():
    long = {
        **BASE,
        "line_items": [{**BASE["line_items"][0], "description": "A" * 10000}],
    }
    assert validate_invoice(long)[0] is None


# ---- Approval verification (Step 6) -------------------------------------
NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
GOOD = {
    "approval_id": "APR-123456",
    "invoice_number": "INV-2001",
    "vendor_id": "V-1001",
    "amount": 441.0,
    "status": "approved",
    "decided_at": NOW - timedelta(hours=1),
}


def verdict(approval=GOOD, used=False, **override):
    from common.payment_rules import check_approval

    args = dict(
        approval_id="APR-123456",
        invoice_number="INV-2001",
        vendor_id="V-1001",
        amount=441.0,
        now=NOW,
    )
    args.update(override)
    return check_approval(approval, used, **args)


def test_a_matching_unused_approval_passes():
    assert verdict() == []


def test_forged_approval_id_fails():
    assert verdict(approval=None)


def test_approval_for_another_invoice_fails():
    assert verdict(invoice_number="INV-9999")


def test_approval_for_another_amount_fails():
    assert verdict(amount=44100.0)


def test_replayed_approval_fails():
    assert verdict(used=True)


def test_expired_approval_fails():
    old = {**GOOD, "decided_at": NOW - timedelta(hours=48)}
    assert verdict(approval=old)


def test_a_rejection_is_not_an_approval():
    assert verdict(approval={**GOOD, "status": "rejected"})


def test_policy_approval_cannot_cover_a_large_amount():
    assert verdict(approval=None, approval_id="APR-000000", amount=20000.0)


def test_policy_approval_covers_a_small_amount():
    assert verdict(approval=None, approval_id="APR-000000", amount=441.0) == []


# ---- Reply attacks (Steps 5 and 6) ---------------------------------------
@pytest.mark.parametrize(
    "reply",
    [
        "approve",
        "yes",
        "approve APR-000000",
        "approve but reject",
        "approve APR-123456 unless the vendor disagrees",
    ],
)
def test_unrecorded_or_hedged_replies_are_not_approvals(reply):
    verdict_, approval_id = replies.parse_with_id(reply)
    assert not (verdict_ == "APPROVED" and approval_id)


def test_a_recorded_approval_is_recognized():
    assert replies.parse_with_id("approve APR-123456") == ("APPROVED", "APR-123456")
