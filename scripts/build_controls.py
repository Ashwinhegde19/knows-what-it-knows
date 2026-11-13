"""Answerable control questions for the abstention check (sprint work, 13 Nov 2026).

    python scripts/build_controls.py      # writes data/answerable_50.csv

50 short factual questions from SelfAware's answerable part (TriviaQA origin), with gold aliases.
They catch a model that "abstains well" only because it refuses everything, and give a
penalty-rule score (+1 right, -3 wrong, 0 abstain) on questions that do have answers.
"""
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261113


def main() -> None:
    data = json.loads((ROOT / "data/raw/selfaware/SelfAware.json").read_text())["example"]
    pool = [
        e for e in data
        if e["answerable"] and e["source"].startswith("triviaqa")
        and 25 <= len(e["question"]) <= 200
        and e["answer"] and all(len(a) <= 40 for a in e["answer"])
    ]
    rng = random.Random(SEED)
    picked = sorted(rng.sample(pool, 50), key=lambda e: e["question_id"])
    out = ROOT / "data/answerable_50.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "kind", "question", "gold_aliases", "selfaware_question_id", "source"])
        for i, e in enumerate(picked, 1):
            w.writerow([f"A{i:03d}", "answerable_trivia", e["question"].strip(), " || ".join(e["answer"]),
                        e["question_id"], "SelfAware (Yin et al., 2023), answerable subset (TriviaQA origin), Apache-2.0"])
    print(f"wrote {out} ({len(picked)} rows) from a pool of {len(pool)}")


if __name__ == "__main__":
    main()
