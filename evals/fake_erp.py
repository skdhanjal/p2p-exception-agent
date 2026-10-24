"""An in-memory ERP that behaves like the MCP servers (seed data)."""

from fastmcp.exceptions import ToolError

from app import ids

VENDORS = [
    {
        "vendor_id": "V-1001",
        "name": "Acme Supplies",
        "status": "active",
        "bank_account_last4": "4821",
        "payment_terms": "NET30",
    },
    {
        "vendor_id": "V-1002",
        "name": "Globex Logistics",
        "status": "active",
        "bank_account_last4": "1190",
        "payment_terms": "NET45",
    },
    {
        "vendor_id": "V-1003",
        "name": "Initech Office Goods",
        "status": "active",
        "bank_account_last4": "7733",
        "payment_terms": "NET30",
    },
    {
        "vendor_id": "V-1004",
        "name": "Umbrella Industrial",
        "status": "on_hold",
        "bank_account_last4": "5502",
        "payment_terms": "NET60",
    },
]
FREIGHT = "Pallet freight Mumbai-Delhi"
POS = {
    "PO-7701": {
        "header": {
            "po_number": "PO-7701",
            "vendor_id": "V-1001",
            "currency": "USD",
            "total_amount": 420.0,
            "status": "open",
        },
        "lines": [
            {
                "line_no": 1,
                "description": "A4 paper ream",
                "quantity": 100.0,
                "unit_price": 4.2,
                "received_qty": 100.0,
            }
        ],
    },
    "PO-7781": {
        "header": {
            "po_number": "PO-7781",
            "vendor_id": "V-1002",
            "currency": "USD",
            "total_amount": 16250.0,
            "status": "open",
        },
        "lines": [
            {
                "line_no": 1,
                "description": FREIGHT,
                "quantity": 10.0,
                "unit_price": 1600.0,
                "received_qty": 10.0,
            },
            {
                "line_no": 2,
                "description": "Handling fee",
                "quantity": 10.0,
                "unit_price": 25.0,
                "received_qty": 10.0,
            },
        ],
    },
    "PO-7790": {
        "header": {
            "po_number": "PO-7790",
            "vendor_id": "V-1003",
            "currency": "USD",
            "total_amount": 3600.0,
            "status": "open",
        },
        "lines": [
            {
                "line_no": 1,
                "description": "Ergonomic chair",
                "quantity": 20.0,
                "unit_price": 180.0,
                "received_qty": 15.0,
            }
        ],
    },
}
INVOICES = [
    {
        "invoice_number": "INV-1001",
        "vendor_id": "V-1001",
        "po_number": "PO-7650",
        "total_amount": 420.0,
        "status": "approved",
        "hold_reason": None,
    },
    {
        "invoice_number": "INV-1002",
        "vendor_id": "V-1002",
        "po_number": "PO-7600",
        "total_amount": 18250.0,
        "status": "on_hold",
        "hold_reason": "Price mismatch with PO-7600",
    },
    {
        "invoice_number": "INV-1003",
        "vendor_id": "V-1004",
        "po_number": "PO-7702",
        "total_amount": 9800.0,
        "status": "on_hold",
        "hold_reason": "Vendor under review",
    },
    {
        "invoice_number": "INV-5521",
        "vendor_id": "V-1003",
        "po_number": "PO-7688",
        "total_amount": 1250.0,
        "status": "paid",
        "hold_reason": None,
    },
]


def _require(kind: str, value) -> None:
    if not ids.is_valid(kind, value):
        raise ToolError(f"{kind} has an invalid format")


async def call_tool(server: str, tool: str, args: dict) -> dict:
    """Same signature as app.mcp_call.call_tool."""
    if tool == "lookup_vendor":
        _require("vendor_name", args["vendor_name"])
        pattern = args["vendor_name"].strip().lower()
        rows = [v for v in VENDORS if pattern in v["name"].lower()]
        if not rows:
            return {"status": "not_found", "vendor_name": args["vendor_name"]}
        return {"status": "found", "vendors": rows[:5]}
    if tool == "get_invoice_status":
        _require("invoice_number", args["invoice_number"])
        rows = [i for i in INVOICES if i["invoice_number"] == args["invoice_number"]]
        if not rows:
            return {"status": "not_found", "invoice_number": args["invoice_number"]}
        return {"status": "found", "invoices": rows[:5]}
    if tool == "lookup_purchase_order":
        _require("po_number", args["po_number"])
        po = POS.get(args["po_number"])
        if po is None:
            return {"status": "not_found", "po_number": args["po_number"]}
        return {"status": "found", "purchase_order": po["header"], "lines": po["lines"]}
    raise AssertionError(f"unexpected tool {tool}")
