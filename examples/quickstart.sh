#!/usr/bin/env bash
set -euo pipefail

python3 scripts/run_freightbidbench.py \
  --preset smoke \
  --output-dir benchmark_runs/quickstart

python3 scripts/plot_freightbidbench.py \
  --run-dir benchmark_runs/quickstart

echo "Wrote benchmark_runs/quickstart"
