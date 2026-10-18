"""Pure helpers: whether and how to ask for a payment."""

import hashlib
import re

POLICY_APPROVAL = "APR-000000"  # automatic approval by policy
PAYABLE = {"AUTO_APPROVE": False, "APPROVED": True}  # value: human?


def approval_ref(invoice_number: str, vendor_id: str, human: bool) -> str:
    """A stable stand-in for an approval id (real ids arrive in Phase 7)."""
    if not human:
        return POLICY_APPROVAL
    seed = f"{vendor_id}|{invoice_number}".encode()
    number = int(hashlib.sha256(seed).hexdigest()[:8], 16) % 1_000_000
    return f"APR-{number:06d}"


def build_instruction(
    final_decision: str | None,
    invoice: dict,
    case: dict,
    dry_run: bool,
) -> dict | None:
    """Return the executor instruction, or None if nothing may be paid."""
    if final_decision not in PAYABLE:
        return None
    vendor = case.get("checks", {}).get("check_vendor", {})
    vendor_id = vendor.get("vendor_id")
    if not vendor_id or vendor.get("vendor_status") != "active":
        return None
    number = invoice["invoice_number"]
    key = re.sub(r"[^A-Za-z0-9\-_]", "-", f"{vendor_id}-{number}")[:64]
    human = PAYABLE[final_decision]
    return {
        "invoice_number": number,
        "vendor_id": vendor_id,
        "po_number": invoice.get("po_number") or "",
        "amount": invoice["total_amount"],
        "currency": invoice["currency"],
        "approval_id": approval_ref(number, vendor_id, human),
        "idempotency_key": key,
        "decision_reason": (
            "approved by a person" if human else "auto-approved by policy"
        ),
        "dry_run": dry_run,
    }
