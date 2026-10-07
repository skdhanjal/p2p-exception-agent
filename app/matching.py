"""Deterministic invoice-to-PO comparison. No LLM involved."""

PRICE_TOLERANCE_PCT = 1.0  # unit price may differ by up to 1 percent


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def compare_invoice_to_po(invoice_lines: list[dict], po_lines: list[dict]) -> dict:
    """Compare invoice lines with PO lines and report exceptions."""
    po_by_desc = {_norm(p["description"]): p for p in po_lines}
    findings: list[dict] = []
    for line in invoice_lines:
        po_line = po_by_desc.get(_norm(line["description"]))
        if po_line is None:
            findings.append(
                {"type": "line_not_on_po", "description": line["description"]}
            )
            continue
        findings.extend(_check_line(line, po_line))
    status = "exceptions_found" if findings else "matched"
    return {"match_status": status, "findings": findings}


def _check_line(line: dict, po_line: dict) -> list[dict]:
    found = []
    qty = float(line["quantity"])
    inv_price = float(line["unit_price"])
    po_price = float(po_line["unit_price"])
    diff_pct = abs(inv_price - po_price) / po_price * 100 if po_price else 0
    if diff_pct > PRICE_TOLERANCE_PCT:
        found.append(
            {
                "type": "price_mismatch",
                "description": line["description"],
                "po_unit_price": po_price,
                "invoice_unit_price": inv_price,
                "variance_amount": round((inv_price - po_price) * qty, 2),
            }
        )
    received = float(po_line["received_qty"])
    if qty > received:
        found.append(
            {
                "type": "quantity_exceeds_received",
                "description": line["description"],
                "invoiced_qty": qty,
                "received_qty": received,
            }
        )
    return found
