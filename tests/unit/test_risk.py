from app.risk import assess

INVOICE = {"total_amount": 441.0}
OK_VENDOR = {"status": "ok", "flags": []}
NO_DUP = {"status": "no_duplicate"}
OK_PO = {"status": "ok", "flags": [], "findings": []}


def checks(vendor=OK_VENDOR, dup=NO_DUP, po=OK_PO):
    return {"check_vendor": vendor, "check_duplicate": dup, "check_po": po}


def test_clean_invoice_is_auto_approved():
    assert assess(INVOICE, checks())["decision"] == "AUTO_APPROVE"


def test_price_mismatch_needs_approval():
    po = {"status": "ok", "flags": [], "findings": [{"type": "price_mismatch"}]}
    result = assess(INVOICE, checks(po=po))
    assert result["decision"] == "NEEDS_APPROVAL"
    assert "price_mismatch" in result["flags"]


def test_duplicate_is_held():
    result = assess(INVOICE, checks(dup={"status": "duplicate"}))
    assert result["decision"] == "HOLD"


def test_bank_mismatch_is_held():
    vendor = {"status": "ok", "flags": ["bank_mismatch"]}
    assert assess(INVOICE, checks(vendor=vendor))["decision"] == "HOLD"


def test_large_amount_needs_approval():
    result = assess({"total_amount": 9000.0}, checks())
    assert result["decision"] == "NEEDS_APPROVAL"
    assert "over_auto_approve_limit" in result["flags"]


def test_failed_check_needs_approval():
    result = assess(INVOICE, checks(vendor={"status": "error"}))
    assert result["decision"] == "NEEDS_APPROVAL"
    assert "vendor_check_failed" in result["flags"]
