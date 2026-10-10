"""List MCP servers in Agent Registry; optionally show one record."""

import json
import os
import sys

from google.adk.integrations.agent_registry import AgentRegistry

registry = AgentRegistry(
    project_id=os.environ["PROJECT_ID"], location=os.environ["REGION"]
)
for server in registry.list_mcp_servers().get("mcpServers", []):
    print(server.get("name"), "|", server.get("displayName"))

if len(sys.argv) > 1:
    print(json.dumps(registry.get_mcp_server(sys.argv[1]), indent=2))
    print(registry.get_mcp_toolset(mcp_server_name=sys.argv[1]))
