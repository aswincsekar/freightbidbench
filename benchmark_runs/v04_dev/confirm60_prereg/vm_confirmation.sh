#!/bin/bash
# Locked confirmation program: thirty unused train/eval pairs (31-60),
# run once with frozen code and hyperparameters. These pairs become
# the paper's primary confirmatory set; pairs 1-30 are relabeled
# development/validation. Waits for converge_scaling.sh to finish.
set -uo pipefail
cd ~/fbb_trackb
LOG=~/fbb_trackb/logs/confirmation.log
mkdir -p logs
while pgrep -f converge_scaling.sh > /dev/null; do sleep 300; done
# Pre-registration gate: wait for the pushed freeze commit flag.
while [ ! -f ~/fbb_trackb/FREEZE_PUSHED ]; do sleep 300; done
echo "=== $(date '+%F %H:%M') CONFIRMATION START (pairs 31-60)" >> "$LOG"
CFG=configs/freightbidbench_v03_scenarios.json
declare -a pids=()
for scen in tight scarce; do
  nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
    --config "$CFG" --scenarios "$scen" --first-pair 31 --pair-count 30 \
    --label-limit 200 \
    --policies bid_price,surrogate_linear,dual_price,dual_price_vf,rollout_teacher \
    --output-dir "benchmark_runs/v04_dev/confirm60/$scen" \
    >> "logs/confirm_$scen.log" 2>&1 &
  pids+=($!)
done
nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
  --config "$CFG" --scenarios mild --first-pair 31 --pair-count 30 \
  --label-limit 200 \
  --policies bid_price,surrogate_linear,dual_price,dual_price_vf,rollout_teacher \
  --output-dir benchmark_runs/v04_dev/confirm60/mild \
  >> logs/confirm_mild.log 2>&1 &
pids+=($!)
for pid in "${pids[@]}"; do wait "$pid"; done
echo "=== $(date '+%F %H:%M') headline arms done; DLP + naive" >> "$LOG"
for scen_h in "tight 3" "scarce 6" "mild 1"; do
  set -- $scen_h
  FREIGHTBID_DLP_RESOLVE_HOURS=$2 nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
    --config "$CFG" --scenarios "$1" --first-pair 31 --pair-count 30 \
    --policies dlp_resolve \
    --output-dir "benchmark_runs/v04_dev/confirm60/dlp_tuned/$1" \
    >> "logs/confirm_dlp_$1.log" 2>&1
  nice -n 5 python3 -u scripts/run_dual_price_experiment.py \
    --config "$CFG" --scenarios "$1" --first-pair 31 --pair-count 30 \
    --policies dual_price_vf_naive \
    --output-dir "benchmark_runs/v04_dev/confirm60/naive/$1" \
    >> "logs/confirm_naive_$1.log" 2>&1
done
echo "=== $(date '+%F %H:%M') CONFIRMATION DONE" >> "$LOG"
