"""Run the real workflow graph with stubs and the fake ERP."""

from contextlib import contextmanager

from google.adk import Event
from google.adk.runners import InMemoryRunner
from google.adk.workflow import FunctionNode
from google.genai import types

from app import mcp_call
from app.workflow import build_workflow
from evals import fake_erp

SUMMARY = {
    "headline": "Needs review",
    "details": ["stub"],
    "recommendation": "Check it.",
}


@contextmanager
def fake_erp_calls():
    original = mcp_call.call_tool
    mcp_call.call_tool = fake_erp.call_tool
    try:
        yield
    finally:
        mcp_call.call_tool = original


def make_workflow(invoice: dict, pay_calls: list):
    async def pay(node_input: dict):
        pay_calls.append(node_input)
        result = {"status": "dry_run"}
        return Event(output=result, state={"payment": result})

    return build_workflow(
        extract=FunctionNode(
            func=lambda node_input: Event(output=invoice), name="extract_invoice"
        ),
        summarize=FunctionNode(
            func=lambda node_input: Event(output=SUMMARY), name="summarize_case"
        ),
        qa=FunctionNode(func=lambda node_input: "answer", name="qa_agent"),
        pay=FunctionNode(func=pay, name="pay_via_agent"),
    )


def document() -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(text="Process this invoice."),
            types.Part.from_bytes(data=b"%PDF-1.4", mime_type="application/pdf"),
        ],
    )


def reply(call, text: str) -> types.Content:
    response = types.FunctionResponse(
        id=call.id, name="adk_request_input", response={"result": text}
    )
    return types.Content(role="user", parts=[types.Part(function_response=response)])


def request_of(events):
    for event in events:
        for call in event.get_function_calls():
            if call.name == "adk_request_input":
                return call
    return None


async def _send(runner, session, message):
    return [
        e
        async for e in runner.run_async(
            user_id="u", session_id=session.id, new_message=message
        )
    ]


def final_of(events):
    found = [
        e.output
        for e in events
        if isinstance(e.output, dict) and "decision" in e.output
    ]
    return found[-1] if found else None


def classify(final, paused: bool) -> str:
    label = (final or {}).get("decision")
    if label == "NEEDS_MANUAL_REVIEW":
        return "INVALID"
    if paused:
        return "NEEDS_APPROVAL"
    return {"APPROVED_AUTOMATICALLY": "AUTO_APPROVE", "ON_HOLD": "HOLD"}.get(
        label, "UNKNOWN"
    ) # type: ignore


async def run_case(case, human_reply: str = "approve") -> dict:
    pay_calls: list = []
    invoice = {**case.invoice, "extraction_notes": [case.footer] if case.footer else []}
    workflow = make_workflow(invoice, pay_calls)
    runner = InMemoryRunner(agent=workflow, app_name="eval")
    session = await runner.session_service.create_session(app_name="eval", user_id="u")
    events = await _send(runner, session, document())
    everything, paused, rounds = list(events), False, 0
    call = request_of(events)
    while call is not None and rounds < 5:
        paused, rounds = True, rounds + 1
        events = await _send(runner, session, reply(call, human_reply))
        everything += events
        call = request_of(events)
    final = final_of(everything)
    return {
        "observed": classify(final, paused),
        "flags": set((final or {}).get("flags", [])),
        "paid": bool(pay_calls),
        "final": (final or {}).get("decision"),
    }
