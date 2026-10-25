"""Fail if the extraction report is below the Phase 5 gates."""

import json
import sys

from evals import gates

report = json.load(open("evals/reports/extraction_report.json"))
problems = []
if report["strict_valid_rate"] < gates.EXTRACTION["strict_valid_rate"]:
    problems.append("strict_valid_rate")
if report["po_hallucinations"] > gates.EXTRACTION["po_hallucinations"]:
    problems.append("po_hallucinations")
if report["id_amount_accuracy"] < gates.EXTRACTION["id_amount_accuracy"]:
    problems.append("id_amount_accuracy")
print("extraction gates:", problems or "pass")
sys.exit(1 if problems else 0)
