"""Prove that preferences persist across sessions using Memory Bank."""

import asyncio
import os

import agentplatform
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ["REGION"]
APP_NAME = "p2p-memory-demo"
USER_ID = "approver-1"


def get_memory_bank_id() -> str:
    existing = os.environ.get("MEMORY_BANK_ID")
    if existing:
        return existing
    client = agentplatform.Client(project=PROJECT, location=REGION) # type: ignore
    bank = client.memory_banks.create()
    bank_id = bank.name.split("/")[-1]
    print(f"Created Memory Bank {bank_id}. Export MEMORY_BANK_ID to reuse.")
    return bank_id


async def ask(runner, session_id, text):
    message = types.Content(role="user", parts=[types.Part(text=text)])
    print("\nUSER:", text)
    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=message
    ):
        if event.is_final_response() and event.content:
            print("AGENT:", event.content.parts[0].text)


async def main():
    memory_service = VertexAiMemoryBankService(
        project=PROJECT,
        location=REGION,
        agent_engine_id=get_memory_bank_id(),
    )
    sessions = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=sessions,
        memory_service=memory_service,
    )

    first = await sessions.create_session(app_name=APP_NAME, user_id=USER_ID)
    await ask(
        runner,
        first.id,
        "For my approvals: always show vendor payment terms, and "
        "flag anything over 10,000 USD for my manager.",
    )

    print("\nWaiting 30 seconds for memory generation...")
    await asyncio.sleep(30)
    found = await memory_service.search_memory(
        app_name=APP_NAME, user_id=USER_ID, query="approver preferences"
    )
    for memory in found.memories:
        print("MEMORY:", memory.content.parts[0].text) # type: ignore

    second = await sessions.create_session(app_name=APP_NAME, user_id=USER_ID)
    await ask(
        runner, second.id, "What are my standing preferences when you review invoices?"
    )


asyncio.run(main())
