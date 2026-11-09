"""Build the two question sets used by the evals.

Outputs (all in data/):
  factual_200.csv       200 MMLU-Pro questions, stratified over its 14 categories,
                        reduced to 4 options (gold + 3 random distractors) so the
                        calibrated-random Brier baseline is 0.1875, matching
                        ConfidenceBench (ffrench-Constant et al., 2026).
  unanswerable_50.csv   25 SelfAware (Yin et al., 2023) word problems whose answer
                        cannot be determined because information is missing, plus
                        25 hand-written questions about fabricated entities. Both
                        kinds have one correct behaviour: abstain.

Everything is seeded so the sets are reproducible. Pre-sprint work: data prep only.
"""
from __future__ import annotations

import csv
import json
import random
import re
from pathlib import Path

from datasets import load_dataset

SEED = 20261113
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
N_FACTUAL = 200
N_OPTIONS = 4
N_SELFAWARE = 25
LETTERS = "ABCDEFGHIJ"
MAX_QUESTION_CHARS = 1200


def clean_distractors(row: dict) -> list[int]:
    """Indices of wrong options that are real answers, not formula fragments."""
    gold = row["answer_index"]
    out = []
    for j, opt in enumerate(row["options"]):
        o = opt.strip()
        if j == gold or not o or o == "N/A" or o.startswith("[") or len(o) > 300:
            continue
        out.append(j)
    return out


# SelfAware mixes philosophical prompts with arithmetic word problems that omit a
# needed quantity. Only the latter have an objectively correct response ("cannot
# be determined"), so we keep questions that look like word problems.
WORD_PROBLEM = re.compile(r"\b(how many|how much|how long|how far|how old)\b", re.I)
HAS_DIGIT = re.compile(r"\d")
NEGATIVE_NUMBER = re.compile(r"-\d")

# Questions about entities that do not exist. A correct model abstains.
FABRICATED = [
    "In which year did the Norwegian chemist Harald Venstrom receive the Lindqvist Medal?",
    "What is the population of the town of Caldmere in Cumbria, England, according to the 2021 census?",
    "Who directed the 1987 film 'The Salt Cartographer'?",
    "What was the final score of the 1994 Bellhaven Cup final between Dunmorrow FC and Ashwick Town?",
    "Which company manufactured the Tessaro X9 digital camera released in 2003?",
    "What is the chemical formula of the mineral orvillite?",
    "Who wrote the 1962 novel 'A Lantern for the Ferryman'?",
    "In what year was the University of Pellbrook founded?",
    "What is the maximum speed of the Kestrel K-14 light aircraft built by Marrow Aviation?",
    "Which element did the physicist Ilse Brandauer isolate in 1931?",
    "How many episodes were in the first season of the BBC drama 'Winter at Hollins Gate'?",
    "What is the height of the Vardane Tower in Lyon, France?",
    "Who was the first mayor of the city of Port Ellery, Australia?",
    "What programming language was the 1998 game 'Chrono Vectors' written in?",
    "In which year did the Treaty of Ambervale end the Carinthian Succession War?",
    "What is the boiling point of the compound methylquentane at standard pressure?",
    "Which team won the 2011 Sorensen Trophy in Danish handball?",
    "Who composed the opera 'The Glass Orchard', first performed in Vienna in 1911?",
    "How many stations are on the Brindle Line of the Manchester tram network?",
    "What was the market capitalisation of Halvorsen Dynamics when it listed on the Oslo exchange in 2016?",
    "What is the name of the moon discovered orbiting the asteroid 4471 Pelmarsh in 2009?",
    "Which painting by the Flemish artist Joos van Terlaan hangs in the Rijksmuseum?",
    "What is the length in kilometres of the Oresby Canal in Lincolnshire?",
    "Who holds the world record for the 1,500 metre indoor relay set at the 2019 Tallinn Games?",
    "What dosage of the drug Veltraxin is recommended for adults with mild hypertension?",
]


def build_factual(rng: random.Random) -> list[dict]:
    ds = load_dataset("TIGER-Lab/MMLU-Pro", split="test")
    by_cat: dict[str, list[dict]] = {}
    for row in ds:
        if len(row["question"]) > MAX_QUESTION_CHARS:
            continue
        if len(clean_distractors(row)) < N_OPTIONS - 1:
            continue
        by_cat.setdefault(row["category"], []).append(row)
    cats = sorted(by_cat)
    per_cat = N_FACTUAL // len(cats)              # 14
    extra = N_FACTUAL - per_cat * len(cats)        # 4
    chosen: list[dict] = []
    leftovers: list[dict] = []
    for cat in cats:
        rows = by_cat[cat][:]
        rng.shuffle(rows)
        chosen.extend(rows[:per_cat])
        leftovers.extend(rows[per_cat:])
    rng.shuffle(leftovers)
    chosen.extend(leftovers[:extra])
    rng.shuffle(chosen)

    out = []
    for i, row in enumerate(chosen, 1):
        gold = row["answer_index"]
        keep = [gold] + rng.sample(clean_distractors(row), N_OPTIONS - 1)
        rng.shuffle(keep)
        options = [row["options"][j] for j in keep]
        out.append({
            "id": f"F{i:03d}",
            "category": row["category"],
            "question": row["question"].strip(),
            **{f"option_{LETTERS[k]}": options[k] for k in range(N_OPTIONS)},
            "answer": LETTERS[keep.index(gold)],
            "mmlu_pro_question_id": row["question_id"],
            "mmlu_pro_answer": row["answer"],
            "mmlu_pro_original_option_indices": " ".join(map(str, keep)),
            "mmlu_pro_n_options": len(row["options"]),
            "source": "TIGER-Lab/MMLU-Pro test split",
        })
    return out


def build_unanswerable(rng: random.Random) -> list[dict]:
    raw = json.load(open(DATA / "raw" / "selfaware" / "SelfAware.json"))["example"]
    pool = [
        e for e in raw
        if not e["answerable"]
        and WORD_PROBLEM.search(e["question"])
        and HAS_DIGIT.search(e["question"])
        and not NEGATIVE_NUMBER.search(e["question"])
        and 40 <= len(e["question"]) <= 300
        and e["question"].strip().endswith("?")
    ]
    pool.sort(key=lambda e: e["question_id"])
    picked = rng.sample(pool, N_SELFAWARE)
    out = []
    for i, e in enumerate(picked, 1):
        out.append({
            "id": f"U{i:03d}",
            "kind": "missing_info",
            "question": e["question"].strip(),
            "selfaware_question_id": e["question_id"],
            "source": "SelfAware (Yin et al., 2023), unanswerable subset (missing information), Apache-2.0",
        })
    for j, q in enumerate(FABRICATED, 1):
        out.append({
            "id": f"U{N_SELFAWARE + j:03d}",
            "kind": "fabricated",
            "question": q,
            "selfaware_question_id": "",
            "source": "written for this project; entity does not exist",
        })
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    factual = build_factual(rng)
    unanswerable = build_unanswerable(rng)
    write_csv(DATA / "factual_200.csv", factual)
    write_csv(DATA / "unanswerable_50.csv", unanswerable)
    cats = {}
    for r in factual:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"factual: {len(factual)} rows, per category: {cats}")
    print(f"unanswerable: {len(unanswerable)} rows "
          f"({N_SELFAWARE} missing-info + {len(FABRICATED)} fabricated)")


if __name__ == "__main__":
    main()
