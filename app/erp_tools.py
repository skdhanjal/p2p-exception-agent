"""Read-only ERP lookup tools exposed to the agent."""

from app.erp_client import run_query


def lookup_purchase_order(po_number: str) -> dict:
    """Look up a purchase order, its lines, and goods received so far.

    Args:
        po_number: The PO number, for example "PO-7781".

    Returns:
        status "found" with the PO header and its lines (each with
        received_qty), or status "not_found".
    """
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


def lookup_vendor(vendor_name: str) -> dict:
    """Find vendors by full or partial name.

    Args:
        vendor_name: The vendor name as written on the invoice.

    Returns:
        status "found" with up to five matching vendors (vendor_id,
        name, status, bank_account_last4, payment_terms), or
        status "not_found".
    """
    rows = run_query(
        """
        SELECT vendor_id, name, status, bank_account_last4, payment_terms
        FROM `__DATASET__.vendors`
        WHERE LOWER(name) LIKE @pattern
        ORDER BY name
        LIMIT 5
        """,
        {"pattern": f"%{vendor_name.strip().lower()}%"},
    )
    if not rows:
        return {"status": "not_found", "vendor_name": vendor_name}
    return {"status": "found", "vendors": rows}


def check_duplicate_invoice(vendor_id: str, invoice_number: str) -> dict:
    """Check whether this vendor already submitted this invoice number.

    Args:
        vendor_id: The vendor id from lookup_vendor, for example "V-1003".
        invoice_number: The invoice number from the document.

    Returns:
        status "duplicate" with the existing invoice, or "no_duplicate".
    """
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


def get_invoice_status(invoice_number: str) -> dict:
    """Look up the processing status of an invoice already in the ERP.

    Args:
        invoice_number: The invoice number, for example "INV-1002".

    Returns:
        status "found" with matching invoices (status, hold_reason,
        total_amount), or status "not_found".
    """
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
