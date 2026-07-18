#!/usr/bin/env bash
# FreightBidBench v0.4 30-seed empirical program (workplan Path C, section 5).
# Phase A: 30-seed policy comparisons on pairs 1-30 (pair 0 excluded: its
#          eval stream fitted the frozen dual tables), one process per
#          scenario in parallel.
# Phase B: certificate bound solves (45 iterations, 4 workers) on the eval
#          streams of pairs 1-10 for tight and scarce.
set -u
cd "$HOME/freightbidbench"
mkdir -p logs benchmark_runs/v04_dev/seed30 benchmark_runs/v04_dev/certs

echo "=== $(date '+%F %H:%M') PHASE A: 30-seed policy program ==="
for scen in tight scarce mild; do
  nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
    --config configs/freightbidbench_v03_scenarios.json \
    --scenarios "$scen" --first-pair 1 --pair-count 30 --label-limit 200 \
    --policies bid_price,surrogate_linear,dual_price,dual_price_vf,rollout_teacher \
    --output-dir "benchmark_runs/v04_dev/seed30/$scen" \
    > "logs/seed30_$scen.log" 2>&1 &
done
wait
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
      --config configs/freightbidbench_v03_scenarios.json \
      --scenario "$scen" --eval-seed "$eval_seed" \
      --iterations 45 --step-scale 100.0 --workers 4 --verbose \
      --output-dir "$out" \
      > "logs/cert_${scen}_${eval_seed}.log" 2>&1
  done
done
echo "=== $(date '+%F %H:%M') PHASE B done — program complete ==="
