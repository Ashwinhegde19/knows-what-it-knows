# Does a small model know what it knows?

Calibration, abstention and pushback-resistance evals for new small open-weight models.

Built for the Apart Research **AI x Epistemics Research Sprint**, Track 1 (Model Epistemics & Decision-Making Evals), 13–15 November 2026.

## Question

New small open models ship every few weeks with no independent honesty evals. This project tests whether they know when they are likely to be wrong, using three checks:

1. **Calibration.** Answer 200 MMLU-Pro questions and state a confidence. Score with Brier score and a reliability diagram. Baseline: calibrated random.
2. **Abstention.** 50 unanswerable questions under an explicit penalty instruction (wrong answer costs points, "I don't know" costs nothing). Does the model abstain or guess?
3. **Pushback.** For questions the model got right, rebut with escalating pressure ("Are you sure? I think it's B."). Count right-to-wrong flips separately from wrong-to-right updates.

## Models

| Model | Role |
|---|---|
| K2 Horizon 3.7B, 7B (IFM, Sep 2026) | Target: top-ranked tiny open model, no independent evals |
| MiniCPM5-2B (OpenBMB, Sep 2026) | Target: abstains far more than peers; is that real? |
| Qwen3.5-4B (Alibaba, Mar 2026) | Reference: widely evaluated |
| K2 Horizon 32B | Stretch, only if time allows |

## Layout

```
data/      question sets as CSV (200 factual, 50 unanswerable)
tasks/     Inspect AI tasks, one per check
prompts/   confidence, abstention and pushback prompt templates
scripts/   data sampling, plotting, Modal runner
logs/      Inspect logs from the real runs
results/   CSVs behind the figures
figures/   reliability diagram, flip curve
report/    the PDF and its source
```

## Running

```
pip install -r requirements.txt
python scripts/build_datasets.py          # samples questions into data/
inspect eval tasks/calibration.py --model <model>
```

Full instructions will be filled in during the sprint.

## Provenance (sprint honesty rule)

Apart requires pre-sprint work to be declared. Before 13 November 2026 this repo contained only:

- this README, the folder layout, `.gitignore` and `requirements.txt`
- `scripts/build_datasets.py` and its outputs `data/factual_200.csv` and `data/unanswerable_50.csv`, with `data/README.md` describing the sampling (added 9 November)
- the 25 fabricated-entity questions in that script (written 9 November)
- `scripts/modal_download.py`, `scripts/modal_serve.py` and `scripts/smoke_test.py`: Modal weight download, vLLM serving, and a one-request connectivity check (added 9 November). No eval logic.

All eval tasks, prompts, runs, figures and the report were produced during the sprint. Any later exception is listed here.

## Related work

SycEval (Fanous et al., 2025) for the rebuttal ladder; ConfidenceBench (ffrench-Constant et al., 2026) for verbalized-confidence Brier scoring; Kalai et al. (2025) for why binary-graded benchmarks reward guessing; Pander Score (Botas et al., 2026) for output-level sycophancy on flagship models.

## License

MIT for code. Question sets inherit the licenses of MMLU-Pro and SelfAware.
