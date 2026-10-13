"""Function nodes for the invoice workflow. Code decides; LLMs assist."""

from fastmcp.exceptions import ToolError
from google.adk import Event
from google.adk.agents.context import Context
from google.adk.events import RequestInput
from google.genai import types

from app import mcp_call
from app.matching import compare_invoice_to_po
from app.risk import assess
from app.schemas import validate_invoice as strict_validate

MAX_APPROVAL_ATTEMPTS = 3


def _as_dict(value) -> dict:
    """Agent nodes may hand over a model object or a plain dict."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value)


def route_request(node_input: types.Content):
    """Invoices carry a document; everything else is a question."""
    parts = node_input.parts or []
    has_document = any(p.inline_data or p.file_data for p in parts)
    if not has_document:
        return Event(output=node_input, route="QUESTION")
    return Event(
        output=node_input,
        route="INVOICE",
        state={
            "invoice": None,
            "case": None,
            "summary": None,
            "decision": None,
            "final_decision": None,
            "approval_attempts": 0,
        },
    )


def validate_invoice(node_input):
    """Strictly validate what the extraction agent returned."""
    raw = _as_dict(node_input)
    invoice, errors = strict_validate(raw)
    if invoice is None:
        return Event(output={"errors": errors}, route="INVALID")
    data = invoice.model_dump()
    return Event(output=data, route="VALID", state={"invoice": data})


def escalate_invalid(node_input: dict):
    """Failure branch: tell the user, record the outcome, stop."""
    errors = node_input.get("errors", [])
    text = (
        "I could not read this invoice reliably, so I have not "
        "processed it. Please review it manually.\n- " + "\n- ".join(errors)
    )
    yield Event(message=text)
    yield Event(
        output={"decision": "NEEDS_MANUAL_REVIEW", "errors": errors},
        state={"final_decision": "NEEDS_MANUAL_REVIEW"},
    )


def dispatch(node_input: dict):
    """Fan-out point: hand the validated invoice to the parallel checks."""
    return Event(output=node_input)


async def check_vendor(node_input: dict):
    """Look up the vendor; flag unknown, inactive, or bank mismatches."""
    try:
        result = await mcp_call.call_tool(
            "vendor", "lookup_vendor", {"vendor_name": node_input["vendor_name"]}
        )
    except ToolError as exc:
        return Event(output={"status": "error", "message": str(exc)})
    vendors = result.get("vendors", [])
    if len(vendors) != 1:
        flag = "vendor_not_found" if not vendors else "vendor_ambiguous"
        return Event(output={"status": "ok", "flags": [flag]})
    vendor = vendors[0]
    flags = []
    if vendor["status"] != "active":
        flags.append("vendor_inactive")
    last4 = node_input.get("bank_account_last4")
    if last4 and last4 != vendor["bank_account_last4"]:
        flags.append("bank_mismatch")
    return Event(
        output={
            "status": "ok",
            "vendor_id": vendor["vendor_id"],
            "vendor_status": vendor["status"],
            "payment_terms": vendor["payment_terms"],
            "flags": flags,
        }
    )


async def check_duplicate(node_input: dict):
    """Has this invoice number been seen before?"""
    try:
        result = await mcp_call.call_tool(
            "erp",
            "get_invoice_status",
            {"invoice_number": node_input["invoice_number"]},
        )
    except ToolError as exc:
        return Event(output={"status": "error", "message": str(exc)})
    if result.get("status") == "found":
        return Event(output={"status": "duplicate", "existing": result["invoices"]})
    return Event(output={"status": "no_duplicate"})


async def check_po(node_input: dict):
    """Compare the invoice with its purchase order, in code."""
    po_number = node_input.get("po_number")
    if not po_number:
        return Event(output={"status": "no_po", "flags": ["no_po"], "findings": []})
    try:
        result = await mcp_call.call_tool(
            "erp", "lookup_purchase_order", {"po_number": po_number}
        )
    except ToolError as exc:
        return Event(output={"status": "error", "message": str(exc)})
    if result.get("status") != "found":
        return Event(
            output={"status": "po_not_found", "flags": ["po_not_found"], "findings": []}
        )
    comparison = compare_invoice_to_po(node_input["line_items"], result["lines"])
    return Event(
        output={
            "status": "ok",
            "flags": [],
            "findings": comparison["findings"],
            "match_status": comparison["match_status"],
        }
    )


def score_risk(node_input: dict, ctx: Context):
    """Turn the three check results into one decision."""
    invoice = ctx.state.get("invoice") or {}
    result = assess(invoice, node_input)
    case = {"invoice": invoice, "checks": node_input, **result}
    state = {"case": case, "decision": result["decision"]}
    if result["decision"] == "AUTO_APPROVE":
        state["final_decision"] = "AUTO_APPROVE"
    return Event(output=case, route=result["decision"], state=state)


def gate(node_input, ctx: Context):
    """Holds end here; everything else needs a human answer."""
    summary = _as_dict(node_input)
    if ctx.state.get("decision") == "HOLD":
        return Event(
            output=summary,
            route="DONE",
            state={"summary": summary, "final_decision": "HOLD"},
        )
    return Event(output=summary, route="ASK_HUMAN", state={"summary": summary})


def _approval_prompt(summary: dict, case: dict) -> str:
    lines = [summary.get("headline", "Invoice needs approval"), ""]
    lines += [f"- {item}" for item in summary.get("details", [])]
    flags = ", ".join(case.get("flags", [])) or "none"
    lines += [
        "",
        f"Flags: {flags}",
        f"Recommendation: {summary.get('recommendation', 'n/a')}",
        "",
        "Reply 'approve' or 'reject', optionally with a reason.",
    ]
    return "\n".join(lines)


def request_approval(ctx: Context):
    """Pause the run until a person answers."""
    case = ctx.state.get("case") or {}
    summary = ctx.state.get("summary") or {}
    invoice = case.get("invoice", {})
    yield RequestInput(
        message=_approval_prompt(summary, case),
        payload={
            "invoice_number": invoice.get("invoice_number"),
            "total_amount": invoice.get("total_amount"),
            "flags": case.get("flags", []),
        },
        response_schema=str,
    )


APPROVE_WORDS = {"approve", "approved", "yes"}
REJECT_WORDS = {"reject", "rejected", "no"}


def interpret_decision(node_input: str, ctx: Context):
    """Read the approver's reply. Unclear replies loop; max 3."""
    reply = str(node_input).strip()
    words = reply.lower().split()
    word = words[0].strip(".,:;!") if words else ""
    attempts = int(ctx.state.get("approval_attempts") or 0) + 1
    if word in APPROVE_WORDS:
        verdict = "APPROVED"
    elif word in REJECT_WORDS:
        verdict = "REJECTED"
    elif attempts >= MAX_APPROVAL_ATTEMPTS:
        verdict = "REJECTED"  # fail closed
    else:
        return Event(
            output=reply, route="UNCLEAR", state={"approval_attempts": attempts}
        )
    return Event(
        output=reply,
        route=verdict,
        state={
            "final_decision": verdict,
            "approval_comment": reply,
            "approval_attempts": attempts,
        },
    )


