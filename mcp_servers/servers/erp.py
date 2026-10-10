"""ERP MCP server: read-only purchase order and invoice lookups."""

import os

from common import ids
from common.bq import run_query
from common.logs import log
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("p2p-erp")
READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}


def _require(kind: str, value: str) -> None:
    if not ids.is_valid(kind, value):
        raise ToolError(f"{kind} has an invalid format")


@mcp.tool(annotations=READ_ONLY)
def lookup_purchase_order(po_number: str) -> dict:
    """Look up a purchase order, its lines, and goods received so far.

    Args:
        po_number: The PO number, for example "PO-7781".

    Returns:
        status "found" with the PO header and its lines (each with
        received_qty), or status "not_found".
    """
    _require("po_number", po_number)
    log("INFO", "tool_call", tool="lookup_purchase_order")
    header = run_query(
        """
        SELECT po_number, vendor_id, currency, total_amount, status
        FROM `__DATASET__.purchase_orders`
        WHERE po_number = @po_number
        """,
        {"po_number": po_number},
    )
    if not header:
        return {"status": "not_found", "po_number": po_number}
    lines = run_query(
        """
        SELECT l.line_no, l.description, l.quantity, l.unit_price,
               IFNULL(r.received_qty, 0) AS received_qty
        FROM `__DATASET__.po_lines` AS l
        LEFT JOIN `__DATASET__.goods_receipts` AS r
          ON r.po_number = l.po_number AND r.line_no = l.line_no
        WHERE l.po_number = @po_number
        ORDER BY l.line_no
        """,
        {"po_number": po_number},
    )
    return {"status": "found", "purchase_order": header[0], "lines": lines}


@mcp.tool(annotations=READ_ONLY)
def check_duplicate_invoice(vendor_id: str, invoice_number: str) -> dict:
    """Check whether this vendor already submitted this invoice number.

    Args:
        vendor_id: The vendor id, for example "V-1003".
        invoice_number: The invoice number from the document.

    Returns:
        status "duplicate" with the existing invoice, or "no_duplicate".
    """
    _require("vendor_id", vendor_id)
    _require("invoice_number", invoice_number)
    log("INFO", "tool_call", tool="check_duplicate_invoice")
    rows = run_query(
        """
        SELECT invoice_number, vendor_id, po_number, total_amount,
               status, hold_reason
        FROM `__DATASET__.invoices`
        WHERE vendor_id = @vendor_id AND invoice_number = @invoice_number
        """,
        {"vendor_id": vendor_id, "invoice_number": invoice_number},
    )
    if rows:
        return {"status": "duplicate", "existing_invoice": rows[0]}
    return {"status": "no_duplicate"}


@mcp.tool(annotations=READ_ONLY)
def get_invoice_status(invoice_number: str) -> dict:
    """Look up the processing status of an invoice already in the ERP.

    Args:
        invoice_number: The invoice number, for example "INV-1002".

    Returns:
        status "found" with matching invoices (status, hold_reason,
        total_amount), or status "not_found".
    """
    _require("invoice_number", invoice_number)
    log("INFO", "tool_call", tool="get_invoice_status")
    rows = run_query(
        """
        SELECT invoice_number, vendor_id, po_number, total_amount,
               status, hold_reason
        FROM `__DATASET__.invoices`
        WHERE invoice_number = @invoice_number
        LIMIT 5
        """,
        {"invoice_number": invoice_number},
    )
    if not rows:
        return {"status": "not_found", "invoice_number": invoice_number}
    return {"status": "found", "invoices": rows}


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        stateless_http=True,
    )
