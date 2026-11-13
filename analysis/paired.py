"""Paired differences with 95% bootstrap intervals over questions (same questions in both conditions).

    python analysis/paired.py        # writes results/paired_differences.csv

- Thinking on minus off, per model: accuracy, Brier, overconfidence (parsed replies).
- Penalty minus plain, per model and mode: abstention on unanswerable, abstention on answerable, penalty score.
Each question is averaged over its runs first, then questions are resampled (2,000 draws, seed 0).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(0)
B = 2000
NAMES = {"k2-horizon-3.7b": "K2 Horizon 3.7B", "k2-horizon-7b": "K2 Horizon 7B",
         "minicpm5-2b": "MiniCPM5-2B", "qwen3.5-4b": "Qwen3.5-4B"}


def ci(diff: np.ndarray):
    diff = diff[~np.isnan(diff)]
    boots = [diff[RNG.integers(0, len(diff), len(diff))].mean() for _ in range(B)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return diff.mean(), lo, hi, len(diff)


def main():
    out = []
    c = pd.read_csv(ROOT / "results" / "calibration_items.csv")
    c["p"] = c["confidence"] / 100
    c["over"] = np.where(c["valid"], c["p"] - c["is_correct"], np.nan)
    per_q = c.groupby(["slug", "mode", "id"]).agg(acc=("is_correct", "mean"), brier=("brier", "mean"),
                                                   over=("over", "mean")).reset_index()
    for slug, g in per_q.groupby("slug"):
        w = g.pivot(index="id", columns="mode")
        for m in ("acc", "brier", "over"):
            d, lo, hi, n = ci((w[(m, "think")] - w[(m, "nothink")]).to_numpy(dtype=float))
            out.append({"comparison": "thinking on - off", "model": NAMES[slug], "mode": "", "metric": m,
                        "diff": d, "lo": lo, "hi": hi, "n_questions": n})
    a = pd.read_csv(ROOT / "results" / "abstention_items.csv")
    a["abst"] = a["abstained"].astype(float)
    per_q = a.groupby(["slug", "mode", "condition", "id", "answerable"]).agg(abst=("abst", "mean"),
                                                                             score=("score", "mean")).reset_index()
    for (slug, mode), g in per_q.groupby(["slug", "mode"]):
        for label, sub, metric in (("abstain on unanswerable", g[~g["answerable"]], "abst"),
                                   ("abstain on answerable", g[g["answerable"]], "abst"),
                                   ("penalty score on answerable", g[g["answerable"]], "score")):
            w = sub.pivot(index="id", columns="condition", values=metric)
            d, lo, hi, n = ci((w["penalty"] - w["plain"]).to_numpy(dtype=float))
            out.append({"comparison": "penalty - plain", "model": NAMES[slug], "mode": mode, "metric": label,
                        "diff": d, "lo": lo, "hi": hi, "n_questions": n})
    for slug, g in per_q.groupby("slug"):
        for label, sub in (("abstain on unanswerable", g[~g["answerable"]]), ("abstain on answerable", g[g["answerable"]])):
            w = sub.groupby(["id", "mode"])["abst"].mean().unstack()
            d, lo, hi, n = ci((w["think"] - w["nothink"]).to_numpy(dtype=float))
            out.append({"comparison": "thinking on - off", "model": NAMES[slug], "mode": "", "metric": label,
                        "diff": d, "lo": lo, "hi": hi, "n_questions": n})
    # Pushback: thinking on - off in the share of right answers given up by the end of the ladder, on questions
    # the model answered right in both modes (so the same questions are compared).
    pb = pd.read_csv(ROOT / "results" / "pushback_items.csv")
    pb["caved"] = pb["flipped_at"].notna().astype(float)
    R = pb[pb["start_correct"]]
    for slug, g in R.groupby("slug"):
        w = g.pivot(index="id", columns="mode", values="caved").dropna()
        d, lo, hi, n = ci((w["think"] - w["nothink"]).to_numpy(dtype=float))
        out.append({"comparison": "thinking on - off", "model": NAMES[slug], "mode": "",
                    "metric": "right answers given up (same questions)", "diff": d, "lo": lo, "hi": hi, "n_questions": n})
    df = pd.DataFrame(out)
    df["excludes_zero"] = (df["lo"] > 0) | (df["hi"] < 0)
    df.to_csv(ROOT / "results" / "paired_differences.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 200)
    print(df.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
