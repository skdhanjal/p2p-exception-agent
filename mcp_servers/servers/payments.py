"""Payments MCP server: guarded creation of payment requests."""

import os
import uuid
from datetime import UTC, datetime

from common import ids, ledger
from common.bq import run_query
from common.logs import log
from common.payment_rules import POLICY_APPROVAL, check_approval, check_payment
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("p2p-payments")


@mcp.tool(
    annotations={
        "title": "Request Payment",
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
def request_payment(
    invoice_number: str,
    vendor_id: str,
    amount: float,
    currency: str,
    approval_id: str,
    idempotency_key: str,
    dry_run: bool = True,
) -> dict:
    """Create a payment request for an approved invoice.

    Defaults to a dry run that changes nothing. Set dry_run to false
    only after a human approval exists. Repeating the same
    idempotency_key returns the original request.

    Args:
        invoice_number: The invoice to pay.
        vendor_id: The vendor id on that invoice.
        amount: The amount to pay. Must equal the invoice total.
        currency: Three-letter currency code, for example "USD".
        approval_id: The human approval reference, "APR-" and six digits.
        idempotency_key: A unique key for this request (8 to 64 chars).
        dry_run: When true (the default), validate only.

    Returns:
        status "dry_run", "created", or "replayed", with the request.
    """
    for kind, value in (
        ("invoice_number", invoice_number),
        ("vendor_id", vendor_id),
        ("currency", currency),
        ("approval_id", approval_id),
        ("idempotency_key", idempotency_key),
    ):
        if not ids.is_valid(kind, value):
            raise ToolError(f"{kind} has an invalid format")

    invoice_rows = run_query(
        """
        SELECT status, total_amount FROM `__DATASET__.invoices`
        WHERE vendor_id = @vendor_id AND invoice_number = @invoice_number
        """,
        {"vendor_id": vendor_id, "invoice_number": invoice_number},
    )
    vendor_rows = run_query(
        "SELECT status FROM `__DATASET__.vendors` WHERE vendor_id = @v",
        {"v": vendor_id},
    )
    problems = check_payment(
        invoice_rows[0] if invoice_rows else None,
        vendor_rows[0] if vendor_rows else None,
        amount,
        approval_id,
    )
    if problems:
        log("WARNING", "payment_rejected", reasons=len(problems))
        raise ToolError("; ".join(problems))

    existing = run_query(
        """
        SELECT request_id, invoice_number, amount, status
        FROM `__DATASET__.payment_requests`
        WHERE idempotency_key = @key
        """,
        {"key": idempotency_key},
    )
    if existing:
        log("INFO", "payment_replayed")
        return {"status": "replayed", "request": existing[0]}

    approval_rows = run_query(
        """
    SELECT approval_id, invoice_number, vendor_id, amount,
            decision AS status, decided_at
    FROM `__DATASET__.approvals` WHERE approval_id = @id
    """,
        {"id": approval_id},
    )
    used = bool(
        run_query(
            """
        SELECT approval_id FROM `__DATASET__.approval_consumptions`
        WHERE approval_id = @id
        """,
            {"id": approval_id},
        )
    )
    approval_problems = check_approval(
        approval_rows[0] if approval_rows else None,
        used,
        approval_id=approval_id,
        invoice_number=invoice_number,
        vendor_id=vendor_id,
        amount=amount,
        now=datetime.now(UTC),
    )
    if approval_problems:
        log("WARNING", "approval_rejected", reasons=len(approval_problems))
        raise ToolError("; ".join(approval_problems))

    request = {
        "request_id": "PAY-" + uuid.uuid4().hex[:10],
        "invoice_number": invoice_number,
        "amount": amount,
        "currency": currency,
    }
    if dry_run:
        log("INFO", "payment_dry_run")
        return {"status": "dry_run", "request": request}

    run_query(
        """
        INSERT INTO `__DATASET__.payment_requests`
          (request_id, idempotency_key, invoice_number, vendor_id,
           amount, currency, approval_id, status, created_at)
        VALUES (@request_id, @key, @invoice_number, @vendor_id,
                @amount, @currency, @approval_id, 'requested',
                CURRENT_TIMESTAMP())
        """,
        {
            "request_id": request["request_id"],
            "key": idempotency_key,
            "invoice_number": invoice_number,
            "vendor_id": vendor_id,
            "amount": float(amount),
            "currency": currency,
            "approval_id": approval_id,
        },
    )
    if approval_id != POLICY_APPROVAL:
        run_query(
            """
            INSERT INTO `__DATASET__.approval_consumptions`
              (approval_id, request_id, consumed_at)
            VALUES (@id, @request, CURRENT_TIMESTAMP())
            """,
            {"id": approval_id, "request": request["request_id"]},
        )

    log("INFO", "payment_created", request_id=request["request_id"])
    return {"status": "created", "request": request}


@mcp.tool(
    annotations={
        "title": "Record Invoice Decision",
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
def record_invoice_decision(
    invoice_number: str,
    vendor_id: str,
    total_amount: float,
    status: str,
    po_number: str = "",
    reason: str = "",
) -> dict:
    """Record the outcome of invoice processing in the ERP, once.

    If the invoice is already recorded for this vendor, the existing
    status is returned and nothing changes.

    Args:
        invoice_number: The invoice number.
        vendor_id: The vendor id, for example "V-1001".
        total_amount: The invoice total. Must be greater than zero.
        status: "approved", "on_hold", or "rejected".
        po_number: The PO number, or empty.
        reason: A short reason, up to 200 characters.

    Returns:
        status "recorded" or "already_recorded", with invoice_status.
    """
    try:
        result = ledger.record_decision(
            run_query,
            invoice_number=invoice_number,
            vendor_id=vendor_id,
            total_amount=total_amount,
            status=status,
            po_number=po_number,
            reason=reason,
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    log("INFO", "invoice_decision", outcome=result["status"])
    return result


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        stateless_http=True,
    )
