# Do New Small Open Models Know What They Know? Calibration, Abstention and Pushback in K2 Horizon, MiniCPM5 and Qwen3.5

Ashwin K M (independent), with Apart Research

## Abstract

New small open models come out every few weeks, and almost nobody checks how honestly they handle their own
uncertainty. I tested four models released in 2026 (K2 Horizon 3.7B and 7B, MiniCPM5-2B and Qwen3.5-4B), each
with thinking on and off, on three checks: stated confidence on 200 MMLU-Pro questions, abstention on 50
unanswerable and 50 answerable questions with and without a stated penalty for wrong answers, and pushback of
rising strength against the model's own answers (14,597 requests in total). All eight setups are overconfident,
by 6.5 to 14.1 points. No model declines exactly what it cannot know: K2 Horizon 7B answered questions about
people and things I made up 40% to 52% of the time, while MiniCPM5 refused up to three in four questions it
could answer. Stating the penalty barely changed anything. When a user named a wrong answer, the models gave up
29% to 87% of their correct answers. Thinking was the only thing that helped everywhere: it lowered the Brier
score in every model and cut the giving-up rate on the same questions by 17 to 50 points.

## 1. Introduction

Small open-weight models now run on phones, on laptops and inside agents, often with no human checking each
answer. For that, accuracy is not enough. The model also has to show when it is probably wrong: by stating
lower confidence, by declining to answer, or by keeping a correct answer when a user pushes back. Honesty
evaluations such as ConfidenceBench [4] and the Pander Score [2] cover flagship models, not new small ones.

K2 Horizon (Institute of Foundation Models, September 2026) is a good example. Artificial Analysis reports that
its largest model, at 375B, attempts only 40% of AA-Omniscience questions and has one of the lowest
hallucination rates they have measured [1]. As far as I could find, nobody has checked whether that caution
survives at 3.7B and 7B. I tested those two models, MiniCPM5-2B and Qwen3.5-4B (the well-studied reference).

My main contributions are:

1. **The first independent check of calibration, abstention and pushback on K2 Horizon 3.7B/7B and
   MiniCPM5-2B.** All are overconfident, and the caution of the largest K2 Horizon is missing in the small ones.
2. **A direct test of the proposal by Kalai et al. [5]** to state the penalty for wrong answers in the prompt.
   It clearly improved the score in only one of eight setups.
3. **A same-question comparison of thinking on and off.** Thinking helped every model: better calibration, and
   17 to 50 points less giving up under pushback.

## 2. Related Work

ConfidenceBench [4] scores stated confidence with the Brier score; I follow its 4-option format. SelfAware [8]
pairs unanswerable questions with answerable ones. Kalai et al. [5] argue that benchmarks which mark "I don't
know" as wrong reward guessing, and propose stating a penalty in the prompt. FlipFlop [6] found that 2023
models flipped 46% of answers after a bare "Are you sure?", and SycEval [3] separates right-to-wrong flips from
wrong-to-right ones. These studies cover large or older models, one behaviour at a time. I run all three on the
same new small models.

## 3. Methods

**Models.** Four models served with vLLM, each at its developer's recommended sampling settings (Appendix C).
K2 Horizon has no thinking-off switch, so for K2 Horizon "off" means its lowest effort setting.

**Calibration.** 200 MMLU-Pro [7] questions from all 14 subjects, cut from 10 options to 4. The model gives an
answer and a confidence from 0 to 100. I report accuracy, Brier score, overconfidence (mean confidence minus
accuracy) and AUROC (how well confidence separates right answers from wrong ones).

**Abstention.** 50 questions with no answer: 25 SelfAware arithmetic problems with a missing number, and 25
questions about people, places and products that I invented. 50 answerable controls come from SelfAware. Each
is asked with a *plain* prompt (answer, or write ABSTAIN) and a *penalty* prompt that adds: "Answer only if you
are more than 75% confident. A correct answer scores 1 point, a wrong answer loses 3 points, and ABSTAIN scores
0 points."

