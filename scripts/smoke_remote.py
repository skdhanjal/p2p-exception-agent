"""Smoke tests against a deployed agent. Prod runs read-only checks."""

import argparse
import asyncio
import random
import sys
from pathlib import Path

from evals.cases import PAPER, invoice, line
from evals.render import render_invoice
from scripts import remote_client as rc


async def ask(url: str, message: dict) -> str:
    session_id = None
    async with rc.httpx.AsyncClient(timeout=300) as client:
        session_id = await rc.create_session(client, url)
    texts, pause = await rc.run(url, session_id, message)
    return " ".join(texts) + (" PAUSED" if pause else "")


def check(name: str, text: str, expect: str, failures: list) -> None:
    ok = expect.lower() in text.lower()
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: expected {expect!r} in {text[:300]!r}")


async def main(resource: str, writes_allowed: bool) -> int:
    url = rc.base_url(resource)
    failures: list = []

    reply = await ask(url, rc.text_message("What is the status of invoice INV-1002?"))
    check("qa: invoice status", reply, "on hold", failures)

    reply = await ask(url, rc.pdf_message("samples/inv_duplicate.pdf"))
    check("duplicate invoice is held", reply, "on hold", failures)

    if writes_allowed:
        number = f"INV-9{random.randint(1000, 9999)}"
        inv = invoice(
            number, "Acme Supplies", "PO-7701", [line(PAPER, 10, 4.20)], bank="4821"
        )
        path = Path(f"evals/reports/smoke-{number}.pdf")
        render_invoice(inv, path, 0)
        reply = await ask(url, rc.pdf_message(str(path)))
        check("clean invoice is approved", reply, "approved automatically", failures)

    for failure in failures:
        print("  ", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource", required=True)
    parser.add_argument(
        "--allow-writes",
        action="store_true",
        help="dev only: includes a clean-invoice test",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.resource, args.allow_writes)))
