#!/bin/bash
# Cross-fitted scaling evaluation: for each scaling cell, fit the
# dual-price tables from one seed's solve and evaluate the policy on
# a DIFFERENT seed's stream (all ordered train != eval pairs among
# the three fresh seeds). Removes the in-sample fitting leakage from
# the Table 3 policy-vs-rollout comparison; certificates still divide
# by the evaluation stream's own bound. Sequential because the fit
# scripts write shared global table CSVs.
set -euo pipefail
cd "$(dirname "$0")/.."
SCFG=configs/freightbidbench_v04_dev_scaling.json
OUT=benchmark_runs/trackb/scaling_crossfit
mkdir -p "$OUT"

for cell in tight_x05 tight_x1 tight_x2; do
  for train in 20260509 20260511 20260513; do
    # Corrected-solver duals (invalid originals retained under
    # trackb/scaling for the audit).
    d="benchmark_runs/v041_fix/scaling/${cell}_${train}"
    python3 scripts/fit_dual_prices.py --config "$SCFG" --scenario "$cell" \
      --eval-seed "$train" --duals-csv "$d/lagrangian_dual_prices.csv"
    python3 scripts/fit_value_togo.py --config "$SCFG" --scenario "$cell" \
      --eval-seed "$train" --duals-csv "$d/lagrangian_dual_prices.csv"
    for eval in 20260509 20260511 20260513; do
      [ "$eval" = "$train" ] && continue
      pair=$(( (eval - 20260507) / 2 ))
      dir="$OUT/${cell}_train${train}_eval${eval}"
      nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
        --config "$SCFG" --scenarios "$cell" \
        --first-pair "$pair" --pair-count 1 \
        --policies dual_price_vf \
        --output-dir "$dir"
      # The runner CSV's train_seed column records the paired stream's
      # nominal seed; the fitted tables' actual provenance is here.
      printf '{\n "table_train_seed": %s,\n "table_source": "benchmark_runs/v041_fix/scaling/%s_%s/lagrangian_dual_prices.csv",\n "eval_seed": %s\n}\n' \
        "$train" "$cell" "$train" "$eval" > "$dir/manifest.json"
    done
  done
done
python3 scripts/aggregate_scaling_crossfit.py
echo "SCALING CROSSFIT DONE"
