"""Deterministic calls to the payments executor over A2A."""

import json
import time

import httpx
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)
from google.adk.runners import InMemoryRunner
from google.auth.transport.requests import Request
from google.genai import types
from google.oauth2 import id_token

from app import config


class CloudRunAuth(httpx.Auth):
    """Attach a Cloud Run ID token, refreshed before it expires."""

    def __init__(self, audience: str):
        self.audience = audience
        self._token = None
        self._expires = 0.0

    def _fresh(self) -> str | None:
        if self._token is None or time.time() > self._expires:
            self._token = id_token.fetch_id_token(Request(), self.audience)
            self._expires = time.time() + 45 * 60
        return self._token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._fresh()}"
        yield request


def parse_reply(texts: list[str]) -> dict:
    """The last text part that is a JSON object wins."""
    for text in reversed(texts):
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return {"status": "error", "reason": "no readable reply"}


async def send_instruction(instruction: dict) -> dict:
    base = config.PAYMENTS_AGENT_URL.rstrip("/")
    auth = None if base.startswith("http://") else CloudRunAuth(base)
    async with httpx.AsyncClient(auth=auth, timeout=90) as client:
        agent = RemoteA2aAgent(
            name="payments_executor",
            description="Executes approved payments.",
            agent_card=f"{base}{AGENT_CARD_WELL_KNOWN_PATH}",
            httpx_client=client,
        )
        runner = InMemoryRunner(agent=agent, app_name="payments-client")
        session = await runner.session_service.create_session(
            app_name="payments-client", user_id="workflow"
        )
        message = types.Content(
            role="user", parts=[types.Part(text=json.dumps(instruction))]
        )
        texts: list[str] = []
        async for event in runner.run_async(
            user_id="workflow", session_id=session.id, new_message=message
        ):
            for part in event.content.parts if event.content else []:  # type: ignore
                if part.text:
                    texts.append(part.text)
    return parse_reply(texts)
