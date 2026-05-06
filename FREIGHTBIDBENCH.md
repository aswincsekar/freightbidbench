# FreightBidBench v0.2

FreightBidBench v0.2 is a public-calibrated synthetic benchmark for real-time
truckload bid acceptance.

The benchmark is designed to be publishable as a standalone artifact before the
method paper is finished. Its purpose is to let other researchers run the same
closed-loop freight environment, compare accept/reject policies under identical
stochastic seeds, and report latency-profit frontiers.

## What The Benchmark Tests

At each decision point, a candidate load is tendered to the carrier. A policy
must decide whether to accept or reject it. Accepted loads move trucks through
the network and make those trucks unavailable until delivery, so early decisions
affect later opportunity cost.

The benchmark reports:

- closed-loop profit,
- profit retention versus a finite rollout teacher,
- mean and p95 decision latency,
- truck utilization,
- rejected loads and no-truck outcomes,
- infeasible accept attempts caused by pickup/delivery windows,
- simplified HOS rest hours,
- deadhead miles to pickup,
- stochastic pickup and dropoff yard-delay hours,
- cascade rollout-call share,
- held-out rollout-label fit for learned surrogates.

The finite rollout teacher is a stochastic benchmark, not an oracle. A cheaper
policy can exceed 100% retention if it earns higher realized closed-loop profit
than the finite-lookahead teacher on the same seed average.

## Feasibility Layer

Version 0.2 adds a first operational feasibility layer:

- individual truck records rather than only regional truck counts,
- pickup reach time inside the origin market,
- pickup appointment earliest/latest times,
- delivery appointment earliest/latest times,
- simplified HOS clocks using an 11-hour drive, 14-hour duty, 10-hour reset model,
- stochastic unexpected yard delays at pickup and dropoff,
- deadhead and yard-delay costs in realized profit.

This is still not a full dispatch engine. It does not model road closures,
route-level traffic, driver home-time preferences, team drivers, split sleeper
rules, or equipment maintenance.

## Public Inputs

The v0.2 runner uses the processed seed lane table already in this workspace:

- `data/processed/v1_usda_faf_mapped_lanes.csv`
- `data/processed/faf_state_imbalance_2024.csv`

Those processed files come from public FAF state freight-flow data and USDA AMS
FVWTRK truck-rate reports. The raw-data inspection and processing entry point is
`scripts/inspect_public_sources.py`.

## Scenarios

| Key | Description |
| --- | --- |
| `mild` | Loose capacity. Myopic policies should be hard to beat. |
| `tight` | Moderate scarcity. Opportunity cost should matter. |
| `scarce` | High demand and low fleet count. Bad accept/reject decisions compound quickly. |

Each scenario runs a 72-hour closed-loop simulation. Load streams, fleet
initialization, rollout-label generation, and evaluation are seeded separately.

## Presets

| Preset | Purpose | Scenarios | Seed Pairs | Label Limit | Eval Load Limit |
| --- | --- | --- | ---: | ---: | ---: |
| `smoke` | Quick correctness check and CI run. | `tight` | 1 | 200 | 250 |
| `standard` | Default benchmark run for local development. | `mild,tight,scarce` | 3 | 600 | Full horizon |
| `paper` | Stronger preliminary table for a benchmark paper. | `mild,tight,scarce` | 10 | 1,200 | Full horizon |

## Run Commands

Smoke run:

```bash
python3 scripts/run_freightbidbench.py --preset smoke --output-dir benchmark_runs/smoke
```

Standard run:

```bash
python3 scripts/run_freightbidbench.py --preset standard --output-dir benchmark_runs/standard
```

Paper-strength run:

```bash
python3 scripts/run_freightbidbench.py --preset paper --output-dir benchmark_runs/paper
```

Useful overrides:

```bash
python3 scripts/run_freightbidbench.py \
  --preset paper \
  --seed-count 20 \
  --label-limit 1200 \
  --scenarios tight,scarce \
  --cascade-bands 0,100,250,500,700,900,1200,1600 \
  --output-dir benchmark_runs/paper_20seed_tight_scarce
```

All commands are run from the `faster_planning/` directory.

## Output Files

Each run writes:

