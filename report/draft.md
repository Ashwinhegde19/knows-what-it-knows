# Do New Small Open Models Know What They Know? Calibration, Abstention and Pushback in K2 Horizon, MiniCPM5 and Qwen3.5

Ashwin K M. Apart Research AI x Epistemics Sprint, Track 1, 13 to 15 November 2026.
Code and raw replies: github.com/Ashwinhegde19/knows-what-it-knows

> Draft status: sections marked [RESULTS] are filled after the runs. Items marked [VERIFY] need a source link
> checked before submission.

## Abstract

[RESULTS] Four sentences: what we tested, on which models, the headline number for each check, and the one
practical takeaway.

## 1. Introduction

Small open-weight models are now released every few weeks and are increasingly run on phones, laptops and
inside agents, often without a human checking each answer. For that use, accuracy is not enough. A model also
has to signal when it is likely to be wrong: by stating lower confidence, by declining to answer, or by holding
a correct answer when a user pushes back. These are epistemic properties, and they are rarely measured for new
small models. Public leaderboards report accuracy; honesty evaluations such as ConfidenceBench and the Pander
Score cover flagship models.

K2 Horizon (Institute of Foundation Models, September 2026, Apache 2.0) is a useful case. Its 3.7B and 7B
versions are among the strongest tiny open models on standard benchmarks, and its largest sibling is reported
by Artificial Analysis to decline more often than it guesses on AA-Omniscience [VERIFY: attempts about 40% of
questions, 26% hallucination rate]. Nobody has checked whether that caution survives at 3.7B and 7B, or whether
these models know what they know at all.

We ask three questions of K2 Horizon 3.7B and 7B, MiniCPM5-2B (OpenBMB, September 2026) and Qwen3.5-4B
(Alibaba, March 2026, the widely evaluated reference), each with thinking on and with thinking off or at its
lowest setting:

1. **Calibration.** When the model says it is 90% sure, is it right 90% of the time?
2. **Abstention.** Does it decline questions that have no answer, without declining questions that do? Does an
   explicit penalty for wrong answers change that the way it should?
3. **Pushback.** When a user disagrees, does it give up correct answers, accept corrections to wrong ones, and
   does its own stated confidence predict which?

Contributions: [RESULTS] three findings, one line each. All prompts, raw replies (including thinking text),
scoring code and figures are released.

## 2. Related work

**Verbalized confidence.** ConfidenceBench (ffrench-Constant et al., 2026) scores stated confidence on
multiple-choice questions with the Brier score against a calibrated-random baseline; we follow its 4-option
format and its rule for unparseable replies.
**Abstention.** SelfAware (Yin et al., 2023) pairs unanswerable questions with answerable ones. Kalai et al.
(2025) argue that benchmarks which score "I don't know" as wrong reward guessing, and propose stating an explicit
penalty threshold in the prompt; we test that proposal directly.
**Pushback and sycophancy.** The FlipFlop experiment (Laban et al., 2023) showed accuracy drops after "Are you
sure?". SycEval (Fanous et al., 2025) separates regressive flips (right to wrong) from progressive ones (wrong to
right) under rebuttals of rising strength. The Pander Score (Botas et al., 2026) measures sycophancy in flagship
models. We combine these into one protocol and add the link to stated confidence.

## 3. Method

**Models and settings.** Four models served with vLLM 0.33.0 on one NVIDIA L40S each (Modal). Each model runs at
its developer's recommended sampling: K2 Horizon temperature 1.0, top-p 0.95; MiniCPM5 temperature 1.0, top-p
0.95, min-p 0; Qwen3.5 thinking temperature 1.0, top-p 0.95, top-k 20, presence penalty 1.5, and non-thinking
temperature 0.7, top-p 0.8, top-k 20, presence penalty 1.5. Output limit 32,768 tokens (K2 Horizon's stated
minimum). Thinking is switched by the chat template. K2 Horizon has no off switch: its lowest setting
(`reasoning_effort=low`) still thinks briefly, so "thinking off" means off for Qwen3.5 and MiniCPM5 and low for
K2 Horizon. A pilot with one shared temperature (0.6) made Qwen3.5 loop until the token limit, which is why each
model runs at its own recommended settings.

**Calibration.** 200 MMLU-Pro test questions, at least 14 from each of its 14 subjects, reduced from 10 options
to 4 (the gold answer plus three random wrong options, shuffled) so that the calibrated-random Brier score is
0.1875. The model answers and states a confidence from 0 to 100 on two fixed final lines. Three independent runs
per model and mode. Metrics: accuracy; Brier score (an unparseable reply adds 0.1875, as in ConfidenceBench);
overconfidence (mean confidence minus accuracy); expected calibration error over 10 bins; and AUROC of
confidence for separating right from wrong answers, where 0.5 means confidence carries no information.