**Pushback.** Each model's own calibration answers are challenged up to four times, stopping at the first
changed answer: (0) "Are you sure?", (1) a suggested answer, (2) the same from someone claiming to teach the
subject, (3) the same with a claimed textbook reference. Correct answers are pushed toward a wrong option, and
wrong answers toward the correct one.

**Statistics.** Three runs per setup for calibration and abstention. Intervals are 95% bootstrap intervals over
questions, and thinking on and off are compared on the same questions. A hand check of 80 replies
supported the automatic scoring (Appendix A).

## 4. Results

**Table 1. Summary of the three checks.** Overconfidence is mean stated confidence minus accuracy. Abstention
columns use the plain prompt; "known" means the same model answered the question correctly in another reply.
The last column is the share of initially correct answers given up after all four challenges. Full tables with
intervals are in Appendix B.

| Model | Thinking | Accuracy % | Overconf. (pts) | Abstains, invented % | Abstains, known % | Gives up correct % |
|--------------------|---------|----------|----------|------------|------------|------------|
| MiniCPM5-2B | on | 78.3 | 6.5 | 99 | 37 | 35 |
|  | off | 73.7 | 10.6 | 95 | 45 | 69 |
| K2 Horizon 3.7B | on | 78.5 | 8.6 | 63 | 4 | 29 |
|  | low | 73.8 | 14.1 | 63 | 8 | 52 |
| K2 Horizon 7B | on | 83.0 | 7.1 | 53 | 2 | 30 |
|  | low | 80.2 | 9.7 | 48 | 1 | 43 |
| Qwen3.5-4B | on | 86.3 | 8.5 | 88 | 5 | 38 |
|  | off | 80.8 | 12.6 | 39 | 6 | 87 |

**Calibration.** Every setup is overconfident: stated confidence is 6.5 to 14.1 points above accuracy, and
every interval excludes zero. Answers stated at 90% or more were right 84% to 91% of the time. On the same
questions, thinking lowered the Brier score in all four models (by 0.032 to 0.045) and lowered overconfidence
by 2.8 to 5.6 points (clear for three models, borderline for K2 Horizon 7B).

**Abstention.** K2 Horizon answers questions about things that do not exist: the 7B model answered 40% to 52%
of the invented-entity questions, and the 3.7B model 20% to 37%. Asked "Which element did the physicist Ilse
Brandauer isolate in 1931?" (she does not exist), the two K2 Horizon models answered 16 of 24 times and named
14 different elements, including "Helvetium", which does not exist either. MiniCPM5 goes the other way. It
abstained on 87% to 100% of unanswerable questions, but also on 57% to 82% of answerable ones, including 36% to
76% of questions it got right in another reply. Thinking fixed this for Qwen3.5 only: it abstained on 59% to
63% of unanswerable questions without thinking and 89% to 91% with it (+28 points [+18, +38]).

The penalty prompt raised abstention on unanswerable questions by 2 to 12 points (clear in 3 of 8 setups), but
it raised abstention on answerable questions too. The +1/−3/0 score improved clearly in only one setup,
MiniCPM5 with thinking (Appendix B, Figure B2).

**Pushback.** A bare "Are you sure?" changed 0% to 4% of correct answers, against 46% for 2023 models in
FlipFlop [6]. Naming a wrong answer is different. By the end of the four challenges the models had given up 29%
to 87% of their correct answers (Figure 1), and 90% to 100% of those switches went to exactly the option the
user named. On questions answered correctly in both modes, thinking reduced giving up by 17 points (K2 Horizon
7B) to 50 points (Qwen3.5), and every interval excludes zero. A model's
first stated confidence predicts which answers it will drop (AUROC 0.66 to 0.79), but does not protect them:
answers stated at 95% or more were still given up 18% to 86% of the time.

![Figure 1. Share of initially correct answers given up, cumulative over the four pushback steps. Blue is thinking on, orange is thinking off or low.](../figures/pushback.png){width=5.8in}

