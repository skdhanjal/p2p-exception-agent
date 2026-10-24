"""Measure extraction accuracy on rendered PDFs. Costs model calls."""

import argparse
import asyncio
import json
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents import build_extract_agent
from app.schemas import RawInvoice, validate_invoice
from evals.cases import all_cases
from evals.render import render_invoice

PDF_DIR = Path("evals/reports/pdfs")
REPORT = Path("evals/reports/extraction_report.json")
MONEY = ("subtotal", "tax_amount", "total_amount")
EXACT = (
    "invoice_number",
    "invoice_date",
    "currency",
    "bank_account_last4",
    "po_number",
)


def _norm(text) -> str:
    return " ".join(str(text or "").lower().split())


def _close(a, b) -> bool:
    return a is not None and abs(float(a) - float(b)) <= 0.01


def _lines_match(expected: list, got: list) -> bool:
    if len(expected) != len(got):
        return False
    for e, g in zip(expected, got):
        if _norm(e["description"]) != _norm(g.get("description")):
            return False
        for key in ("quantity", "unit_price", "line_total"):
            if not _close(g.get(key), e[key]):
                return False
    return True


def score(expected: dict, got: dict) -> dict:
    """Field-by-field correctness, plus hallucination checks."""
    results = {
        name: (got.get(name) or None) == (expected.get(name) or None) for name in EXACT
    }
    results["vendor_name"] = _norm(got.get("vendor_name")) == _norm(
        expected["vendor_name"]
    )
    for name in MONEY:
        results[name] = _close(got.get(name), expected[name])
    results["line_items"] = _lines_match(
        expected["line_items"], got.get("line_items") or []
    )
    results["po_hallucination"] = not expected.get("po_number") and bool(
        got.get("po_number")
    )
    return results


async def extract_once(pdf: Path):
    runner = InMemoryRunner(agent=build_extract_agent(), app_name="extract-eval")
    session = await runner.session_service.create_session(
        app_name="extract-eval", user_id="u"
    )
    message = types.Content(
        role="user",
        parts=[
            types.Part(text="Extract this invoice."),
            types.Part.from_bytes(data=pdf.read_bytes(), mime_type="application/pdf"),
        ],
    )
    text = ""
    async for event in runner.run_async(
        user_id="u", session_id=session.id, new_message=message
    ):
        for part in event.content.parts if event.content else []:
            if part.text:
                text = part.text
    try:
        return RawInvoice.model_validate_json(text).model_dump()
    except ValueError:
        return None


def pick_cases(limit: int):
    usable = [c for c in all_cases() if c.expected != "INVALID"]
    step = max(len(usable) // limit, 1)
    return usable[::step][:limit]


async def run(limit: int, repeats: int, concurrency: int) -> dict:
    gate = asyncio.Semaphore(concurrency)
    rows = []

    async def one(index: int, case):
        pdf = PDF_DIR / f"{case.case_id}.pdf"
        render_invoice(case.invoice, pdf, index % 3, case.footer)
        async with gate:
            outputs = [await extract_once(pdf) for _ in range(repeats)]
        rows.append((case, outputs))

    await asyncio.gather(*(one(i, c) for i, c in enumerate(pick_cases(limit))))
    return summarize(rows)


def summarize(rows) -> dict:
    fields: dict[str, list] = {}
    valid = unreadable = hallucinated = stable = total = 0
    for case, outputs in rows:
        for got in outputs:
            total += 1
            if got is None:
                unreadable += 1
                continue
            invoice, errors = validate_invoice(got)
            valid += invoice is not None
            for name, ok in score(case.invoice, got).items():
                if name == "po_hallucination":
                    hallucinated += ok
                else:
                    fields.setdefault(name, []).append(ok)
        if len(outputs) > 1:
            stable += all(o == outputs[0] for o in outputs)
    result = {
        "runs": total,
        "unreadable": unreadable,
        "strict_valid_rate": valid / total,
        "po_hallucinations": hallucinated,
        "field_accuracy": {k: sum(v) / len(v) for k, v in fields.items()},
        "repeat_stability": stable / len(rows),
    }
    ids_and_amounts = [
        result["field_accuracy"][k]
        for k in ("invoice_number", *MONEY)
        if k in result["field_accuracy"]
    ]
    result["id_amount_accuracy"] = (
        sum(ids_and_amounts) / len(ids_and_amounts) if ids_and_amounts else 0.0
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    summary = asyncio.run(run(args.limit, args.repeats, args.concurrency))
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
