import asyncio

from evals import gates
from evals.decision_eval import run_all, summarize


def test_decision_evaluation_meets_the_gates():
    summary = summarize(asyncio.run(run_all()))
    assert summary["safety_violations"] == [], summary["safety_violations"]
    assert summary["accuracy"] >= gates.DECISION["accuracy"], summary["mismatches"]
    assert summary["flag_recall"] >= gates.DECISION["flag_recall"], summary[
        "flag_misses"
    ]
