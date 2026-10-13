"""Run the invoice workflow from the command line, with approvals."""

import asyncio
import json
import sys
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import root_agent

USER = "approver-1"


def invoice_message(path: str) -> types.Content:
    data = Path(path).read_bytes()
    return types.Content(
        role="user",
        parts=[
            types.Part(text="Process this invoice."),
            types.Part.from_bytes(data=data, mime_type="application/pdf"),
        ],
    )


def text_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def answer(call, text: str) -> types.Content:
    response = types.FunctionResponse(
        id=call.id, name="adk_request_input", response={"result": text}
    )
    return types.Content(role="user", parts=[types.Part(function_response=response)])


async def main(first: types.Content) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="p2p-cli")
    session = await runner.session_service.create_session(
        app_name="p2p-cli", user_id=USER
    )
    pending = first
    while pending is not None:
        call = None
        async for event in runner.run_async(
            user_id=USER, session_id=session.id, new_message=pending
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"[{event.author}] {part.text}")
            for fc in event.get_function_calls():
                if fc.name == "adk_request_input":
                    call = fc
            if event.output is not None and call is None:
                print(
                    f"[{event.author}] output:",
                    json.dumps(event.output, default=str)[:400],
                )
        pending = None
        if call is not None:
            print("\n--- APPROVAL NEEDED ---")
            print(call.args.get("message"))
            pending = answer(call, input("> "))


if __name__ == "__main__":
    arg = sys.argv[1]
    message = invoice_message(arg) if arg.endswith(".pdf") else text_message(arg)
    asyncio.run(main(message))
