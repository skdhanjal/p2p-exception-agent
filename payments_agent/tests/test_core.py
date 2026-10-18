import asyncio
import json

from fastmcp.exceptions import ToolError

from payments_agent.core import execute

GOOD = {
    "invoice_number": "INV-2001",
    "vendor_id": "V-1001",
    "po_number": "PO-7701",
    "amount": 441.0,
    "currency": "USD",
    "approval_id": "APR-000000",
    "idempotency_key": "V-1001-INV-2001",
}


def fake_tools(fail_on=None):
    calls = []

    async def call(tool, args):
        calls.append((tool, args))
        if tool == fail_on:
            raise ToolError("rejected by server")
        if tool == "record_invoice_decision":
            return {"status": "recorded"}
        return {"status": "dry_run", "request": {"request_id": "PAY-1"}}

    return call, calls


def run(raw, call, allow_live=False):
    return asyncio.run(execute(raw, call, allow_live))


def test_dry_run_records_then_requests_payment():
    call, calls = fake_tools()
    result = run(json.dumps(GOOD), call)
    assert [c[0] for c in calls] == ["record_invoice_decision", "request_payment"]
    assert calls[1][1]["dry_run"] is True
    assert result["status"] == "dry_run"


def test_live_payment_is_refused_when_disabled():
    call, calls = fake_tools()
    result = run(json.dumps({**GOOD, "dry_run": False}), call)
    assert result["status"] == "rejected"
    assert calls == []


def test_live_payment_runs_when_enabled():
    call, calls = fake_tools()
    run(json.dumps({**GOOD, "dry_run": False}), call, allow_live=True)
    assert calls[1][1]["dry_run"] is False


def test_garbage_is_rejected_without_any_call():
    call, calls = fake_tools()
    assert run("not json", call)["status"] == "rejected"
    assert run(json.dumps({"invoice_number": "x"}), call)["fields"]
    assert calls == []


def test_server_rejection_becomes_a_rejection():
    call, _ = fake_tools(fail_on="request_payment")
    assert run(json.dumps(GOOD), call)["status"] == "rejected"
