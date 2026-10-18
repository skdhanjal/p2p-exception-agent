"""Pure execution logic for the payments executor. No LLM."""

from collections.abc import Awaitable, Callable

from fastmcp.exceptions import ToolError
from pydantic import BaseModel, ValidationError

CallTool = Callable[[str, dict], Awaitable[dict]]


class PaymentInstruction(BaseModel):
    invoice_number: str
    vendor_id: str
    po_number: str = ""
    amount: float
    currency: str
    approval_id: str
    idempotency_key: str
    decision_reason: str = ""
    dry_run: bool = True


async def execute(raw_text: str, call_tool: CallTool, allow_live: bool) -> dict:
    """Validate one instruction, record the decision, request payment."""
    try:
        instruction = PaymentInstruction.model_validate_json(raw_text)
    except ValidationError as exc:
        fields = sorted({str(e["loc"][0]) for e in exc.errors() if e["loc"]})
        return {"status": "rejected", "reason": "invalid instruction", "fields": fields}
    if not instruction.dry_run and not allow_live:
        return {
            "status": "rejected",
            "reason": "live payments are disabled on this executor",
        }
    try:
        recorded = await call_tool(
            "record_invoice_decision",
            {
                "invoice_number": instruction.invoice_number,
                "vendor_id": instruction.vendor_id,
                "total_amount": instruction.amount,
                "status": "approved",
                "po_number": instruction.po_number,
                "reason": instruction.decision_reason[:200],
            },
        )
        payment = await call_tool(
            "request_payment",
            {
                "invoice_number": instruction.invoice_number,
                "vendor_id": instruction.vendor_id,
                "amount": instruction.amount,
                "currency": instruction.currency,
                "approval_id": instruction.approval_id,
                "idempotency_key": instruction.idempotency_key,
                "dry_run": instruction.dry_run,
            },
        )
    except ToolError as exc:
        return {"status": "rejected", "reason": str(exc)}
    return {
        "status": payment.get("status", "unknown"),
        "decision": recorded.get("status"),
        "request": payment.get("request"),
    }
