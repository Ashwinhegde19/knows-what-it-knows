# Hand audit of the abstention scorer

80 replies drawn by `analysis/audit_sample.py` (seed 20261114): 40 the scorer marked as abstaining, 40 not,
across all models, modes and conditions. Read one by one by Claude (the AI assistant used in this project);
the author should spot-check before citing. Labels are in `audit_abstention.csv`.

- Abstained or not: 80 of 80 agree.
- Right or wrong, for the 32 answered answerable questions: 29 of 32 agree (90.6%). All 3 disagreements
  were right answers the alias match missed ("Outdoors" for outside, "Meat Loaf" for meatloaf,
  "Humanity" for people). So correctness on answerable questions is slightly underestimated.
- After this audit the matcher also accepts spacing variants for aliases of 5+ letters, which fixes
  the "Meat Loaf" case. The other two remain misses; scores are rerun with the fix.
