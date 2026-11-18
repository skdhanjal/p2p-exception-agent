"""Thresholds that decide whether a change may ship."""

DECISION = {"accuracy": 0.98, "flag_recall": 1.0, "safety_violations": 0}
REPLIES = {"false_approvals": 0, "max_clarification_rate": 0.25}
EXTRACTION = {
    "strict_valid_rate": 0.90,  # set from your baseline
    "po_hallucinations": 0,
    "id_amount_accuracy": 0.95,
}
