"""Scan log lines on stdin for sensitive data. Prints counts by type."""

import json
import os
import sys
from collections import Counter

from google.cloud import dlp_v2

TYPES = [
    "IBAN_CODE",
    "SWIFT_CODE",
    "CREDIT_CARD_NUMBER",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_BANK_ROUTING_MICR",
]


def main() -> int:
    entries = json.load(sys.stdin)
    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{os.environ['PROJECT_ID']}/locations/global"
    config = {
        "info_types": [{"name": t} for t in TYPES],
        "min_likelihood": dlp_v2.Likelihood.POSSIBLE,
    }
    found: Counter = Counter()
    for entry in entries:
        text = json.dumps(entry.get("jsonPayload") or entry.get("textPayload") or "")[
            :8000
        ]
        response = client.inspect_content(
            request={
                "parent": parent,
                "inspect_config": config,
                "item": {"value": text},
            }
        )
        for finding in response.result.findings:
            found[finding.info_type.name] += 1
    print(f"scanned {len(entries)} entries")
    print(dict(found) if found else "no sensitive data found")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
