"""Pure parsing of an approver's reply. Fails closed."""

import re

APPROVE_WORDS = {"approve", "approved", "yes"}
REJECT_WORDS = {"reject", "rejected", "no", "deny", "denied"}
HEDGES = {
    "not",
    "never",
    "unless",
    "but",
    "however",
    "except",
    "only",
    "if",
    "maybe",
    "unsure",
    "dont",
    "don't",
    "cant",
    "can't",
    "cannot",
}


def parse_reply(reply: str) -> str:
    """Return APPROVED, REJECTED, or UNCLEAR."""
    tokens = re.findall(r"[a-z']+", reply.lower())
    if not tokens:
        return "UNCLEAR"
    first, rest = tokens[0], tokens[1:]
    if first in REJECT_WORDS:
        return "REJECTED"
    if first in APPROVE_WORDS:
        if any(t in REJECT_WORDS or t in HEDGES for t in rest):
            return "UNCLEAR"
        return "APPROVED"
    return "UNCLEAR"
