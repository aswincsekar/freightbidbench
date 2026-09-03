#!/bin/bash
# Sound certification pass: evaluate every finished dual solve's
# incumbent duals with the sound per-truck solver (scripts/certify_bound.py),
# writing sound_bound_summary.csv beside each solve. Four single-worker
# certifications run concurrently (measured throughput beats one
# four-worker evaluation); resume-safe (existing outputs are skipped).
set -uo pipefail
cd ~/fbb_trackb
mkdir -p logs
LOG=logs/certify.log
echo "=== $(date '+%F %H:%M') CERTIFY START" >> "$LOG"
{
  for d in benchmark_runs/v041_fix/lagrangian_tight \
           benchmark_runs/v041_fix/lagrangian_scarce \
           benchmark_runs/v041_fix/lagrangian_mild; do echo "$d"; done
  ls -d benchmark_runs/v041_fix/certs/*/ benchmark_runs/v041_fix/subcritical/*/ \
        benchmark_runs/v041_fix/scaling/*/ | sed 's#/$##'
} | grep -v '\.log$' > logs/certify_dirs.txt
wc -l logs/certify_dirs.txt >> "$LOG"
xargs -P 4 -I{} sh -c \
  'nice -n 5 python3 -u scripts/certify_bound.py --solve-dir "{}" --workers 1 >> logs/certify.log 2>&1' \
  < logs/certify_dirs.txt
echo "=== $(date '+%F %H:%M') CERTIFY DONE" >> "$LOG"
