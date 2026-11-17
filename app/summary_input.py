"""A minimal, allowlisted view of a case for the summary model."""

import json

from app import ids


def _safe(kind: str, value):
    """Identifiers that fail their format never reach the model."""
    if value is None or ids.is_valid(kind, value):
        return value
    return "[invalid identifier]"


def minimize_case(case: dict) -> dict:
    invoice = case["invoice"]
    checks = case["checks"]
    vendor = checks.get("check_vendor", {})
    po = checks.get("check_po", {})
    return {
        "invoice_number": _safe("invoice_number", invoice["invoice_number"]),
        "po_number": _safe("po_number", invoice.get("po_number")),
        "total_amount": invoice["total_amount"],
        "currency": invoice["currency"],
        "vendor_id": vendor.get("vendor_id"),
        "vendor_status": vendor.get("vendor_status"),
        "payment_terms": vendor.get("payment_terms"),
        "decision": case["decision"],
        "flags": case["flags"],
        "findings": [
            {k: v for k, v in f.items() if k != "description"}
            for f in po.get("findings", [])
        ],
    }


def as_text(case: dict) -> str:
    return json.dumps(minimize_case(case))
