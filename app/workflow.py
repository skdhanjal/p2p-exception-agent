"""The invoice workflow graph."""
from google.adk import Workflow
from google.adk.workflow import DEFAULT_ROUTE, FunctionNode, JoinNode, RetryConfig

from app import nodes

TRANSIENT = ["ConnectError", "ReadTimeout", "TimeoutException",
             "ConnectionError", "TimeoutError", "NodeTimeoutError"]


def _check(func, name: str) -> FunctionNode:
    """A check node with a timeout and retries for transient errors."""
    return FunctionNode(
        func=func, name=name, timeout=30,
        retry_config=RetryConfig(
            max_attempts=3, initial_delay=1.0, jitter=0.25,
            exceptions=TRANSIENT), # type: ignore
    )


def build_workflow(extract, summarize, qa) -> Workflow:
    """Build the graph. The three LLM nodes are injected."""
    check_vendor = _check(nodes.check_vendor, "check_vendor")
    check_duplicate = _check(nodes.check_duplicate, "check_duplicate")
    check_po = _check(nodes.check_po, "check_po")
    join = JoinNode(name="join")
    return Workflow(name="invoice_workflow", edges=[
        ("START", nodes.route_request),
        (nodes.route_request, {
            "INVOICE": extract,
            "QUESTION": qa,
            DEFAULT_ROUTE: qa,
        }),
        (extract, nodes.validate_invoice),
        (nodes.validate_invoice, {
            "VALID": nodes.dispatch,
            "INVALID": nodes.escalate_invalid,
            DEFAULT_ROUTE: nodes.escalate_invalid,
        }),
        (nodes.dispatch, check_vendor, join),
        (nodes.dispatch, check_duplicate, join),
        (nodes.dispatch, check_po, join),
        (join, nodes.score_risk),
        (nodes.score_risk, {
            "AUTO_APPROVE": nodes.finalize,
            "NEEDS_APPROVAL": summarize,
            "HOLD": summarize,
            DEFAULT_ROUTE: summarize,
        }),
        (summarize, nodes.gate),
        (nodes.gate, {
            "ASK_HUMAN": nodes.request_approval,
            "DONE": nodes.finalize,
            DEFAULT_ROUTE: nodes.request_approval,
        }),
        (nodes.request_approval, nodes.interpret_decision),
        (nodes.interpret_decision, {
            "APPROVED": nodes.finalize,
            "REJECTED": nodes.finalize,
            "UNCLEAR": nodes.request_approval,
            DEFAULT_ROUTE: nodes.finalize,
        }),
    ])
