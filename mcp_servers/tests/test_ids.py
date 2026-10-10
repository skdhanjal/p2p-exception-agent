from common import ids


def test_valid_identifiers():
    assert ids.is_valid("po_number", "PO-7781")
    assert ids.is_valid("vendor_id", "V-1002")
    assert ids.is_valid("approval_id", "APR-000123")


def test_injection_style_input_is_rejected():
    assert not ids.is_valid("po_number", "PO-7781; DROP TABLE x")
    assert not ids.is_valid("invoice_number", "../../etc/passwd")
    assert not ids.is_valid("vendor_id", "V-1002 OR 1=1")


def test_non_strings_are_rejected():
    assert not ids.is_valid("po_number", 7781)
    assert not ids.is_valid("vendor_id", None)
