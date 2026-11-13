"""Do replies that hit the 32,768-token cap loop? Checks the last 6,000 characters of each capped reply.

    python analysis/loops.py     # writes results/capped_replies.csv

A reply counts as looping if its tail compresses to under 10% of its size with zlib, or one line of 20+
characters repeats 5+ times in it. Both are signs of the same text repeating, not of long new reasoning.
"""
import glob
import json
import zlib
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def looping(text: str) -> tuple[bool, float, int]:
    tail = text[-6000:]
    ratio = len(zlib.compress(tail.encode())) / max(len(tail.encode()), 1)
    lines = [l.strip() for l in tail.splitlines() if len(l.strip()) >= 20]
    top = Counter(lines).most_common(1)[0][1] if lines else 0
    return ratio < 0.10 or top >= 5, round(ratio, 3), top


def main():
    rows = []
    for task in ("calibration", "abstention"):
        for f in sorted(glob.glob(str(ROOT / "results/raw" / task / "*.jsonl"))):
            for line in open(f):
                r = json.loads(line)
                total = 1
                if r.get("finish_reason") != "length":
                    rows.append({"task": task, "file": Path(f).name, "capped": False})
                    continue
                loop, ratio, top = looping((r.get("reasoning") or "") + (r.get("content") or ""))
                rows.append({"task": task, "file": Path(f).name, "capped": True, "looping": loop,
                             "zlib_ratio": ratio, "top_line_repeats": top, "id": r["id"]})
    d = pd.DataFrame(rows)
    d["model_mode"] = d["file"].str.replace(r"__run\d\.jsonl", "", regex=True)
    d[d["capped"]].to_csv(ROOT / "results" / "capped_replies.csv", index=False)
    s = d.groupby("model_mode").agg(replies=("capped", "size"), capped=("capped", "sum"),
                                    looping=("looping", lambda x: int(x.fillna(False).sum())))
    s["capped_pct"] = (100 * s["capped"] / s["replies"]).round(2)
    s["looping_share_of_capped"] = (s["looping"] / s["capped"].where(s["capped"] > 0)).round(2)
    print(s.to_string())


if __name__ == "__main__":
    main()