LABELS = {
    "AUTO_APPROVE": "APPROVED_AUTOMATICALLY",
    "APPROVED": "APPROVED_BY_HUMAN",
    "REJECTED": "REJECTED_BY_HUMAN",
    "HOLD": "ON_HOLD",
}
NEXT_STEP = {
    "APPROVED_AUTOMATICALLY": "Ready for payment processing.",
    "APPROVED_BY_HUMAN": "Ready for payment processing.",
    "ON_HOLD": "Do not pay. Verify with the vendor out of band.",
    "REJECTED_BY_HUMAN": "Do not pay.",
}


def finalize(ctx: Context):
    """One exit for every decision. Missing decision means rejected."""
    key = ctx.state.get("final_decision") or "REJECTED"
    label = LABELS.get(key, "REJECTED_BY_HUMAN")
    invoice = ctx.state.get("invoice") or {}
    case = ctx.state.get("case") or {}
    flags = case.get("flags", [])
    text = (
        f"Invoice {invoice.get('invoice_number', '?')}: "
        f"{label.replace('_', ' ').title()}. {NEXT_STEP[label]}"
    )
    if flags:
        text += f" Flags: {', '.join(flags)}."
    yield Event(message=text)
    yield Event(
        output={
            "decision": label,
            "flags": flags,
            "invoice_number": invoice.get("invoice_number"),
        }
    )
