import pytest
from common.ledger import record_decision


def make_query(vendor_status="active", existing=None):
    calls = []

    def query(sql, params):
        calls.append(sql)
        if "FROM `__DATASET__.vendors`" in sql:
            return [{"status": vendor_status}] if vendor_status else []
        if "SELECT" in sql and "`__DATASET__.invoices`" in sql:
            return existing or []
        return []

    return query, calls


ARGS = {
    "invoice_number": "INV-2001",
    "vendor_id": "V-1001",
    "total_amount": 441.0,
    "status": "approved",
    "po_number": "PO-7701",
}


def test_new_decision_is_inserted():
    query, calls = make_query()
    assert record_decision(query, **ARGS)["status"] == "recorded"
    assert any("INSERT" in sql for sql in calls)


def test_existing_decision_is_not_overwritten():
    query, calls = make_query(existing=[{"status": "approved"}])
    result = record_decision(query, **ARGS)
    assert result["status"] == "already_recorded"
    assert not any("INSERT" in sql for sql in calls)


def test_inactive_vendor_cannot_be_approved():
    query, _ = make_query(vendor_status="on_hold")
    with pytest.raises(ValueError):
        record_decision(query, **ARGS)


def test_unknown_vendor_is_rejected():
    query, _ = make_query(vendor_status=None) # type: ignore
    with pytest.raises(ValueError):
        record_decision(query, **ARGS)


def test_bad_status_and_bad_ids_are_rejected():
    query, _ = make_query()
    with pytest.raises(ValueError):
        record_decision(query, **{**ARGS, "status": "paid"})
    with pytest.raises(ValueError):
        record_decision(query, **{**ARGS, "invoice_number": "x; DROP"})
