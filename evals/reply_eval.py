"""Score reply parsers against evals/reply_cases.py."""

from app.replies import parse_reply
from evals.reply_cases import CASES


def legacy_parse(reply: str) -> str:
    """The Phase 3 rule, copied so that it can be measured."""
    words = reply.lower().split()
    word = words[0].strip(".,:;!") if words else ""
    if word in {"approve", "approved", "yes"}:
        return "APPROVED"
    if word in {"reject", "rejected", "no"}:
        return "REJECTED"
    return "UNCLEAR"


def evaluate(parse) -> dict:
    wrong, false_approvals = [], []
    for reply, allowed in CASES:
        got = parse(reply)
        if got not in allowed:
            wrong.append((reply, got))
        if got == "APPROVED" and "APPROVED" not in allowed:
            false_approvals.append(reply)
    approvals = [r for r, a in CASES if a == {"APPROVED"}]
    clarified = [r for r in approvals if parse(r) == "UNCLEAR"]
    return {
        "wrong": wrong,
        "false_approvals": false_approvals,
        "clarification_rate": len(clarified) / len(approvals),
    }


if __name__ == "__main__":
    result = evaluate(parse_reply)
    print(f"false approvals: {len(result['false_approvals'])}")
    for reply in result["false_approvals"]:
        print("   APPROVED:", repr(reply))
    print(f"clarification rate on real approvals: {result['clarification_rate']:.0%}")
