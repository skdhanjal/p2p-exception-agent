"""Record an approval decision with your own identity."""

import argparse
import json
import os
import subprocess

import httpx


def my_token() -> str:
    return subprocess.check_output(
        ["gcloud", "auth", "print-identity-token"], text=True
    ).strip()


def record(payload: dict, decision: str, comment: str = "") -> str:
    """Record a decision for a paused case; return its approval id."""
    body = {
        "invoice_number": payload["invoice_number"],
        "vendor_id": payload["vendor_id"],
        "amount": payload["total_amount"],
        "currency": payload["currency"],
        "decision": decision,
        "comment": comment[:200],
    }
    token = my_token()
    print('Access token', token)
    reply = httpx.post(
        f"{os.environ['APPROVALS_URL']}/decisions",
        json=body,
        timeout=60,
        headers={"Authorization": f"Bearer {token}"},
    )
    reply.raise_for_status()
    return reply.json()["approval_id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--payload", required=True, help="JSON from the approval request"
    )
    parser.add_argument("--decision", default="approved")
    parser.add_argument("--comment", default="")
    args = parser.parse_args()
    print(record(json.loads(args.payload), args.decision, args.comment))
