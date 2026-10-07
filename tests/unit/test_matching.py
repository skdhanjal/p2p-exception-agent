from app.matching import compare_invoice_to_po

FREIGHT = "Pallet freight Mumbai-Delhi"
PO_LINES = [
    {
        "line_no": 1,
        "description": FREIGHT,
        "quantity": 10,
        "unit_price": 1600.0,
        "received_qty": 10,
    },
    {
        "line_no": 2,
        "description": "Handling fee",
        "quantity": 10,
        "unit_price": 25.0,
        "received_qty": 10,
    },
]


def line(desc, qty, price):
    return {
        "description": desc,
        "quantity": qty,
        "unit_price": price,
        "line_total": qty * price,
    }


def test_clean_invoice_matches():
    lines = [line(FREIGHT, 10, 1600.0), line("Handling fee", 10, 25.0)]
    result = compare_invoice_to_po(lines, PO_LINES)
    assert result["match_status"] == "matched"


def test_price_mismatch_reports_variance():
    lines = [line(FREIGHT, 10, 1800.0), line("Handling fee", 10, 25.0)]
    finding = compare_invoice_to_po(lines, PO_LINES)["findings"][0]
    assert finding["type"] == "price_mismatch"
    assert finding["variance_amount"] == 2000.0


def test_billed_more_than_received():
    po = [
        {
            "line_no": 1,
            "description": "Ergonomic chair",
            "quantity": 20,
            "unit_price": 180.0,
            "received_qty": 15,
        }
    ]
    result = compare_invoice_to_po([line("Ergonomic chair", 20, 180.0)], po)
    assert result["findings"][0]["type"] == "quantity_exceeds_received"


def test_unknown_line_is_flagged():
    lines = [line("Gold plating", 1, 99.0)]
    result = compare_invoice_to_po(lines, PO_LINES)
    assert result["findings"][0]["type"] == "line_not_on_po"
