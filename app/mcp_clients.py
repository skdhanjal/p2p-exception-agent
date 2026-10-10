"""Builds the MCP toolsets the agent uses, preferring the registry."""

import os
from urllib.parse import urlparse

import google.auth
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app import config


def _project_id() -> str:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    return project or google.auth.default()[1]  # type: ignore


def _first_url(server: dict) -> str:
    for interface in server.get("interfaces", []):
        if interface.get("url"):
            return interface["url"]
    raise RuntimeError(
        "No endpoint URL in the registry record. Print the record with "
        "scripts/registry_discovery.py and adjust _first_url()."
    )


def _audience(url: str) -> str:
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"


def _id_token_headers(audience: str):
    """Header provider that attaches a Cloud Run ID token."""

    def provider(context) -> dict:
        token = id_token.fetch_id_token(Request(), audience)
        return {"Authorization": f"Bearer {token}"}

    return provider


def _registry_toolset(server_id: str) -> McpToolset:
    project, location = _project_id(), config.REGISTRY_LOCATION
    name = f"projects/{project}/locations/{location}/mcpServers/{server_id}"
    probe = AgentRegistry(project_id=project, location=location)
    audience = _audience(_first_url(probe.get_mcp_server(name)))
    registry = AgentRegistry(
        project_id=project,
        location=location,
        header_provider=_id_token_headers(audience),
    )
    return registry.get_mcp_toolset(mcp_server_name=name)


def build_toolsets() -> list[McpToolset]:
    erp = os.environ.get("LOCAL_MCP_ERP_URL")
    vendor = os.environ.get("LOCAL_MCP_VENDOR_URL")
    if erp and vendor:
        return [
            McpToolset(connection_params=StreamableHTTPConnectionParams(url=url))
            for url in (erp, vendor)
        ]
    return [
        _registry_toolset(config.ERP_SERVER_ID),
        _registry_toolset(config.VENDOR_SERVER_ID),
    ]
