"""Guardrail, audit, and memory callbacks for the intake agent."""

import json
import logging
import re
from copy import deepcopy
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool
from google.genai import types

from app import ids

logger = logging.getLogger("p2p.audit")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

INJECTION_PATTERNS = [
    r"ignore (all |your )?(previous|prior) instructions",
    r"reveal (your )?(system )?(prompt|instructions)",
    r"disregard (the )?(rules|instructions)",
]
LONG_NUMBER = re.compile(r"\b\d{9,18}\b")


def _log(**fields: Any) -> None:
    logger.info(json.dumps(fields, default=str))


def block_obvious_injection(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
    """Input guardrail: refuse clearly manipulative user text."""
    if not llm_request.contents:
        return None
    last = llm_request.contents[-1]
    if last.role != "user":
        return None
    text = " ".join(p.text for p in (last.parts or []) if p.text).lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            _log(
                event="input_blocked",
                pattern=pattern,
                agent=callback_context.agent_name,
            )
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=(
                                "I can't follow instructions that try to change my "
                                "rules. I'm happy to help with invoice questions."
                            )
                        )
                    ],
                )
            )
    return None


def validate_tool_args(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict | None:
    """Reject malformed identifiers before they reach the ERP."""
    for name in ids.RULES:
        if name in args and not ids.is_valid(name, args[name]):
            _log(
                event="tool_args_rejected",
                tool=tool.name,
                argument=name,
                agent=tool_context.agent_name,
            )
            return {
                "status": "invalid_argument",
                "argument": name,
                "message": f"{name} has an invalid format.",
            }
    return None


def audit_tool_result(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: Any,
) -> dict | None:
    """Count and log every tool call. Never logs argument values."""
    count = tool_context.state.get("tool_call_count", 0) + 1
    tool_context.state["tool_call_count"] = count
    status = tool_response.get("status") if isinstance(tool_response, dict) else None
    _log(
        event="tool_call",
        tool=tool.name,
        status=status,
        call_number=count,
        agent=tool_context.agent_name,
    )
    return None  # keep the original tool result


def redact_long_numbers(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """Output guardrail: mask long digit strings such as account numbers."""
    if getattr(llm_response, "partial", False):
        return None
    if not llm_response.content or not llm_response.content.parts:
        return None
    parts = llm_response.content.parts
    if not any(p.text and LONG_NUMBER.search(p.text) for p in parts):
        return None
    new_parts = [deepcopy(p) for p in parts]
    for part in new_parts:
        if part.text:
            part.text = LONG_NUMBER.sub("[REDACTED]", part.text)
    _log(event="output_redacted", agent=callback_context.agent_name)
    return LlmResponse(content=types.Content(role="model", parts=new_parts))


async def save_to_memory(callback_context: CallbackContext) -> None:
    """After each turn, send recent events to the memory service."""
    events = callback_context.session.events[-5:-1]
    try:
        try:
            await callback_context.add_events_to_memory(events=events)
        except NotImplementedError:
            # Some local memory services only accept whole sessions.
            await callback_context.add_session_to_memory()
    except ValueError:
        # No memory service is configured for this run.
        _log(event="memory_service_unavailable")
    return None
