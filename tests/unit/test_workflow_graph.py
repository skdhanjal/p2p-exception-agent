"""Graph tests with LLM nodes and MCP calls stubbed. No network."""

import asyncio

from fastmcp.exceptions import ToolError
from google.adk import Event
from google.adk.runners import InMemoryRunner
from google.adk.workflow import FunctionNode
from google.genai import types

from app import mcp_call
from app.workflow import build_workflow

CLEAN = {
    "invoice_number": "INV-2001",
    "vendor_name": "Acme Supplies",
    "po_number": "PO-7701",
    "invoice_date": "2026-10-01",
    "currency": "USD",
    "subtotal": 420.0,
    "tax_amount": 21.0,
    "total_amount": 441.0,
    "bank_account_last4": "4821",
    "line_items": [
        {
            "description": "A4 paper ream",
            "quantity": 100,
            "unit_price": 4.2,
            "line_total": 420.0,
        }
    ],
    "extraction_notes": [],
}
PRICEY = {
    **CLEAN,
    "subtotal": 500.0,
    "tax_amount": 0.0,
    "total_amount": 500.0,
    "line_items": [
        {
            "description": "A4 paper ream",
            "quantity": 100,
            "unit_price": 5.0,
            "line_total": 500.0,
        }
    ],
}
BAD_TOTALS = {**CLEAN, "total_amount": 999.0}

VENDOR = {
    "status": "found",
    "vendors": [
        {
            "vendor_id": "V-1001",
            "name": "Acme Supplies",
            "status": "active",
            "bank_account_last4": "4821",
            "payment_terms": "NET30",
        }
    ],
}
PO = {
    "status": "found",
    "purchase_order": {"po_number": "PO-7701"},
    "lines": [
        {
            "line_no": 1,
            "description": "A4 paper ream",
            "quantity": 100,
            "unit_price": 4.2,
            "received_qty": 100,
        }
    ],
}


def fake_calls(invoice_found=False, vendor_error=False):
    async def fake(server, tool, args):
        if tool == "lookup_vendor":
            if vendor_error:
                raise ToolError("vendor service rejected the request")
            return VENDOR
        if tool == "get_invoice_status":
            if invoice_found:
                return {"status": "found", "invoices": [{"invoice_number": "INV-2001"}]}
            return {"status": "not_found"}
        if tool == "lookup_purchase_order":
            return PO
        raise AssertionError(f"unexpected tool {tool}")

    return fake


def make_workflow(invoice):
    summary = {
        "headline": "Needs review",
        "details": ["stub detail"],
        "recommendation": "Check it.",
    }
    return build_workflow(
        extract=FunctionNode(
            func=lambda node_input: Event(output=invoice), name="extract_invoice"
        ),
        summarize=FunctionNode(
            func=lambda node_input: Event(output=summary), name="summarize_case"
        ),
        qa=FunctionNode(func=lambda node_input: "answer", name="qa_agent"),
    )


def document():
    return types.Content(
        role="user",
        parts=[
            types.Part(text="Process this invoice."),
            types.Part.from_bytes(data=b"%PDF-1.4", mime_type="application/pdf"),
        ],
    )


def reply(call, text):
    response = types.FunctionResponse(
        id=call.id, name="adk_request_input", response={"result": text}
    )
    return types.Content(role="user", parts=[types.Part(function_response=response)])


async def run(workflow, message, runner=None, session=None):
    runner = runner or InMemoryRunner(agent=workflow, app_name="test")
    session = session or await runner.session_service.create_session(
        app_name="test", user_id="u"
    )
    events = [
        e
        async for e in runner.run_async(
            user_id="u", session_id=session.id, new_message=message
        )
    ]
    return runner, session, events


def request_of(events):
    for event in events:
        for call in event.get_function_calls():
            if call.name == "adk_request_input":
                return call
    return None


def decision_of(events):
    found = [
        e.output
        for e in events
        if isinstance(e.output, dict) and "decision" in e.output
    ]
    return found[-1]["decision"] if found else None


def test_clean_invoice_is_auto_approved(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls())
    _, _, events = asyncio.run(run(make_workflow(CLEAN), document()))
    assert request_of(events) is None
    assert decision_of(events) == "APPROVED_AUTOMATICALLY"


def test_price_mismatch_pauses_then_human_approves(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls())

    async def scenario():
        wf = make_workflow(PRICEY)
        runner, session, events = await run(wf, document())
        call = request_of(events)
        assert call is not None
        return await run(wf, reply(call, "approve - vendor agreed"), runner, session)

    _, _, events = asyncio.run(scenario())
    assert decision_of(events) == "APPROVED_BY_HUMAN"


def test_human_can_reject(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls())

    async def scenario():
        wf = make_workflow(PRICEY)
        runner, session, events = await run(wf, document())
        return await run(wf, reply(request_of(events), "reject"), runner, session)

    _, _, events = asyncio.run(scenario())
    assert decision_of(events) == "REJECTED_BY_HUMAN"


def test_unclear_replies_end_in_rejection(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls())

    async def scenario():
        wf = make_workflow(PRICEY)
        runner, session, events = await run(wf, document())
        call = request_of(events)
        for word in ("maybe", "hmm"):
            _, _, events = await run(wf, reply(call, word), runner, session)
            call = request_of(events)
            assert call is not None  # asked again
        return await run(wf, reply(call, "dunno"), runner, session)

    _, _, events = asyncio.run(scenario())
    assert decision_of(events) == "REJECTED_BY_HUMAN"


def test_duplicate_is_held_without_asking_a_human(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls(invoice_found=True))
    _, _, events = asyncio.run(run(make_workflow(CLEAN), document()))
    assert request_of(events) is None
    assert decision_of(events) == "ON_HOLD"


def test_invalid_extraction_never_reaches_the_checks(monkeypatch):
    async def boom(*args):
        raise AssertionError("MCP must not be called")

    monkeypatch.setattr(mcp_call, "call_tool", boom)
    _, _, events = asyncio.run(run(make_workflow(BAD_TOTALS), document()))
    assert decision_of(events) == "NEEDS_MANUAL_REVIEW"


def test_a_question_goes_to_the_qa_node(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls())
    question = types.Content(
        role="user", parts=[types.Part(text="Status of INV-1002?")]
    )
    _, _, events = asyncio.run(run(make_workflow(CLEAN), question))
    assert "answer" in [e.output for e in events]


def test_a_failed_check_fails_closed_to_a_human(monkeypatch):
    monkeypatch.setattr(mcp_call, "call_tool", fake_calls(vendor_error=True))
    _, _, events = asyncio.run(run(make_workflow(CLEAN), document()))
    assert request_of(events) is not None  # never auto-approved