**Abstention.** 50 questions with no answer: 25 SelfAware arithmetic problems with a missing quantity and 25
questions about people, places and products we invented. 50 answerable controls: SelfAware questions of TriviaQA
origin, graded by lenient match against the gold aliases. Every question is asked twice. *Plain*: answer, or
write ABSTAIN if it cannot be answered or you do not know. *Penalty*: the same, plus "answer only if you are more
than 75% confident; correct +1, wrong -3, ABSTAIN 0" (Kalai et al.'s threshold). Three runs. A reply abstains if
its final line contains ABSTAIN, otherwise if it contains a listed phrase such as "cannot be determined"; the
share decided by phrase is reported.

**Pushback.** For each calibration question in run 1, the model's own answer is challenged in the same
conversation, up to four times, stopping at the first changed answer: (0) "Are you sure?" with no suggested
answer; (1) a suggested letter; (2) the same from a claimed university teacher of the subject; (3) the same from
a claimed textbook. Right answers are pushed toward a wrong letter chosen with a fixed seed; wrong answers toward
the right letter. Earlier turns contain only the model's visible answer. We report right-to-wrong and
wrong-to-right rates by step, and whether the model's initial stated confidence predicts which right answers it
gives up (AUROC).

**Uncertainty.** 95% intervals come from a bootstrap over questions (each question keeps all its runs), 2,000
resamples.

## 4. Results

[RESULTS] Table 1 calibration, Figure 1 reliability. Table 2 abstention, Figure 2. Figure 3 pushback.

## 5. Discussion

[RESULTS]

## 6. Conclusion

[RESULTS]

## References

- Botas et al. (2026). Pander Score. [VERIFY full title and link]
- Fanous et al. (2025). SycEval: Evaluating LLM Sycophancy. [VERIFY link]
- ffrench-Constant et al. (2026). ConfidenceBench. [VERIFY full title and link]
- Kalai, Nachum, Vempala, Zhang (2025). Why Language Models Hallucinate. [VERIFY link]
- Laban et al. (2023). Are You Sure? Challenging LLMs Leads to Performance Drops in The FlipFlop Experiment.
- Wang et al. (2024). MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark.
- Yin et al. (2023). Do Large Language Models Know What They Don't Know? (SelfAware).
- Artificial Analysis (2026). AA-Omniscience results for K2 Horizon. [VERIFY link and numbers]
- Model cards: IFM/K2-Horizon-3.7B, IFM/K2-Horizon-7B, openbmb/MiniCPM5-2B, Qwen/Qwen3.5-4B (Hugging Face).

## Appendix A. Limitations and dual-use considerations

**Limitations.**
- Small samples: 200 calibration questions, 50 unanswerable and 50 answerable questions, three runs each. The
  intervals are wide for differences of a few points.
- Verbalized confidence is one signal. Token probabilities or agreement across samples might calibrate better or
  worse; we did not compare them.
- "Thinking off" is not the same thing across models, because K2 Horizon cannot switch thinking off.
- Each model runs at its own recommended sampling. That reflects how the models are meant to be used but means
  sampling differs between models.
- The abstention classifier uses an ABSTAIN token plus a phrase list, and answerable questions are graded by
  lenient alias matching. [RESULTS: hand audit of N replies, agreement X%.]
- The pushback ladder uses fixed templates and a claimed citation that is not real. Real users argue with content,
  which may move models more.
- MMLU-Pro questions may appear in training data, which would inflate accuracy and confidence together.
- English only.

**Dual use.** The pushback results show which kinds of pressure make small models abandon correct answers. That
could help someone manipulate a deployed assistant, but the techniques (disagreeing, claiming expertise, citing a
source) are already common and widely documented. The main use of these results is defensive: choosing models
and settings for unsupervised deployment, and testing fixes. No harmful content was generated or used.

## Appendix B. Reproducibility

Every request is one JSON line in `results/raw/`, with the full reply and thinking text, token counts and finish
reason. `analysis/score.py` recomputes every number from those files. Datasets are rebuilt exactly by
`scripts/build_datasets.py` and `scripts/build_controls.py` (seed 20261113).

## LLM usage statement

Claude (Anthropic) was used through Claude Code to write the evaluation code, run the experiments, and draft this
report. All study design choices, the selection of models and questions, and the interpretation were reviewed by
the author, who is responsible for the content. [AUTHOR: edit to reflect exactly what you did.]

## Pre-existing work

Before the sprint the repository held only data preparation and model-serving scripts, listed in the README's
Provenance section. All evaluation code, runs, figures and this report were produced during the sprint.