## 5. Discussion and Limitations

These models do have information about their own reliability: their
confidence ranks right answers above wrong ones and predicts which answers they will drop. But they do not act
on it. For someone deploying a small model, three things follow. Thinking is the most useful setting you
control, though median reply length went from 110–420 tokens to 580–3,400. The weak spot has moved from bare
doubt to a suggested answer, which is exactly what an agent reading other people's text will meet. And a small
model does not inherit the honesty of its flagship.

**Limitations.** The samples are small (200 calibration questions, 50 + 50 abstention questions), so
differences of a few points are not reliable. "Thinking off" and sampling settings are not the same across
models. I measured stated confidence only, the pushback messages are fixed templates, MMLU-Pro may be in the
training data, and everything is in English. The full list is in Appendix A.

**Future work.** More small models, a larger set of unanswerable questions, and a comparison of stated
confidence with token probabilities.

## 6. Conclusion

Four new small open models are all overconfident, none declines exactly what it cannot know, and all can be
talked out of correct answers by a user who names an alternative. Turning thinking on is the one setting that
improves all three behaviours, and stating a penalty for wrong answers does not replace it.

## Code and Data

- Code repository: https://github.com/Ashwinhegde19/knows-what-it-knows
- Data: questions in `data/`, every raw reply (with thinking text) in `results/raw/`, scored tables in `results/`
- Datasets used: MMLU-Pro [7], SelfAware [8]

## References

1. Artificial Analysis (2026). K2 Horizon 375B A23B on AA-Omniscience. Post on X.
   https://x.com/ArtificialAnlys/status/2095504804651151758
2. Botas, A., de Font-Reaulx, P., Hewitt, L. (2026). Pander Score: A Continuous Measure of Sycophancy as
   Epistemic Deference. arXiv:2606.07897.
3. Fanous, A., et al. (2025). SycEval: Evaluating LLM Sycophancy. AIES 2025. arXiv:2502.08177.
4. ffrench-Constant, M., Yang, D., Huang, X., Kapoor, S. (2026). ConfidenceBench: Evaluating Confidence
   Calibration in Large Language Models. arXiv:2607.20526.
5. Kalai, A. T., Nachum, O., Vempala, S. S., Zhang, E. (2025). Why Language Models Hallucinate.
   arXiv:2509.04664.
6. Laban, P., Murakhovs'ka, L., Xiong, C., Wu, C.-S. (2023). Are You Sure? Challenging LLMs Leads to
   Performance Drops in The FlipFlop Experiment. arXiv:2311.08596.
7. Wang, Y., et al. (2024). MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding
   Benchmark. NeurIPS 2024 Datasets and Benchmarks. arXiv:2406.01574.
8. Yin, Z., et al. (2023). Do Large Language Models Know What They Don't Know? Findings of ACL 2023.
   arXiv:2305.18153.
9. Model cards on Hugging Face: IFM/K2-Horizon-3.7B, IFM/K2-Horizon-7B, openbmb/MiniCPM5-2B, Qwen/Qwen3.5-4B
   (sampling settings and thinking switches, checked 13 November 2026).

## Appendix A. Limitations and dual-use considerations

**Limitations.**

- Small samples: 200 calibration questions, 50 unanswerable and 50 answerable questions, three runs each. The
  intervals are wide for differences of a few points.
- Stated confidence is one signal. Token probabilities or agreement across samples might be better or worse
  calibrated. I did not compare them.
- "Thinking off" is not the same thing across models, because K2 Horizon cannot switch thinking off.
- Each model runs at its own recommended sampling. That is how the models are meant to be used, but it means
  sampling differs between models.
- Abstention is detected by the ABSTAIN token plus a phrase list, and answerable questions are graded by lenient
  matching against the gold aliases. In a hand check of 80 sampled replies, the abstention label agreed on 80 of
  80 and the right/wrong label on 29 of 32 answered questions. The three misses were right answers marked wrong,
  so correctness on answerable questions is slightly underestimated. This hand check was done by the AI
  assistant (see the LLM usage statement), and is recorded in `results/AUDIT.md`.
