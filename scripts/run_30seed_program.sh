#!/usr/bin/env bash
# FreightBidBench v0.4 30-seed empirical program.
#
# Reproduces the paper's empirical tables end to end:
#   Phase 0: mild dual solve + dual-price/value-togo table fits
#            (the paper's corrected mild rows use these fitted tables)
#   Phase A: 30-seed policy comparisons, pairs 1-30 (pair 0 excluded:
#            its eval stream fitted the frozen dual tables)
#   Phase B: certificate bound solves (45 iterations, 4 workers) on the
#            eval streams of pairs 1-10 for tight and scarce
#
# Fail-fast and repo-relative; resumable (completed cert solves and an
# existing mild dual solve are skipped).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p logs benchmark_runs/v04_dev/seed30 \
  benchmark_runs/v04_dev/seed30_mild_fitted benchmark_runs/v04_dev/certs

CONFIG=configs/freightbidbench_v03_scenarios.json
TRAIN_SEED=20260507 # pair-0 eval stream; all tables are fitted here

dual_dir_for() {
  # Canonical training-path dual solves (the checked-in artifacts the
  # paper's tables were fitted from). A clean checkout re-solves any
  # that are missing.
  case "$1" in
    tight) echo benchmark_runs/lagrangian_bound_full_v6_warm ;;
    scarce) echo benchmark_runs/lagrangian_bound_scarce_full ;;
    mild) echo benchmark_runs/v04_dev/lagrangian_mild ;;
  esac
}

echo "=== $(date '+%F %H:%M') PHASE 0: training duals + table fits (all scenarios) ==="
for scen in tight scarce mild; do
  dir="$(dual_dir_for "$scen")"
  if [ ! -f "$dir/lagrangian_dual_prices.csv" ]; then
    echo "--- $(date '+%F %H:%M') dual solve: $scen (missing at $dir)"
    nice -n 5 python3 -u scripts/run_lagrangian_bound.py --config "$CONFIG" \
      --scenario "$scen" --eval-seed "$TRAIN_SEED" \
      --iterations 45 --step-scale 100.0 --workers 4 --verbose \
      --output-dir "$dir" \
      >"logs/lagrangian_${scen}.log" 2>&1
  else
    echo "--- skip $scen dual solve (already present at $dir)"
  fi
  python3 scripts/fit_dual_prices.py --config "$CONFIG" --scenario "$scen" \
    --eval-seed "$TRAIN_SEED" \
    --duals-csv "$dir/lagrangian_dual_prices.csv"
  python3 scripts/fit_value_togo.py --config "$CONFIG" --scenario "$scen" \
    --eval-seed "$TRAIN_SEED" \
    --duals-csv "$dir/lagrangian_dual_prices.csv"
done

echo "=== $(date '+%F %H:%M') PHASE A: 30-seed policy program ==="
declare -a pids=()
for scen in tight scarce; do
  nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
    --config "$CONFIG" \
    --scenarios "$scen" --first-pair 1 --pair-count 30 --label-limit 200 \
    --policies bid_price,surrogate_linear,dual_price,dual_price_vf,rollout_teacher \
    --output-dir "benchmark_runs/v04_dev/seed30/$scen" \
    >"logs/seed30_$scen.log" 2>&1 &
  pids+=($!)
done
nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
  --config "$CONFIG" \
  --scenarios mild --first-pair 1 --pair-count 30 --label-limit 200 \
  --policies bid_price,surrogate_linear,dual_price,dual_price_vf,rollout_teacher \
  --output-dir benchmark_runs/v04_dev/seed30_mild_fitted \
  >"logs/seed30_mild_fitted.log" 2>&1 &
pids+=($!)
for pid in "${pids[@]}"; do wait "$pid"; done
echo "=== $(date '+%F %H:%M') PHASE A done ==="

echo "=== $(date '+%F %H:%M') PHASE B: certificate solves (pairs 1-10) ==="
for i in $(seq 1 10); do
  eval_seed=$((20260506 + 2 * i + 1))
  for scen in tight scarce; do
    out="benchmark_runs/v04_dev/certs/${scen}_${eval_seed}"
    if [ -f "$out/lagrangian_bound_report.md" ]; then
      echo "--- skip $scen seed $eval_seed (already done)"
      continue
    fi
    echo "--- $(date '+%F %H:%M') cert solve: $scen eval_seed=$eval_seed"
    nice -n 5 python3 -u scripts/run_lagrangian_bound.py \
      --config "$CONFIG" \
      --scenario "$scen" --eval-seed "$eval_seed" \
      --iterations 45 --step-scale 100.0 --workers 4 --verbose \
      --output-dir "$out" \
      >"logs/cert_${scen}_${eval_seed}.log" 2>&1
  done
done
echo "=== $(date '+%F %H:%M') PHASE B done — program complete ==="
