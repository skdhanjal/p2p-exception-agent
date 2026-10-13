"""Deterministic risk assessment. The LLM never decides routes."""

AUTO_APPROVE_LIMIT = 5000.00  # above this, a human must approve

# Flags that stop the process: nothing here may be approved by a click.
BLOCKING = {"duplicate_invoice", "vendor_inactive", "bank_mismatch"}


def assess(invoice: dict, checks: dict) -> dict:
    """Combine check results into flags and one decision."""
    vendor = checks.get("check_vendor", {})
    dup = checks.get("check_duplicate", {})
    po = checks.get("check_po", {})
    flags: list[str] = []

    for label, result in (("vendor", vendor), ("duplicate", dup), ("po", po)):
        if result.get("status") == "error":
            flags.append(f"{label}_check_failed")

    flags += vendor.get("flags", [])
    if dup.get("status") == "duplicate":
        flags.append("duplicate_invoice")
    flags += po.get("flags", [])
    flags += [f["type"] for f in po.get("findings", [])]
    if float(invoice["total_amount"]) > AUTO_APPROVE_LIMIT:
        flags.append("over_auto_approve_limit")

    if any(flag in BLOCKING for flag in flags):
        decision = "HOLD"
    elif flags:
        decision = "NEEDS_APPROVAL"
    else:
        decision = "AUTO_APPROVE"
    return {"decision": decision, "flags": sorted(set(flags))}
