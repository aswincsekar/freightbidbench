# FreightBidBench v0.3 Relaxed Full-Horizon Bound

## Purpose

Phase B adds a paper-scale ceiling that is separate from the exact truncated DP.
The exact DP remains the trustworthy small-instance diagnostic; this relaxed
bound is the full-horizon ceiling to report with explicit caveats.

The implementation is dependency-free and lives in
`scripts/run_relaxed_hindsight_bound.py`.

## Relaxation

The script reports two upper bounds and uses the smaller one:

- Positive-profit relaxation: accepts every realized load with positive
  fresh-truck profit, ignoring fleet, location, timing, and sequencing.
- Fractional truck-hour relaxation: ignores location and sequencing, charges
  each profitable load a lower-bound busy time, and solves the fractional
  truck-hour knapsack.

Both bounds add a terminal fleet-value upper bound that allows every truck to
end in the best-valued state. This makes the result a ceiling, not a feasible
plan.

## Commands

Smoke check:

```bash
make relaxed-bound-smoke
```

One-seed full-horizon checks with rollout comparison:

```bash
python3 scripts/run_relaxed_hindsight_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario tight \
  --policies accept_all_feasible,bid_price,rollout_teacher \
  --output-dir benchmark_runs/v03_sweeps/relaxed_bound_tight_full_rollout

python3 scripts/run_relaxed_hindsight_bound.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --scenario scarce \
  --policies accept_all_feasible,bid_price,rollout_teacher \
  --output-dir benchmark_runs/v03_sweeps/relaxed_bound_scarce_full_rollout
```

## Result

| Scenario | Relaxed Bound | Best Simple | Simple Retention | Rollout | Rollout Retention |
| --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | $2,377,500 | $1,114,158 | 46.9% | $1,273,395 | 53.6% |
| `scarce` | $2,675,525 | $808,139 | 30.2% | $1,065,656 | 39.8% |

The bound is intentionally loose. In `tight`, the fractional truck-hour
constraint does not bind beyond the positive-profit relaxation. In `scarce`, it
tightens the positive-profit bound by about `$35k`, but the dominant looseness
is still the relaxed location and sequencing assumptions.

## Decision

Keep this as the v0.3 full-horizon relaxed ceiling. It is good enough for the
paper if reported honestly as a loose upper bound and paired with exact DP on
small prefixes.
