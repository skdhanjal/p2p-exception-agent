"""The payments executor: a non-LLM ADK agent exposed over A2A."""

import json
import os
from collections.abc import AsyncGenerator

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from payments_agent import core
from payments_agent.mcp_call import call_payments_tool

ALLOW_LIVE = os.environ.get("ALLOW_LIVE_PAYMENTS", "false") == "true"


class PaymentsExecutor(BaseAgent):
    """Executes one approved payment instruction. Contains no model."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        parts = (ctx.user_content.parts if ctx.user_content else None) or []
        raw = " ".join(p.text for p in parts if p.text)
        result = await core.execute(raw, call_payments_tool, ALLOW_LIVE)
        yield Event(
            author=self.name,
            content=types.Content(
                role="model", parts=[types.Part(text=json.dumps(result))]
            ),
        )


executor = PaymentsExecutor(
    name="payments_executor",
    description=(
        "Records an approved invoice decision and requests its "
        "payment. Accepts one JSON instruction. Dry run by "
        "default."
    ),
)

a2a_app = to_a2a(
    executor,
    host=os.environ.get("PUBLIC_HOST", "localhost"),
    protocol=os.environ.get("PUBLIC_PROTOCOL", "http"),
    port=int(os.environ.get("PUBLIC_PORT", "8090")),
)