- A question counts as "known" if the model answered it correctly at least once. With sampling at temperature
  0.7 to 1.0, a lucky guess can count as known.
- Pushback uses each model's run-1 answers only, and the questions that start right differ between models and
  modes. The thinking comparison in Section 4 is therefore limited to questions right in both modes.
- At low effort K2 Horizon often closes its thinking with a different tag than it opened (97% of 7B replies,
  59% of 3.7B), so the server files the whole reply as thinking. I take the visible answer from after the last
  closing tag and flag every such reply in the raw data.
- Most requests ran on A100 GPUs, but the first K2 Horizon requests ran on an L40S. The GPU was not recorded per
  request. Sampling noise is far larger than any numeric difference between GPUs.
- The pushback ladder uses fixed templates and a claimed citation that is not real. Real users argue with
  content, which may move models more.
- MMLU-Pro questions may appear in training data, which would raise accuracy and confidence together.
- 1% to 2% of K2 Horizon's thinking replies (36 of 2,400) hit the 32,768-token limit with no answer. They were
  not repetition loops; the model kept reasoning in new words. These count as unparseable replies.
- English only.

**Dual use.** The pushback results show which kinds of pressure make small models drop correct answers. Someone
could use that to manipulate a deployed assistant. But the techniques (disagreeing, claiming expertise, citing a
source) are already common and well documented. The main use of these results is defensive: choosing models and
settings for unsupervised use, and testing fixes. No harmful content was generated or used.

## Appendix B. Full results

Intervals in brackets are 95% bootstrap intervals over questions.

**Table B1. Calibration.** 200 questions × 3 runs per row. Acc. = accuracy. Think = thinking mode. Conf. = mean stated confidence. Overconf. = Conf. minus Acc. Skill = Brier improvement over always stating the model's own accuracy (0 = no better). AUROC = how well confidence separates right from wrong answers (0.5 = not at all). Right at ≥90% = accuracy of answers stated at 90% confidence or more; Share ≥90% = the share of all answers stated that high. Accuracy intervals are about ±5 points.

| Model | Think | Acc. % | Conf. % | Overconf. (pts) [95% CI] | Brier [95% CI] | Skill | AUROC [95% CI] | Right at ≥90% % | Share ≥90% % |
|---------------------|----------|---------|---------|-----------------|------------------|--------|----------------|------------|-----------|
| MiniCPM5-2B | on | 78.3 | 87.4 | 6.5 [2.3, 10.9] | 0.143 [0.113, 0.176] | 0.16 | 0.77 [0.71, 0.83] | 90.8 | 69 |
|  | off | 73.7 | 85.4 | 10.6 [6.6, 14.9] | 0.175 [0.143, 0.210] | 0.10 | 0.74 [0.68, 0.79] | 84.4 | 67 |
| K2 Horizon 3.7B | on | 78.5 | 90.7 | 8.6 [4.5, 13.3] | 0.139 [0.108, 0.173] | 0.18 | 0.78 [0.73, 0.83] | 89.7 | 73 |
|  | low | 73.8 | 89.3 | 14.1 [9.5, 18.7] | 0.184 [0.148, 0.219] | 0.05 | 0.75 [0.69, 0.80] | 85.4 | 71 |
| K2 Horizon 7B | on | 83.0 | 93.5 | 7.1 [3.1, 11.4] | 0.114 [0.082, 0.148] | 0.20 | 0.74 [0.66, 0.81] | 91.0 | 83 |
|  | low | 80.2 | 90.0 | 9.7 [5.3, 14.2] | 0.145 [0.111, 0.182] | 0.09 | 0.78 [0.73, 0.84] | 87.9 | 76 |
| Qwen3.5-4B | on | 86.3 | 95.1 | 8.5 [4.7, 12.5] | 0.111 [0.080, 0.147] | 0.06 | 0.82 [0.76, 0.87] | 89.6 | 89 |
|  | off | 80.8 | 95.6 | 12.6 [8.6, 16.9] | 0.144 [0.111, 0.179] | 0.07 | 0.81 [0.75, 0.86] | 85.6 | 92 |

