"""Send one instruction to the payments executor over A2A."""

import asyncio
import json
import os
import subprocess
import sys

import httpx
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)
from google.adk.runners import InMemoryRunner
from google.genai import types

BASE = os.environ.get("A2A_PAYMENTS_AGENT_URL", "http://localhost:8090")

INSTRUCTION = {
    "invoice_number": "INV-1001",
    "vendor_id": "V-1001",
    "po_number": "PO-7650",
    "amount": 420.0,
    "currency": "USD",
    "approval_id": "APR-000000",
    "idempotency_key": "V-1001-INV-1001-probe",
    "dry_run": False,
}


def auth_headers() -> dict:
    if os.environ.get("USE_GCLOUD_TOKEN"):
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], text=True
        ).strip()
        return {"Authorization": f"Bearer {token}"}
    return {}


async def main(instruction: dict) -> None:
    agent = RemoteA2aAgent(
        name="payments_executor",
        description="Executes approved payments.",
        agent_card=f"{BASE}{AGENT_CARD_WELL_KNOWN_PATH}",
        httpx_client=httpx.AsyncClient(headers=auth_headers(), timeout=90),
    )
    runner = InMemoryRunner(agent=agent, app_name="a2a-probe")
    session = await runner.session_service.create_session(
        app_name="a2a-probe", user_id="probe"
    )
    message = types.Content(
        role="user", parts=[types.Part(text=json.dumps(instruction))]
    )
    async for event in runner.run_async(
        user_id="probe", session_id=session.id, new_message=message
    ):
        for part in event.content.parts if event.content else []: # type: ignore
            if part.text:
                print(f"[{event.author}] {part.text}")


if __name__ == "__main__":
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else INSTRUCTION
    asyncio.run(main(payload))
