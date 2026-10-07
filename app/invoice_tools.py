"""Tools that read and write session state."""

from google.adk.tools import ToolContext

from app.erp_tools import lookup_purchase_order
from app.ids import is_valid
from app.matching import compare_invoice_to_po
from app.schemas import validate_invoice


def record_invoice_extraction(invoice: dict, tool_context: ToolContext) -> dict:
    """Validate and save the invoice data you extracted from a document.

    Call this once after reading an invoice. If it returns status
    "invalid", correct the listed errors using the document and call
    it again.

    Args:
        invoice: The extracted invoice as an object with the fields
            described in your instructions.

    Returns:
        status "recorded" with a short summary, or status "invalid"
        with a list of errors.
    """
    parsed, errors = validate_invoice(invoice)
    if parsed is None:
        return {"status": "invalid", "errors": errors}
    tool_context.state["current_invoice"] = parsed.model_dump()
    recent = list(tool_context.state.get("user:recent_invoices", []))
    tool_context.state["user:recent_invoices"] = ([parsed.invoice_number, *recent])[:5]
    return {
        "status": "recorded",
        "invoice_number": parsed.invoice_number,
        "vendor_name": parsed.vendor_name,
        "po_number": parsed.po_number,
        "total_amount": parsed.total_amount,
        "line_count": len(parsed.line_items),
    }


def compare_current_invoice_to_po(tool_context: ToolContext) -> dict:
    """Compare the recorded invoice with its purchase order.

    Uses the invoice saved by record_invoice_extraction. The
    differences are computed in code, not by the model.

    Returns:
        status "compared" with match_status and findings, or a status
        explaining why no comparison was possible.
    """
    invoice = tool_context.state.get("current_invoice")
    if not invoice:
        return {"status": "no_invoice", "message": "Record an invoice first."}
    po_number = invoice.get("po_number")
    if not po_number:
        return {"status": "no_po_number", "message": "The invoice shows no PO number."}
    if not is_valid("po_number", po_number):
        return {"status": "invalid_po_number", "po_number": po_number}
    po = lookup_purchase_order(po_number)
    if po["status"] == "not_found":
        return {"status": "po_not_found", "po_number": po_number}
    result = compare_invoice_to_po(invoice["line_items"], po["lines"])
    tool_context.state["last_comparison"] = result
    return {"status": "compared", "po_number": po_number, **result}
