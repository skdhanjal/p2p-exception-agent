"""Run every case through the real graph. Offline and deterministic."""

import asyncio
import json
from collections import defaultdict
from pathlib import Path

from evals.cases import all_cases
from evals.harness import fake_erp_calls, run_case

REPORT = Path("evals/reports/decision_report.json")


async def run_all() -> list[dict]:
    rows = []
    with fake_erp_calls():
        for case in all_cases():
            rows.append({"case": case, "got": await run_case(case)})
    return rows


def summarize(rows: list[dict]) -> dict:
    by_category = defaultdict(lambda: [0, 0])
    mismatches, violations, flag_misses = [], [], []
    observed = defaultdict(int)
    for row in rows:
        case, got = row["case"], row["got"]
        observed[got["observed"]] += 1
        ok = got["observed"] == case.expected
        by_category[case.category][0] += ok
        by_category[case.category][1] += 1
        if not ok:
            mismatches.append(
                f"{case.case_id}: expected {case.expected}, got {got['observed']}"
            )
        if case.must_not_pay and got["paid"]:
            violations.append(case.case_id)
        if case.flags and not case.flags <= got["flags"]:
            missing = sorted(case.flags - got["flags"])
            flag_misses.append(f"{case.case_id}: missing {missing}")
    total = len(rows)
    with_flags = sum(1 for r in rows if r["case"].flags)
    scores = {k: f"{v[0]}/{v[1]}" for k, v in by_category.items()}
    return {
        "total": total,
        "accuracy": 1 - len(mismatches) / total,
        "flag_recall": 1 - len(flag_misses) / max(with_flags, 1),
        "safety_violations": violations,
        "mismatches": mismatches,
        "flag_misses": flag_misses,
        "by_category": scores,
        "auto_approval_rate": observed["AUTO_APPROVE"] / total,
        "human_queue_rate": observed["NEEDS_APPROVAL"] / total,
        "hold_rate": observed["HOLD"] / total,
    }


def main() -> None:
    summary = summarize(asyncio.run(run_all()))
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(summary, indent=2))
    print(
        f"cases: {summary['total']}   "
        f"accuracy: {summary['accuracy']:.1%}   "
        f"safety violations: {len(summary['safety_violations'])}"
    )
    for name, score in sorted(summary["by_category"].items()):
        print(f"  {name:20} {score}")
    for item in summary["mismatches"] + summary["flag_misses"]:
        print("  MISMATCH", item)
    for case_id in summary["safety_violations"]:
        print("  SAFETY VIOLATION: paid", case_id)
    print(
        f"auto {summary['auto_approval_rate']:.0%}  "
        f"human {summary['human_queue_rate']:.0%}  "
        f"hold {summary['hold_rate']:.0%}"
    )


if __name__ == "__main__":
    main()
