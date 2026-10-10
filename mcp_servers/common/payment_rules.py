"""Pure checks for a payment request. No I/O, easy to test."""

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
