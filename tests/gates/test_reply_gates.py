from app.replies import parse_reply
from evals import gates
from evals.reply_cases import CASES


def test_nothing_unclear_is_ever_approved():
    bad = [
        r
        for r, allowed in CASES
        if "APPROVED" not in allowed and parse_reply(r) == "APPROVED"
    ]
    assert bad == []


def test_every_reply_lands_in_an_allowed_outcome():
    wrong = [
        (r, parse_reply(r)) for r, allowed in CASES if parse_reply(r) not in allowed
    ]
    assert wrong == []


def test_real_approvals_rarely_need_clarification():
    approvals = [r for r, allowed in CASES if allowed == {"APPROVED"}]
    unclear = [r for r in approvals if parse_reply(r) == "UNCLEAR"]
    rate = len(unclear) / len(approvals)
    assert rate <= gates.REPLIES["max_clarification_rate"]
