"""Pure checks for a payment request. No I/O, easy to test."""

from datetime import datetime, timedelta
from typing import Optional

from common import ids

MAX_PAYMENT = 25000.00  # hard cap per request, in the invoice currency
TOLERANCE = 0.01


def check_payment(
    invoice: dict | None,
    vendor: dict | None,
    amount: float,
    approval_id: str,
) -> list[str]:
    """Return a list of problems. An empty list means the request is OK."""
    problems: list[str] = []
    if not ids.is_valid("approval_id", approval_id):
        problems.append("approval_id has an invalid format")
    if amount <= 0:
        problems.append("amount must be greater than zero")
    if amount > MAX_PAYMENT:
        problems.append(f"amount exceeds the limit of {MAX_PAYMENT:,.2f}")
    if invoice is None:
        problems.append("invoice not found for this vendor")
    else:
        if invoice["status"] != "approved":
            problems.append(f"invoice status is {invoice['status']}, not approved")
        if abs(float(invoice["total_amount"]) - amount) > TOLERANCE:
            problems.append("amount does not match the invoice total")
    if vendor is None or vendor["status"] != "active":
        problems.append("vendor is not active")
    return problems



POLICY_APPROVAL = "APR-000000"  # automatic approval by policy
POLICY_LIMIT = 5000.00  # must be at least the workflow's limit
APPROVAL_TTL = timedelta(hours=24)


def check_approval(
    approval: dict | None,
    used: bool,
    *,
    approval_id: str,
    invoice_number: str,
    vendor_id: str,
    amount: float,
    now: datetime,
) -> list[str]:
    """Return problems with the approval. Empty means it may be spent."""
    if approval_id == POLICY_APPROVAL:
        if amount > POLICY_LIMIT:
            return ["policy approval does not cover this amount"]
        return []
    if approval is None:
        return ["approval not found"]
    problems: list[str] = []
    if approval["status"] != "approved":
        problems.append("approval is not an approval")
    if used:
        problems.append("approval was already used")
    if (approval["invoice_number"], approval["vendor_id"]) != (
        invoice_number,
        vendor_id,
    ):
        problems.append("approval is for a different invoice")
    if abs(float(approval["amount"]) - amount) > TOLERANCE:
        problems.append("approval is for a different amount")
    if now - approval["decided_at"] > APPROVAL_TTL:
        problems.append("approval has expired")
    return problems
