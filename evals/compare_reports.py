"""Compare two extraction reports. Usage: baseline.json candidate.json"""

import json
import sys

TOLERANCE = 0.03  # allowed drop in any rate


def main(baseline_path: str, candidate_path: str) -> int:
    old = json.load(open(baseline_path))
    new = json.load(open(candidate_path))
    worse = []
    for key in ("strict_valid_rate", "id_amount_accuracy", "repeat_stability"):
        change = new[key] - old[key]
        print(f"{key:22} {old[key]:.3f} -> {new[key]:.3f} ({change:+.3f})")
        if change < -TOLERANCE:
            worse.append(key)
    if new["po_hallucinations"] > old["po_hallucinations"]:
        worse.append("po_hallucinations")
    for name, score in new["field_accuracy"].items():
        before = old["field_accuracy"].get(name, score)
        if score < before - TOLERANCE:
            worse.append(f"field:{name}")
    print("REGRESSIONS:", worse or "none")
    return 1 if worse else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
