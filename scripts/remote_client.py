"""Talk to a deployed agent: upload an invoice, answer approvals."""

import argparse
import asyncio
import base64
import json
import os
from pathlib import Path

import google.auth
import google.auth.transport.requests
import httpx

USER = "approver-1"


def headers() -> dict:
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(google.auth.transport.requests.Request())
    return {"Authorization": f"Bearer {creds.token}"}


def base_url(resource: str) -> str:
    region = os.environ["REGION"]
    return f"https://{region}-aiplatform.googleapis.com/v1/{resource}"


def text_message(text: str) -> dict:
    return {"role": "user", "parts": [{"text": text}]}


def pdf_message(path: str) -> dict:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return {
        "role": "user",
        "parts": [
            {"text": "Process this invoice."},
            {"inline_data": {"mime_type": "application/pdf", "data": data}},
        ],
    }


def answer_message(call_id: str, text: str) -> dict:
    return {
        "role": "user",
        "parts": [
            {
                "function_response": {
                    "id": call_id,
                    "name": "adk_request_input",
                    "response": {"result": text},
                }
            }
        ],
    }


async def create_session(client, url: str) -> str:
    body = {"class_method": "async_create_session", "input": {"user_id": USER}}
    reply = await client.post(f"{url}:query", headers=headers(), json=body)
    reply.raise_for_status()
    return reply.json()["output"]["id"]


async def stream(client, url: str, session_id: str, message: dict):
    body = {
        "class_method": "async_stream_query",
        "input": {"user_id": USER, "session_id": session_id, "message": message},
    }
    async with client.stream(
        "POST", f"{url}:streamQuery?alt=sse", headers=headers(), json=body
    ) as reply:
        reply.raise_for_status()
        async for line in reply.aiter_lines():
            line = line.removeprefix("data:").strip()
            if line:
                yield json.loads(line)


def pick(obj: dict, *names):
    """Field lookup that tolerates snake_case and camelCase."""
    for name in names:
        if name in obj:
            return obj[name]
    return None


def parts_of(event: dict) -> list:
    content = pick(event, "content") or {}
    return pick(content, "parts") or []


async def run(url: str, session_id: str, message: dict) -> tuple:
    """Send one message. Returns (texts, pause_call_or_None)."""
    texts, pause = [], None
    async with httpx.AsyncClient(timeout=300) as client:
        async for event in stream(client, url, session_id, message):
            for part in parts_of(event):
                if part.get("text"):
                    texts.append(part["text"])
                call = pick(part, "function_call", "functionCall")
                if call and call.get("name") == "adk_request_input":
                    pause = call
    return texts, pause


async def main(args) -> None:
    url = base_url(args.resource)
    async with httpx.AsyncClient(timeout=300) as client:
        session_id = args.session or await create_session(client, url)
    if args.resume:
        message = answer_message(args.call_id, args.reply)
    elif args.file:
        message = pdf_message(args.file)
    else:
        message = text_message(args.text)
    print(f"session: {session_id}")
    while message is not None:
        texts, pause = await run(url, session_id, message)
        for text in texts:
            print(text)
        message = None
        if pause is not None:
            call_id = pause.get("id")
            print(f"\nPAUSED  session={session_id}  call_id={call_id}")
            if args.interactive:
                reply_text = input("> ")
                if reply_text.strip().lower().startswith("approve"):
                    from scripts import approve
                    payload = (pause.get("args") or {}).get("payload", {})
                    apr = approve.record(payload[0] if len(payload) > 0  else payload, "approved", reply_text)
                    print(f"recorded as {apr}")
                    reply_text = f"{reply_text} {apr}"

                message = answer_message(call_id, reply_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resource",
        default=os.environ.get("AGENT_RESOURCE", ""),
        help="projects/.../reasoningEngines/ID",
    )
    parser.add_argument("--file", help="invoice PDF to upload")
    parser.add_argument("--text", default="Hello", help="a question")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--session", help="existing session id")
    parser.add_argument(
        "--resume", action="store_true", help="answer a paused approval"
    )
    parser.add_argument("--call-id", help="call id printed at the pause")
    parser.add_argument("--reply", default="approve")
    asyncio.run(main(parser.parse_args()))
