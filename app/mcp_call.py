"""Deterministic MCP calls for workflow nodes (no LLM in the loop)."""

import asyncio
import os
from functools import lru_cache

from fastmcp import Client
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app import config
from app.mcp_clients import resolve_endpoint

SERVER_IDS = {"erp": config.ERP_SERVER_ID, "vendor": config.VENDOR_SERVER_ID}


@lru_cache(maxsize=None)
def _endpoint(server: str) -> tuple[str, str]:
    return resolve_endpoint(SERVER_IDS[server])


def _token(audience: str) -> str:
    return id_token.fetch_id_token(Request(), audience)  # type: ignore


async def _connection(server: str) -> tuple[str, str | None]:
    local = os.environ.get(f"LOCAL_MCP_{server.upper()}_URL")
    if local:  # authenticated proxy on your laptop
        return local, None
    url, audience = await asyncio.to_thread(_endpoint, server)
    return url, await asyncio.to_thread(_token, audience)


def _payload(result) -> dict:
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    return dict(result.structured_content or {})


async def call_tool(server: str, tool: str, args: dict) -> dict:
    """Call one tool on one registered MCP server; return a dict."""
    url, token = await _connection(server)
    async with Client(url, auth=token) as client:
        result = await client.call_tool(tool, args)
    return _payload(result)
