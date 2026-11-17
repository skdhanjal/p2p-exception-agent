import pytest
from common.approvals_logic import validate_decision

OK = {
    "email": "boss@example.com",
    "approvers": {"boss@example.com"},
    "invoice_number": "INV-2001",
    "vendor_id": "V-1001",
    "amount": 441.0,
    "currency": "USD",
    "decision": "approved",
}


def test_an_approver_may_decide():
    validate_decision(**OK)


def test_a_stranger_may_not():
    with pytest.raises(PermissionError):
        validate_decision(**{**OK, "email": "x@example.com"})


def test_bad_input_is_refused():
    for change in (
        {"decision": "paid"},
        {"amount": 0},
        {"invoice_number": "x; DROP"},
        {"currency": "usd"},
    ):
        with pytest.raises(ValueError):
            validate_decision(**{**OK, **change})
