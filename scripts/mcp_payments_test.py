"""Exercise the payments tool: valid, invalid, dry run, replay."""

import asyncio
import uuid

from fastmcp import Client
from fastmcp.exceptions import ToolError

URL = "http://127.0.0.1:8083/mcp"
BASE = {
    "invoice_number": "INV-1001",
    "vendor_id": "V-1001",
    "amount": 420.0,
    "currency": "USD",
    "approval_id": "APR-000001",
}


async def attempt(client, label, **overrides):
    args = {**BASE, "idempotency_key": uuid.uuid4().hex, **overrides}
    try:
        result = await client.call_tool("request_payment", args)
        print(f"{label}: OK -> {result.data}")
    except ToolError as exc:
        print(f"{label}: REJECTED -> {exc}")


async def main():
    async with Client(URL) as client:
        await attempt(client, "1 dry run (default)")
        await attempt(client, "2 wrong amount", amount=999.0)
        await attempt(
            client,
            "3 held invoice",
            invoice_number="INV-1002",
            vendor_id="V-1002",
            amount=18250.0,
        )
        await attempt(client, "4 bad approval id", approval_id="trust-me")
        key = "replay-" + uuid.uuid4().hex[:12]
        await attempt(client, "5 real request", dry_run=False, idempotency_key=key)
        await attempt(client, "6 same key again", dry_run=False, idempotency_key=key)


asyncio.run(main())
