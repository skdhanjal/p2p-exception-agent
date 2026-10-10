"""Structured JSON logs that Cloud Logging understands."""

import json
import sys


def log(severity: str, message: str, **fields) -> None:
    record = {"severity": severity, "message": message, **fields}
    print(json.dumps(record, default=str), file=sys.stdout, flush=True)
