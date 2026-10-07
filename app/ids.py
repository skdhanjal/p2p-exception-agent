"""Identifier formats shared by tools and callbacks."""

import re

RULES = {
    "po_number": re.compile(r"^PO-\d{4,6}$"),
    "vendor_id": re.compile(r"^V-\d{4}$"),
    "invoice_number": re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_/]{0,39}$"),
    "vendor_name": re.compile(r"^[\w .,&'\-]{1,80}$"),
}


def is_valid(kind: str, value: object) -> bool:
    """True if value matches the expected format for this identifier."""
    return isinstance(value, str) and bool(RULES[kind].match(value))
