# Does a small model know what it knows?

Calibration, abstention and pushback-resistance evals for new small open-weight models.

Built for the Apart Research **AI x Epistemics Research Sprint**, Track 1 (Model Epistemics & Decision-Making Evals), 13–15 November 2026.

**Report:** [`report/Apart_submission.pdf`](report/Apart_submission.pdf) (4 pages of main text, plus references and appendix).

## Main results

Four models released in 2026, each with thinking on and off, 14,597 requests in total. Every reply, including thinking text, is in `results/raw/`.

- **All eight setups are overconfident**, by 6.5 to 14.1 points. Answers stated at 90% confidence or more were right 84% to 91% of the time.
- **No model declines exactly what it cannot know.** K2 Horizon 7B answered questions about invented people and things 40% to 52% of the time. MiniCPM5-2B refused 57% to 82% of answerable questions.
- **Stating the penalty for wrong answers barely helps** (right +1, wrong -3, ABSTAIN 0). It improved the penalty score clearly in only one of eight setups.
- **A named wrong answer overturns correct ones.** By the end of the four challenges, models gave up 29% to 87% of their correct answers, almost always to the suggested one. A bare "Are you sure?" changed 0% to 4%.
- **Thinking is the one setting that helped everywhere.** It lowered the Brier score in every model and, on the same questions, cut giving up under pushback by 17 to 50 points.

| Model | Thinking | Accuracy % | Overconfidence (points) | Abstains on invented entities % | Abstains on answers it knows % | Correct answers given up % |
|---|---|---|---|---|---|---|
| MiniCPM5-2B | on | 78.3 | 6.5 | 99 | 37 | 35 |
| MiniCPM5-2B | off | 73.7 | 10.6 | 95 | 45 | 69 |
| K2 Horizon 3.7B | on | 78.5 | 8.6 | 63 | 4 | 29 |
| K2 Horizon 3.7B | low | 73.8 | 14.1 | 63 | 8 | 52 |
| K2 Horizon 7B | on | 83.0 | 7.1 | 53 | 2 | 30 |
| K2 Horizon 7B | low | 80.2 | 9.7 | 48 | 1 | 43 |
| Qwen3.5-4B | on | 86.3 | 8.5 | 88 | 5 | 38 |
| Qwen3.5-4B | off | 80.8 | 12.6 | 39 | 6 | 87 |

Limits: small samples (200 calibration questions, 50 + 50 abstention questions), so differences of a few points are not reliable. K2 Horizon cannot switch thinking off, so "low" is its lowest setting. A hand check of 80 replies was done by the AI assistant that helped build this; see `results/AUDIT.md`. The full list is in Appendix A of the report.

## Question

New small open models ship every few weeks with no independent honesty evals. This project tests whether they know when they are likely to be wrong, using three checks:

1. **Calibration.** Answer 200 MMLU-Pro questions and state a confidence. Score with Brier score and a reliability diagram. Baseline: calibrated random.
2. **Abstention.** 50 unanswerable questions and 50 answerable controls, asked plainly and again with an explicit penalty rule (right +1, wrong -3, ABSTAIN 0). A good model abstains on the first set, keeps answering the second, and shifts sensibly under the penalty.
3. **Pushback.** Challenge each answer up to four times: "are you sure?", then a suggested letter, then claimed expertise, then a claimed textbook. Right answers are pushed toward a wrong letter, wrong answers toward the right one. Right-to-wrong flips are counted separately from wrong-to-right corrections, and compared with the model's own stated confidence.

## Models

| Model | Role |
|---|---|
| K2 Horizon 3.7B, 7B (IFM, Sep 2026) | Target: top-ranked tiny open model, no independent evals |
| MiniCPM5-2B (OpenBMB, Sep 2026) | Target: abstains far more than peers; is that real? |
| Qwen3.5-4B (Alibaba, Mar 2026) | Reference: widely evaluated |

## Layout

```
data/       question sets as CSV (200 factual, 50 unanswerable, 50 answerable controls)
kwik/       runner, prompts, parsers, model settings  (python -m kwik.run ...)
analysis/   scoring (score.py) and figures (figures.py)
scripts/    data building, Modal serving, run_all.sh
results/    raw/ one JSON line per request with full replies; summary_*.csv and *_items.csv
figures/    reliability, abstention and pushback plots
report/     the submitted PDF (Apart_submission.pdf) and how it was built (fill_template.py)
```

## Running

```
pip install -r requirements.txt
python scripts/build_datasets.py && python scripts/build_controls.py    # rebuild data/ exactly
KWIK_MODEL=IFM/K2-Horizon-3.7B modal deploy scripts/modal_serve.py       # one vLLM server per model
scripts/run_all.sh                                                       # every model x thinking mode
python analysis/score.py && python analysis/figures.py
```

## Method notes

- **Runner.** A small streaming Python runner (`kwik/run.py`) instead of Inspect AI. It gives exact control over
  what earlier turns contain in the multi-turn pushback test, and stores every raw reply, including thinking text.
  Reruns skip finished questions.
- **Sampling.** Each model runs at its developer's recommended settings (see `kwik/models.py`), with up to
  32,768 output tokens. A first pilot with one shared temperature (0.6) made Qwen3.5-4B loop until the token cap;
  that pilot is kept in `results/pilot_t06/` and not used.
- **Thinking modes.** Qwen3.5 and MiniCPM5 can switch thinking off. K2 Horizon cannot: its lowest setting,
  `reasoning_effort=low`, still thinks briefly. "Thinking off / lowest" means off for the first two and low for K2.
- **Recovered replies.** At low effort K2 Horizon 7B sometimes closes its thinking with a different tag than it
  opened, so the server files the whole reply as thinking. The visible answer is taken from after the last closing
  tag, and each such reply is flagged `visible_recovered`.
- **Multi-turn history.** In the pushback test, earlier assistant turns contain only the visible answer, with an
  empty thinking field (K2 Horizon's template requires the field).

## Provenance (sprint honesty rule)

Apart requires pre-sprint work to be declared. Before 13 November 2026 this repo contained only:

- this README, the folder layout, `.gitignore` and `requirements.txt`
- `scripts/build_datasets.py` and its outputs `data/factual_200.csv` and `data/unanswerable_50.csv`, with `data/README.md` describing the sampling (added 9 November)
- the 25 fabricated-entity questions in that script (written 9 November)
- `scripts/modal_download.py`, `scripts/modal_serve.py` and `scripts/smoke_test.py`: Modal weight download, vLLM serving, and a one-request connectivity check (added 9 November). No eval logic.

All eval tasks, prompts, runs, figures and the report were produced during the sprint (from 13 November 2026),
including `data/answerable_50.csv` and `scripts/build_controls.py`. Any later exception is listed here.

## Related work

SycEval (Fanous et al., 2025) for the rebuttal ladder; ConfidenceBench (ffrench-Constant et al., 2026) for verbalized-confidence Brier scoring; Kalai et al. (2025) for why binary-graded benchmarks reward guessing; Pander Score (Botas et al., 2026) for output-level sycophancy on flagship models.

## License

MIT for code. Question sets inherit the licenses of MMLU-Pro and SelfAware.
