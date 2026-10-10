"""Vendor MCP server: read-only vendor master lookup."""

import os

from common import ids
from common.bq import run_query
from common.logs import log
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("p2p-vendor")


@mcp.tool(annotations={"readOnlyHint": True, "idempotentHint": True})
def lookup_vendor(vendor_name: str) -> dict:
    """Find vendors by full or partial name.

    Args:
        vendor_name: The vendor name as written on the invoice.

    Returns:
        status "found" with up to five matching vendors (vendor_id,
        name, status, bank_account_last4, payment_terms), or
        status "not_found".
    """
    if not ids.is_valid("vendor_name", vendor_name):
        raise ToolError("vendor_name has an invalid format")
    log("INFO", "tool_call", tool="lookup_vendor")
    rows = run_query(
        """
        SELECT vendor_id, name, status, bank_account_last4, payment_terms
        FROM `__DATASET__.vendors`
        WHERE LOWER(name) LIKE @pattern
        ORDER BY name
        LIMIT 5
        """,
        {"pattern": f"%{vendor_name.strip().lower()}%"},
    )
    if not rows:
        return {"status": "not_found", "vendor_name": vendor_name}
    return {"status": "found", "vendors": rows}


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
        stateless_http=True,
    )
