#!/usr/bin/env bash
# Waits for the K2 Horizon runs to finish, then runs MiniCPM5-2B and Qwen3.5-4B (GPUs start only a few at a time).
cd "$(dirname "$0")/.."
while pgrep -f "kwik[.]run .*K2-Horizon" > /dev/null; do sleep 60; done
echo "K2 runs finished $(date); starting MiniCPM5 and Qwen3.5"
MODELS="openbmb/MiniCPM5-2B Qwen/Qwen3.5-4B" scripts/run_all.sh
