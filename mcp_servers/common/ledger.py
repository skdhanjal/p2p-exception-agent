"""Pure logic for recording invoice decisions. Takes a query callable."""

from collections.abc import Callable

from common import ids

ALLOWED_STATUS = {"approved", "on_hold", "rejected"}
Query = Callable[[str, dict], list]


def record_decision(
    query: Query,
    *,
    invoice_number: str,
    vendor_id: str,
    total_amount: float,
    status: str,
    po_number: str = "",
    reason: str = "",
) -> dict:
    """Insert an invoice decision once. Raises ValueError if invalid."""
    if not ids.is_valid("invoice_number", invoice_number):
        raise ValueError("invoice_number has an invalid format")
    if not ids.is_valid("vendor_id", vendor_id):
        raise ValueError("vendor_id has an invalid format")
    if po_number and not ids.is_valid("po_number", po_number):
        raise ValueError("po_number has an invalid format")
    if status not in ALLOWED_STATUS:
        raise ValueError("status must be approved, on_hold, or rejected")
    if total_amount <= 0:
        raise ValueError("total_amount must be greater than zero")
    if len(reason) > 200:
        raise ValueError("reason is too long")

    vendor = query(
        "SELECT status FROM `__DATASET__.vendors` WHERE vendor_id = @v",
        {"v": vendor_id},
    )
    if not vendor:
        raise ValueError("vendor not found")
    if status == "approved" and vendor[0]["status"] != "active":
        raise ValueError("an inactive vendor's invoice cannot be approved")

    existing = query(
        """
        SELECT status FROM `__DATASET__.invoices`
        WHERE vendor_id = @vendor_id AND invoice_number = @invoice_number
        """,
        {"vendor_id": vendor_id, "invoice_number": invoice_number},
    )
    if existing:
        return {"status": "already_recorded", "invoice_status": existing[0]["status"]}

    query(
        """
        INSERT INTO `__DATASET__.invoices`
          (invoice_number, vendor_id, po_number, total_amount,
           status, hold_reason)
        VALUES (@invoice_number, @vendor_id, NULLIF(@po_number, ''),
                @total_amount, @status, NULLIF(@reason, ''))
        """,
        {
            "invoice_number": invoice_number,
            "vendor_id": vendor_id,
            "po_number": po_number,
            "total_amount": float(total_amount),
            "status": status,
            "reason": reason,
        },
    )
    return {"status": "recorded", "invoice_status": status}
