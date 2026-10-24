"""Compare the fake ERP with the real MCP servers. Needs the proxies."""

import asyncio

from app import mcp_call
from evals import fake_erp

CALLS = [
    ("vendor", "lookup_vendor", {"vendor_name": "Globex"}),
    ("vendor", "lookup_vendor", {"vendor_name": "acme supplies"}),
    ("vendor", "lookup_vendor", {"vendor_name": "No Such Vendor"}),
    ("erp", "get_invoice_status", {"invoice_number": "INV-5521"}),
    ("erp", "get_invoice_status", {"invoice_number": "INV-0000"}),
    ("erp", "lookup_purchase_order", {"po_number": "PO-7781"}),
    ("erp", "lookup_purchase_order", {"po_number": "PO-7790"}),
    ("erp", "lookup_purchase_order", {"po_number": "PO-9999"}),
]


def norm(value):
    """Floats compare by value; everything else as is."""
    if isinstance(value, dict):
        return {k: norm(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [norm(v) for v in value]
    return round(value, 4) if isinstance(value, float) else value


async def main() -> int:
    bad = 0
    for server, tool, args in CALLS:
        real = norm(await mcp_call.call_tool(server, tool, args))
        fake = norm(await fake_erp.call_tool(server, tool, args))
        same = real == fake
        bad += not same
        print("OK  " if same else "DIFF", tool, args)
        if not same:
            print("   real:", real)
            print("   fake:", fake)
    print(f"{len(CALLS) - bad} of {len(CALLS)} calls agree")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
