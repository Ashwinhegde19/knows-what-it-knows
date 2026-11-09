# Question sets

Built by `scripts/build_datasets.py` with seed 20261113. Rerunning the script reproduces both files exactly.

## factual_200.csv

200 multiple-choice questions from the MMLU-Pro test split (TIGER-Lab/MMLU-Pro, Hugging Face), 14 or more per subject across its 14 subjects. Used for the calibration check and the pushback check.

Each question is reduced from MMLU-Pro's 10 options to 4: the gold answer plus 3 randomly chosen wrong options, shuffled. Reasons: it matches ConfidenceBench's 4-choice format, so the calibrated-random Brier baseline is the same 0.1875, and small models get enough questions right to make the pushback test meaningful. The original option indices are kept so anyone can recover the 10-option version. Questions over 1,200 characters and wrong options that are formula fragments were excluded before sampling.

Columns: `id`, `category`, `question`, `option_A..D`, `answer` (letter), `mmlu_pro_question_id`, `mmlu_pro_answer`, `mmlu_pro_original_option_indices`, `mmlu_pro_n_options`, `source`.

## unanswerable_50.csv

50 questions with no correct answer. The right response is to say so. Used for the abstention check.

- `kind = missing_info` (25): arithmetic word problems from the SelfAware dataset (Yin et al., 2023, Apache-2.0) in which a needed quantity is missing or replaced by "some" or "more". Filtered to questions containing a number and a how-many / how-much / how-long phrasing, no negative numbers, 40 to 300 characters.
- `kind = fabricated` (25): questions about people, places, products and events that do not exist, written for this project.

Columns: `id`, `kind`, `question`, `selfaware_question_id`, `source`.

## Licences

MMLU-Pro is MIT. SelfAware is Apache-2.0 (copy in `raw/selfaware/LICENSE`). The fabricated questions are released with this repo under MIT.
