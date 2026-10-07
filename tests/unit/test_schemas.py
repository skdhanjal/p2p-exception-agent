from app.schemas import validate_invoice

VALID = {
    "invoice_number": "INV-2001",
    "vendor_name": "Acme Supplies",
    "po_number": "PO-7701",
    "invoice_date": "2026-10-01",
    "currency": "USD",
    "line_items": [
        {
            "description": "A4 paper ream",
            "quantity": 100,
            "unit_price": 4.2,
            "line_total": 420.0,
        },
    ],
    "subtotal": 420.0,
    "tax_amount": 21.0,
    "total_amount": 441.0,
}


def test_valid_invoice_passes():
    invoice, errors = validate_invoice(VALID)
    assert errors == []
    assert invoice is not None
    assert invoice.invoice_number == "INV-2001"


def test_wrong_total_is_reported():
    invoice, errors = validate_invoice({**VALID, "total_amount": 500.0})
    assert invoice is None
    assert any("total_amount" in e for e in errors)


def test_bad_date_is_reported():
    _, errors = validate_invoice({**VALID, "invoice_date": "01/10/2026"})
    assert any("invoice_date" in e for e in errors)


def test_bad_line_math_is_reported():
    bad = dict(VALID)
    bad["line_items"] = [
        {
            "description": "A4 paper ream",
            "quantity": 100,
            "unit_price": 4.2,
            "line_total": 999.0,
        }
    ]
    _, errors = validate_invoice(bad)
    assert any("line_total" in e for e in errors)
