"""Calls the Payments MCP server with a Cloud Run ID token."""

import asyncio
import os

from fastmcp import Client
from google.auth.transport.requests import Request
from google.oauth2 import id_token


def _token(audience: str) -> str:
    return id_token.fetch_id_token(Request(), audience) # type: ignore


async def call_payments_tool(tool: str, args: dict) -> dict:
    local = os.environ.get("LOCAL_MCP_PAYMENTS_URL")
    if local:  # authenticated proxy on your laptop
        url, token = local, None
    else:
        url = os.environ["PAYMENTS_MCP_URL"]  # ends with /mcp
        audience = url.removesuffix("/mcp")
        token = await asyncio.to_thread(_token, audience)
    async with Client(url, auth=token) as client:
        result = await client.call_tool(tool, args)
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    return dict(result.structured_content or {})
