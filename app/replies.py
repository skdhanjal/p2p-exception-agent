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


APPROVAL_ID = re.compile(r"\bAPR-\d{6}\b")
RESERVED = "APR-000000"  # policy approvals cannot come from a human


def approval_id_in(reply: str) -> str | None:
    match = APPROVAL_ID.search(reply.upper())
    if match and match.group(0) != RESERVED:
        return match.group(0)
    return None


def parse_with_id(reply: str) -> tuple[str, str | None]:
    """An approval counts only if it names a recorded approval id."""
    verdict = parse_reply(reply)
    approval_id = approval_id_in(reply)
    if verdict == "APPROVED" and approval_id is None:
        return "UNCLEAR", None
    return verdict, approval_id if verdict == "APPROVED" else None


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