**Table B2. Abstention.** 50 unanswerable and 50 answerable questions × 3 runs per row. Unans. = unanswerable questions; Answ. = answerable questions. "Invented" is the 25 unanswerable questions about people, places and products that do not exist. "Known" = answerable questions the same model answered correctly in at least one reply. Penalty score: +1 right, −3 wrong, 0 abstain, on answerable questions.

| Model | Think | Prompt | Unans.: abstains % [95% CI] | Invented: abstains % | Answ.: abstains % [95% CI] | Known: abstains % | Answ.: wrong % | Penalty score [95% CI] |
|--------------------|----------|------------|-----------------|-------------|-----------------|------------|-----------|-------------------|
| MiniCPM5-2B | on | plain | 87 [78, 95] | 99 | 58 [47, 69] | 37 | 17 | −0.27 [−0.52, −0.03] |
|  |  | penalty | 93 [85, 99] | 100 | 57 [45, 69] | 36 | 9 | +0.09 [−0.16, +0.32] |
|  | off | plain | 88 [80, 95] | 95 | 63 [51, 73] | 45 | 17 | −0.29 [−0.56, −0.04] |
|  |  | penalty | 100 [100, 100] | 100 | 82 [72, 91] | 76 | 7 | −0.09 [−0.29, +0.07] |
| K2 Horizon 3.7B | on | plain | 65 [54, 76] | 63 | 7 [2, 12] | 4 | 35 | −0.45 [−0.84, −0.09] |
|  |  | penalty | 73 [62, 83] | 71 | 15 [9, 23] | 11 | 29 | −0.30 [−0.70, +0.10] |
|  | low | plain | 63 [52, 73] | 63 | 13 [7, 21] | 8 | 41 | −0.76 [−1.21, −0.34] |
|  |  | penalty | 75 [63, 85] | 80 | 23 [14, 32] | 16 | 37 | −0.72 [−1.17, −0.30] |
| K2 Horizon 7B | on | plain | 58 [46, 69] | 53 | 4 [1, 8] | 2 | 29 | −0.21 [−0.68, +0.21] |
|  |  | penalty | 63 [51, 74] | 59 | 7 [2, 15] | 4 | 29 | −0.25 [−0.67, +0.15] |
|  | low | plain | 57 [45, 69] | 48 | 5 [1, 10] | 1 | 31 | −0.30 [−0.73, +0.13] |
|  |  | penalty | 63 [51, 74] | 60 | 9 [4, 16] | 4 | 27 | −0.19 [−0.58, +0.22] |
| Qwen3.5-4B | on | plain | 89 [81, 95] | 88 | 13 [4, 23] | 5 | 21 | +0.02 [−0.43, +0.42] |
|  |  | penalty | 91 [83, 97] | 95 | 14 [6, 23] | 6 | 20 | +0.06 [−0.37, +0.44] |
|  | off | plain | 59 [47, 71] | 39 | 7 [2, 13] | 6 | 37 | −0.57 [−1.03, −0.11] |
|  |  | penalty | 63 [52, 74] | 53 | 11 [5, 19] | 7 | 33 | −0.41 [−0.86, −0.02] |

**Table B3. Pushback.** Each model's run-1 calibration answers, challenged up to four times. "Gave up" = an initially correct answer changed to a wrong one. "Corrected" = an initially wrong answer changed to the right one. "Sure?" is the bare "Are you sure?" challenge. The two "conf." columns split initially correct answers by the confidence the model first stated. AUROC = how well that first confidence predicts which correct answers are given up (0.5 = not at all).

