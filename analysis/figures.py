"""Figures for the report, from the CSVs that analysis/score.py writes. Static PNG + PDF, light surface.

    python analysis/figures.py

Colours: validated pair (blue thinking on, orange thinking off or lowest), with different marker shapes
so mode is never shown by colour alone. One panel per model.
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = Path(os.environ.get("KWIK_OUT", ROOT / "results"))
FIG = ROOT / "figures"
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MODE = {"think": ("#2a78d6", "o", "Thinking on"), "nothink": ("#eb6834", "s", "Thinking off / lowest")}
ORDER = ["minicpm5-2b", "k2-horizon-3.7b", "qwen3.5-4b", "k2-horizon-7b"]
NAMES = {"k2-horizon-3.7b": "K2 Horizon 3.7B", "k2-horizon-7b": "K2 Horizon 7B",
         "minicpm5-2b": "MiniCPM5-2B", "qwen3.5-4b": "Qwen3.5-4B"}
BINS = [0, 50, 70, 80, 90, 95, 100.001]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "lines.linewidth": 2,
})


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", FIG / f"{name}.png")


def models_present(df, col="slug"):
    return [m for m in ORDER if m in set(df[col])]


def reliability():
    d = pd.read_csv(RES / "calibration_items.csv")
    d = d[d["valid"]]
    ms = models_present(d)
    fig, axes = plt.subplots(1, len(ms), figsize=(2.6 * len(ms), 2.9), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, ms):
        ax.plot([0, 100], [0, 100], color=INK2, lw=1, ls=(0, (3, 3)), zorder=1)
        for mode, (col, mk, label) in MODE.items():
            g = d[(d["slug"] == m) & (d["mode"] == mode)]
            if g.empty:
                continue
            g = g.assign(bin=pd.cut(g["confidence"], BINS, right=False))
            b = g.groupby("bin", observed=True).agg(conf=("confidence", "mean"), acc=("is_correct", "mean"), n=("id", "size"))
            b = b[b["n"] >= 5]
            ax.plot(b["conf"], 100 * b["acc"], color=col, zorder=2)
            ax.scatter(b["conf"], 100 * b["acc"], s=12 + 120 * b["n"] / len(g), color=col, marker=mk,
                       edgecolor=SURFACE, linewidth=1.5, zorder=3, label=label)
        ax.set_title(NAMES[m], color=INK, fontsize=10, loc="left")
        ax.set_xlim(40, 101)
        ax.set_ylim(0, 102)
        ax.set_xlabel("Stated confidence (%)")
    axes[0].set_ylabel("Actually correct (%)")
    axes[0].legend(frameon=False, loc="upper left", fontsize=8)
    fig.suptitle("Reliability: points below the dashed line are overconfident (bins with 5+ answers; size = share of answers)",
                 color=INK2, fontsize=9, x=0.01, ha="left", y=1.02)
    save(fig, "reliability")


def pushback():
    d = pd.read_csv(RES / "pushback_items.csv")
    ms = models_present(d)
    steps = ["Are you\nsure?", "Simple", "Ethos", "Citation"]
    fig, axes = plt.subplots(2, len(ms), figsize=(2.6 * len(ms), 4.8), sharey="row", sharex=True)
    axes = np.atleast_2d(axes)
    for j, m in enumerate(ms):
        for mode, (col, mk, label) in MODE.items():
            g = d[(d["slug"] == m) & (d["mode"] == mode)]
            if g.empty:
                continue
            R, W = g[g["start_correct"]], g[~g["start_correct"]]
            rw = [100 * (R["flipped_at"].notna() & (R["flipped_at"] <= k)).mean() for k in range(4)]
            wr = [100 * (W["flipped_at"].notna() & (W["flipped_at"] <= k) & (W["flipped_to"] == W["gold"])).mean() for k in range(4)]
            axes[0, j].plot(range(4), rw, color=col, marker=mk, ms=6, mec=SURFACE, mew=1.2, label=label)
            axes[1, j].plot(range(4), wr, color=col, marker=mk, ms=6, mec=SURFACE, mew=1.2, label=label)
        axes[0, j].set_title(NAMES[m], color=INK, fontsize=10, loc="left")
        axes[1, j].set_xticks(range(4), steps, fontsize=7.5)
        axes[0, j].set_ylim(0, 100)
        axes[1, j].set_ylim(0, 100)
    axes[0, 0].set_ylabel("Right answers given up (%)")
    axes[1, 0].set_ylabel("Wrong answers corrected (%)")
    axes[0, 0].legend(frameon=False, loc="upper left", fontsize=8)
    fig.suptitle("Pushback, cumulative by step. Top: pushed toward a wrong letter. Bottom: pushed toward the right letter.",
                 color=INK2, fontsize=9, x=0.01, ha="left", y=1.01)
    save(fig, "pushback")


def abstention():
    s = pd.read_csv(RES / "summary_abstention.csv")
    rev = {v: k for k, v in NAMES.items()}
    s["slug"] = s["model"].map(rev)
    ms = models_present(s)
    rows = [("unanswerable_abstain", "plain", "Unanswerable, plain"), ("unanswerable_abstain", "penalty", "Unanswerable, penalty"),
            ("answerable_abstain", "plain", "Answerable, plain"), ("answerable_abstain", "penalty", "Answerable, penalty")]
    fig, axes = plt.subplots(1, len(ms), figsize=(2.6 * len(ms), 2.6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, ms):
        for i, (col_name, cond, _) in enumerate(rows):
            for k, (mode, (col, mk, label)) in enumerate(MODE.items()):
                r = s[(s["slug"] == m) & (s["mode"] == mode) & (s["condition"] == cond)]
                if r.empty:
                    continue
                v = 100 * r[col_name].iloc[0]
                lo, hi = 100 * r[col_name + "_lo"].iloc[0], 100 * r[col_name + "_hi"].iloc[0]
                y = i + (k - 0.5) * 0.28
                ax.plot([lo, hi], [y, y], color=col, lw=1.2, alpha=0.6)
                ax.scatter([v], [y], color=col, marker=mk, s=36, edgecolor=SURFACE, linewidth=1.2, zorder=3,
                           label=label if i == 0 else None)
        ax.axhline(1.5, color=GRID, lw=1)
        ax.set_yticks(range(4), [r[2] for r in rows])
        ax.invert_yaxis()
        ax.set_xlim(-2, 102)
        ax.set_xlabel("Said ABSTAIN (%)")
        ax.set_title(NAMES[m], color=INK, fontsize=10, loc="left")
    axes[-1].legend(frameon=False, loc="lower right", fontsize=8)
    fig.suptitle("Abstention. Good: high on unanswerable, low on answerable. Bars are 95% intervals.",
                 color=INK2, fontsize=9, x=0.01, ha="left", y=1.03)
    save(fig, "abstention")


if __name__ == "__main__":
    for f in (reliability, pushback, abstention):
        try:
            f()
        except FileNotFoundError as e:
            print("skip", f.__name__, e)
