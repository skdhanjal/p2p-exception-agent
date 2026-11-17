"""Pure rules for recording an approval decision."""

from common import ids

DECISIONS = {"approved", "rejected"}


def validate_decision(
    *,
    email: str,
    approvers: set,
    invoice_number: str,
    vendor_id: str,
    amount: float,
    currency: str,
    decision: str,
    comment: str = "",
) -> None:
    """Raise PermissionError or ValueError if the decision is invalid."""
    if email.lower() not in approvers:
        raise PermissionError("caller is not an approver")
    if decision not in DECISIONS:
        raise ValueError("decision must be approved or rejected")
    if not ids.is_valid("invoice_number", invoice_number):
        raise ValueError("invoice_number has an invalid format")
    if not ids.is_valid("vendor_id", vendor_id):
        raise ValueError("vendor_id has an invalid format")
    if not ids.is_valid("currency", currency):
        raise ValueError("currency has an invalid format")
    if amount <= 0:
        raise ValueError("amount must be greater than zero")
    if len(comment) > 200:
        raise ValueError("comment is too long")