| Model | Think | Right (n) | Gave up after "Sure?" % | Gave up by end % [95% CI] | ≥95% conf.: gave up % (n) | <95% conf.: gave up % (n) | Wrong (n) | Corrected by end % [95% CI] | AUROC [95% CI] |
|------------------|----------|----------|-----------|----------------|-------------|-------------|-----------|----------------|---------------|
| MiniCPM5-2B | on | 155 | 2.6 | 35 [27, 43] | 23 (109) | 63 (46) | 37 | 95 [86, 100] | 0.76 [0.67, 0.83] |
|  | off | 140 | 2.9 | 69 [61, 76] | 53 (86) | 93 (54) | 57 | 95 [88, 100] | 0.79 [0.72, 0.85] |
| K2 Horizon 3.7B | on | 157 | 2.5 | 29 [22, 36] | 18 (107) | 55 (49) | 33 | 82 [70, 94] | 0.78 [0.71, 0.86] |
|  | low | 145 | 4.1 | 52 [43, 59] | 39 (99) | 78 (46) | 52 | 79 [67, 90] | 0.73 [0.65, 0.81] |
| K2 Horizon 7B | on | 166 | 3.6 | 30 [23, 36] | 18 (122) | 61 (44) | 27 | 70 [52, 85] | 0.78 [0.70, 0.85] |
|  | low | 158 | 1.9 | 43 [35, 51] | 36 (118) | 65 (40) | 41 | 98 [93, 100] | 0.66 [0.57, 0.74] |
| Qwen3.5-4B | on | 173 | 0.0 | 38 [31, 45] | 29 (145) | 86 (28) | 27 | 96 [89, 100] | 0.78 [0.71, 0.84] |
|  | off | 163 | 0.6 | 87 [82, 92] | 86 (147) | 100 (16) | 32 | 100 [100, 100] | 0.75 [0.67, 0.81] |

![Figure B1. Reliability diagrams: stated confidence against actual accuracy for each model. Points below the diagonal are overconfident.](../figures/reliability.png)

![Figure B2. Abstention on unanswerable and answerable questions, by model, thinking mode and prompt. A model that knows what it knows would be high on unanswerable questions and low on answerable ones.](../figures/abstention.png)

## Appendix C. Settings and reproducibility

**Sampling.** K2 Horizon: temperature 1.0, top-p 0.95. MiniCPM5: temperature 1.0, top-p 0.95, min-p 0. Qwen3.5
with thinking: temperature 1.0, top-p 0.95, top-k 20, presence penalty 1.5. Qwen3.5 without thinking:
temperature 0.7, top-p 0.8, top-k 20, presence penalty 1.5. Output limit 32,768 tokens for all models (K2
Horizon's stated minimum). Served with vLLM 0.33.0.

**Abstention scoring.** A reply abstains if its final line contains ABSTAIN, otherwise if it contains a listed
phrase such as "cannot be determined". The penalty score is +1 for a right answer, −3 for a wrong one and 0 for
abstaining, on answerable questions.

**Reproducing the numbers.** Every request is one JSON line in `results/raw/`, with the full reply, thinking
text, token counts and finish reason. `analysis/score.py` recomputes every number from those files,
`analysis/paired.py` the same-question differences, `analysis/tables.py` the tables and `analysis/figures.py`
the figures. Datasets are rebuilt by `scripts/build_datasets.py` and `scripts/build_controls.py` (seed
20261113).

**Pre-existing work.** Before the sprint the repository held only data preparation and model-serving scripts,
listed in the README's Provenance section. All evaluation code, runs, figures and this report were produced
during the sprint.

## LLM Usage Statement

I used Claude (Anthropic), through Claude Code, heavily in this project. Claude wrote most of the evaluation
and scoring code, ran the experiments, did the hand check of 80 replies, and wrote the first draft of this
report. I chose the topic, the models and the three checks, made the decisions along the way (for example
running each model at its recommended settings, and which GPUs to pay for), and reviewed and edited the report.
Every number in the report is generated by scripts from the raw replies, which are public in the repository.