| File | Purpose |
| --- | --- |
| `freightbidbench_policy_runs.csv` | One row per scenario, train/eval seed pair, policy, and cascade band. |
| `freightbidbench_static_label_fit.csv` | Held-out surrogate fit per scenario and seed pair. |
| `freightbidbench_policy_summary.csv` | Aggregate policy table with means, standard deviations, and 95% confidence intervals. |
| `freightbidbench_frontier_summary.csv` | Aggregate latency-profit frontier for cascade bands. |
| `freightbidbench_manifest.json` | Reproducibility manifest: command, seeds, scenarios, inputs, outputs, and row counts. |
| `freightbidbench_report.md` | Human-readable report with the main tables. |

## Current Reference Run

The current checked v0.2 standard reference run is:

```bash
python3 scripts/run_freightbidbench.py --preset standard --output-dir benchmark_runs/standard_v02
```

It produced:

- `benchmark_runs/standard_v02/freightbidbench_report.md`
- `benchmark_runs/standard_v02/freightbidbench_manifest.json`
- 99 seed-level policy rows,
- 9 static-fit rows,
- 33 aggregate policy rows,
- 21 aggregate frontier rows.

The previous v0.1 standard run remains in `benchmark_runs/standard`, but it
does not include HOS/window feasibility.

Key standard-run findings:

- `mild`: myopic and bid-price slightly exceed the finite rollout teacher on
  realized profit, reinforcing that rollout is a stochastic benchmark and not
  an oracle.
- `tight`: rollout earns $942k versus $867k for myopic/bid-price, while the
  +/- $500 cascade earns $813k at 41.3% rollout-call share.
- `scarce`: rollout earns $758k versus $718k for myopic/bid-price; the widest
  cascade band reaches 90.5% retention at 64.5% rollout-call share.
- Feasibility materially changes the benchmark: myopic and bid-price policies
  create hundreds of infeasible accept attempts, while rollout avoids them in
  the reported standard run.
- Rollout latency is much higher than in v0.1 because each branch now checks
  individual truck feasibility, windows, HOS, and yard delays.

## Baseline Policies

The v0.2 reference runner includes:

- `myopic_margin`: accept if immediate margin is non-negative.
- `bid_price`: accept using a simple origin-destination future-value proxy.
- `surrogate_linear`: train a dependency-free ridge linear surrogate on rollout incremental-value labels.
- `cascade_surrogate_rollout`: use the surrogate except near the decision boundary or when trucks are scarce.
- `rollout_teacher`: finite-lookahead Monte Carlo teacher with common-random-number accept/reject branches.

## Reporting Rules

For a benchmark result to be comparable, report:

1. Preset or exact scenario list.
2. Number of seed pairs and first seed.
3. Cascade bands.
4. Label limit and evaluation load limit.
5. Full `freightbidbench_manifest.json`.
6. Mean profit and confidence intervals from `freightbidbench_policy_summary.csv`.
7. Latency-profit frontier from `freightbidbench_frontier_summary.csv`.
8. Feasibility metrics: infeasible accepts, pickup-window misses, delivery-window misses, HOS rest hours, yard-delay hours, and deadhead miles.

Do not report a single seed as a final result except for smoke testing.

## Extending The Bench

New policies should plug into the policy choice layer in
`scripts/run_surrogate_cascade.py`, then be added to `POLICIES` in
`scripts/run_freightbidbench.py`.

The benchmark intentionally starts with a dependency-free reference
implementation. Stronger ML methods can live in separate scripts as long as
they consume the same generated decision states, use the same seed protocol, and
write comparable policy rows.

## V0.2 Limitations

- Synthetic loads are public-calibrated, not private production tenders.
- Prices and fleet behavior are simplified.
- The rollout teacher is finite-lookahead and CPU-based.
- Latency is Python reference latency, not optimized serving latency.
- HOS is simplified and does not cover split sleeper, recap, home-time, or team-driver cases.
- Pickup reach time is state/market-level, not a street-level routing model.
- Traffic, road closures, weather, and route-specific incident simulation are still future work.
- Current surrogate baseline is deliberately weak; the benchmark is the first
  artifact, not the final method.

These limitations are acceptable for a first benchmark paper if the claims stay
focused on reproducibility, calibration from public data, and closed-loop
latency-profit evaluation.
