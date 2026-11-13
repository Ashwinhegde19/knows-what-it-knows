#!/usr/bin/env bash
# Full sprint run: every model x thinking mode. Calibration (3 runs) then pushback; abstention (3 runs) alongside.
# Four processes per model x 16 requests = 64 in flight, what one GPU container accepts (max_inputs=64).
set -u
cd "$(dirname "$0")/.."
mkdir -p logs/runs
MODELS=${MODELS:-"IFM/K2-Horizon-3.7B IFM/K2-Horizon-7B openbmb/MiniCPM5-2B Qwen/Qwen3.5-4B"}
for M in $MODELS; do
  S=$(echo "${M##*/}" | tr 'A-Z' 'a-z')
  for MODE in think nothink; do
    ( .venv/bin/python -m kwik.run calibration --model "$M" --mode "$MODE" --runs 3 --concurrency 16 \
      && .venv/bin/python -m kwik.run pushback --model "$M" --mode "$MODE" --concurrency 16 ) \
      > "logs/runs/${S}_${MODE}_calib_push.log" 2>&1 &
    .venv/bin/python -m kwik.run abstention --model "$M" --mode "$MODE" --runs 3 --concurrency 16 \
      > "logs/runs/${S}_${MODE}_abstention.log" 2>&1 &
  done
done
wait
echo "all runs finished $(date)"
