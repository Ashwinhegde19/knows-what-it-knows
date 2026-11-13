"""Draw a seeded sample of abstention replies for checking the automatic classifier by hand.

    python analysis/audit_sample.py [n=80]      # writes results/audit_abstention.csv

Stratified: half from replies classed as abstaining, half not, across models, modes and conditions.
The reviewer fills `human_abstained` (yes/no) and, for answerable questions, `human_correct` (yes/no).
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    d = pd.read_csv(ROOT / "results" / "abstention_items.csv")
    q = pd.concat([pd.read_csv(ROOT / "data" / "unanswerable_50.csv")[["id", "question"]],
                   pd.read_csv(ROOT / "data" / "answerable_50.csv")[["id", "question", "gold_aliases"]]])
    d = d.merge(q, on="id", how="left")
    parts = [g.sample(min(len(g), n // 2), random_state=20261114) for _, g in d.groupby("abstained")]
    s = pd.concat(parts).sample(frac=1, random_state=1)
    s["human_abstained"] = ""
    s["human_correct"] = ""
    cols = ["slug", "mode", "condition", "run", "id", "kind", "question", "gold_aliases", "final",
            "abstained", "abstain_how", "is_correct", "human_abstained", "human_correct"]
    s[cols].to_csv(ROOT / "results" / "audit_abstention.csv", index=False)
    print(f"wrote {len(s)} rows to results/audit_abstention.csv")


if __name__ == "__main__":
    main()
