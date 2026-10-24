"""Agreement between a human and an LLM judge. Reads evals/labels.csv."""

import csv
from pathlib import Path


def kappa(pairs: list[tuple[int, int]]) -> float:
    """Cohen's kappa for two binary raters."""
    n = len(pairs)
    observed = sum(h == j for h, j in pairs) / n
    h1 = sum(h for h, _ in pairs) / n
    j1 = sum(j for _, j in pairs) / n
    expected = h1 * j1 + (1 - h1) * (1 - j1)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def main(path: str = "evals/labels.csv") -> None:
    rows = list(csv.DictReader(Path(path).open()))
    pairs = [(int(r["human_pass"]), int(r["judge_pass"])) for r in rows]
    agree = sum(h == j for h, j in pairs) / len(pairs)
    judge_too_kind = sum(1 for h, j in pairs if j == 1 and h == 0)
    judge_too_harsh = sum(1 for h, j in pairs if j == 0 and h == 1)
    print(f"pairs: {len(pairs)}   agreement: {agree:.0%}   kappa: {kappa(pairs):.2f}")
    print(f"judge passed what you failed: {judge_too_kind}")
    print(f"judge failed what you passed: {judge_too_harsh}")
    by_rubric: dict[str, list] = {}
    for row in rows:
        by_rubric.setdefault(row["rubric"], []).append(
            int(row["human_pass"]) == int(row["judge_pass"])
        )
    for rubric, same in sorted(by_rubric.items()):
        print(f"  {rubric:20} agrees {sum(same)}/{len(same)}")


if __name__ == "__main__":
    main()
