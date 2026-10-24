from evals.cases import all_cases
from evals.extraction_eval import score


def clean():
    return next(c for c in all_cases() if c.category == "clean").invoice


def test_a_perfect_extraction_scores_perfectly():
    inv = clean()
    results = score(inv, dict(inv))
    assert all(v for k, v in results.items() if k != "po_hallucination")
    assert results["po_hallucination"] is False


def test_a_wrong_amount_and_a_made_up_po_are_caught():
    inv = clean()
    got = {**inv, "total_amount": inv["total_amount"] + 5}
    assert score(inv, got)["total_amount"] is False
    no_po = {**inv, "po_number": None}
    made_up = {**inv, "po_number": "PO-1234"}
    assert score(no_po, made_up)["po_hallucination"] is True


def test_name_case_and_line_changes():
    inv = clean()
    got = {**inv, "vendor_name": inv["vendor_name"].upper()}
    assert score(inv, got)["vendor_name"] is True
    got["line_items"] = []
    assert score(inv, got)["line_items"] is False
