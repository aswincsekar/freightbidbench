# FreightBidBench v0.3

FreightBidBench v0.3 is a public-calibrated synthetic benchmark for real-time
truckload bid acceptance. On top of the v0.2 operational-feasibility layer,
v0.3 adds three economic reward layers (service-failure penalty, terminal
fleet value, temporal price-premium window), exact and Lagrangian-per-truck
hindsight ceilings, and a latency-aware surrogate-to-rollout cascade.

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
- service-failure penalty cost from infeasible accepts (v0.3, L1),
- terminal fleet value at the horizon (v0.3, L2),
- simplified HOS rest hours,
- deadhead miles to pickup,
- stochastic pickup and dropoff yard-delay hours,
- cascade rollout-call share,
- held-out rollout-label fit for learned surrogates.

The finite rollout teacher is a stochastic benchmark, not an oracle. A cheaper
policy can exceed 100% retention if it earns higher realized closed-loop profit
than the finite-lookahead teacher on the same seed average. To bound how much
profit remains against the true optimum, v0.3 adds hindsight ceilings (below).

The versioned benchmark contract is pinned in
`configs/freightbidbench_v03_scenarios.json` and summarized in
`docs/benchmark_spec.md`. Three version strings — `benchmark_version`
(`freightbidbench-v0.3`), `scenario_config_version` (`scenario-v0.3.2`), and
`policy_set_version` (`policy-set-v0.3.0`) — pin the public contract.

## Feasibility Layer

The operational feasibility layer, introduced in v0.2 and retained unchanged in
v0.3, models:

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

## Economic Layers (v0.3)

Three versioned reward layers sharpen the decision problem so that distinct
policy classes separate. Each is independently controllable through the
scenario contract and is frozen at the value below in `scenario-v0.3.2`.

- **L1 — service-failure penalty (`ρ = $10`).** Accepting a load the
  feasibility map classifies as infeasible incurs reward `−ρ` with no fleet
  mutation, so feasibility-blind policies pay regret linear in their
  infeasible-accept rate (Proposition 1 in the paper).
- **L2 — terminal fleet value (`ω = 0.25`).** End-of-horizon trucks earn
  `ω · V(market)`, where `V(·)` combines FAF outbound intensity and the
  FAF/USDA net-outbound imbalance panel; this penalizes greedy positioning
  that strands trucks in low-value markets.
- **L3 — temporal price-premium window (`1.5×` on-peak).** A daily price
  multiplier creates a timing problem: accepting a moderate off-peak load can
  consume capacity needed for a predictable on-peak premium.

## Hindsight Ceilings (v0.3)

Retention against the rollout teacher does not reveal how far a policy is from
the optimum. v0.3 adds two upper bounds on the optimal closed-loop value:

- **Exact small-prefix dynamic program** (`scripts/run_hindsight_bound.py`):
  a trustworthy but small-instance reference, tractable for prefixes of up to
  ~16 loads.
- **Lagrangian-per-truck information relaxation**
  (`scripts/run_lagrangian_bound.py`): a full-horizon bound that dualizes only
  the cross-truck assignment constraint and retains per-truck HOS, location,
  and sequencing structure. It is 20.7% tighter than the LP-style relaxation
  on `tight` and 39.3% tighter on `scarce`. A looser LP-style full-horizon
  bound is available via `scripts/run_relaxed_hindsight_bound.py`.

## Public Inputs

The runner uses the processed seed lane table already in this workspace:

- `data/processed/v1_usda_faf_mapped_lanes.csv`
- `data/processed/faf_state_imbalance_2024.csv`

Those processed files come from public FAF state freight-flow data and USDA AMS
FVWTRK truck-rate reports. The raw-data inspection and processing entry point is
`scripts/inspect_public_sources.py`. Calibration of the load mix, haul lengths,
and prices against these sources is cross-checked by
`scripts/analyze_calibration.py` (`make calibration-report`).

## Scenarios

| Key | Description |
| --- | --- |
| `mild` | Loose capacity. Myopic policies should be hard to beat; used as a negative control. |
| `tight` | Moderate scarcity. Opportunity cost should matter. |
| `scarce` | High demand and low fleet count. Bad accept/reject decisions compound quickly. |

Each scenario runs a 72-hour closed-loop simulation. Load streams, fleet
initialization, rollout-label generation, and evaluation are seeded separately.

## Presets

| Preset | Purpose | Scenarios | Seed Pairs | Label Limit | Eval Load Limit |
| --- | --- | --- | ---: | ---: | ---: |
| `smoke` | Quick correctness check and CI run. | `tight` | 1 | 200 | 250 |
| `standard` | Default benchmark run for local development. | `mild,tight,scarce` | 3 | 600 | Full horizon |
| `paper` | Stronger table for the benchmark paper. | `mild,tight,scarce` | 10 | 1,200 | Full horizon |

## Run Commands

The runner defaults to the v0.2 config, so v0.3 runs must pass
`--config configs/freightbidbench_v03_scenarios.json`. All commands are run from
the `faster_planning/` directory.

Smoke run:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset smoke --output-dir benchmark_runs/smoke
```

Standard run:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --output-dir benchmark_runs/standard
```

Ten-seed methods run (the v0.3 paper reference):

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --scenarios mild,tight,scarce \
  --seed-count 10 --label-limit 200 --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200
```

Feasibility ablation flags:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset smoke --disable-hos --output-dir benchmark_runs/no_hos_smoke
```

Available ablations:

- `--disable-pickup-reach`
- `--disable-time-windows`
- `--disable-hos`
- `--disable-yard-delays`

For a local wrapper that runs all ablations and combines summaries, see
`docs/ablation_protocol.md`.

## Output Files

Each run writes:

| File | Purpose |
| --- | --- |
| `freightbidbench_policy_runs.csv` | One row per scenario, train/eval seed pair, policy, and cascade band. |
| `freightbidbench_static_label_fit.csv` | Held-out surrogate fit per scenario and seed pair. |
| `freightbidbench_policy_summary.csv` | Aggregate policy table with means, standard deviations, and 95% confidence intervals. |
| `freightbidbench_frontier_summary.csv` | Aggregate latency-profit frontier for cascade bands. |
| `freightbidbench_manifest.json` | Reproducibility manifest: command, version strings, seeds, scenarios, inputs, outputs, and row counts. |
| `freightbidbench_report.md` | Human-readable report with the main tables. |

## Current Reference Run

The v0.3 paper reference is the ten-seed methods run:

```bash
python3 scripts/run_freightbidbench.py \
  --config configs/freightbidbench_v03_scenarios.json \
  --preset standard --scenarios mild,tight,scarce \
  --seed-count 10 --label-limit 200 --cascade-bands 0,250,500,700,900 \
  --output-dir benchmark_runs/v03_sweeps/methods_cascade_seed10_label200
```

Its `freightbidbench_manifest.json` is the canonical reproducibility anchor;
paper tables are assembled into `benchmark_runs/paper_v03/` via
`make paper-v03-tables`, and paired-bootstrap deltas are computed with
`scripts/analyze_policy_deltas.py` (20,000 resamples).

Key ten-seed findings (retention is mean closed-loop profit versus the rollout
teacher; cascade uses the representative band `β = $500`, `κ = 2`):

- `mild` (negative control): all policies cluster near the rollout teacher
  (cascade 99.7%), confirming the scenario stays flat under v0.3 economics.
- `tight`: best simple policy retains 91.0%, the stdlib surrogate 94.2%, and
  the cascade 98.2% at ~40% of rollout's mean decision latency; the paired
  cascade-minus-rollout profit delta is not statistically significant (95% CI
  spans zero), i.e. the cascade matches the teacher to within sampling error.
- `scarce`: best simple 86.5%, surrogate 89.3%, cascade 98.0% at ~56% of
  rollout latency; a small but significant ~2% gap to rollout remains.
- Hindsight: the Lagrangian-per-truck bound relocates the rollout teacher from
  53.6%/39.8% of the loose LP ceiling to 67.6%/65.7% of a structure-respecting
  ceiling on `tight`/`scarce`, and shows the residual headroom lies in
  cross-truck coordination rather than single-tender scoring.

The v0.2.1 standard reference run remains under `benchmark_runs/standard_v02/`
and the v0.1 run under `benchmark_runs/standard/` for historical comparison;
the v0.1 run does not include HOS/window feasibility.

## Baseline Policies

The runner includes:

- `reject_all`: reject every load; a lower-bound sanity check.
- `accept_all_feasible`: accept every currently feasible load; a pressure-test sanity check.
- `myopic_margin`: accept if immediate margin is non-negative.
- `bid_price`: accept using a simple origin-destination future-value proxy.
- `surrogate_linear`: train a dependency-free ridge linear surrogate on rollout incremental-value labels.
- `cascade_surrogate_rollout`: use the surrogate except near the decision boundary or when trucks are scarce.
- `rollout_teacher`: finite-lookahead Monte Carlo teacher with common-random-number accept/reject branches.

## Reporting Rules

For a benchmark result to be comparable, report:

1. Benchmark version, scenario-config version, and policy-set version.
2. Preset or exact scenario list.
3. Number of seed pairs and first seed.
4. Cascade bands.
5. Label limit and evaluation load limit.
6. Full `freightbidbench_manifest.json`.
7. Mean profit and confidence intervals from `freightbidbench_policy_summary.csv`.
8. Latency-profit frontier from `freightbidbench_frontier_summary.csv`.
9. Feasibility and economic metrics: infeasible accepts, pickup-window misses, delivery-window misses, HOS rest hours, yard-delay hours, deadhead miles, service-failure penalty cost, and terminal fleet value.

Do not report a single seed as a final result except for smoke testing.

## Extending The Bench

New policies should plug into the policy choice layer in
`scripts/run_surrogate_cascade.py`, then be added to `policies.default` in
`configs/freightbidbench_v03_scenarios.json` if they belong in public benchmark
runs. See `docs/adding_policies.md`.

The benchmark intentionally starts with a dependency-free reference
implementation. Stronger ML methods can live in separate scripts as long as
they consume the same generated decision states, use the same seed protocol, and
write comparable policy rows.

## Limitations

- Synthetic loads are public-calibrated, not private production tenders; the
  v1 USDA-reefer lane subset concentrates load draws on a few high-volume Texas
  and Georgia origins (see the paper's calibration appendix).
- Prices and fleet behavior are simplified.
- The rollout teacher is finite-lookahead and CPU-based.
- Latency is Python reference latency, not optimized serving latency.
- HOS is simplified and does not cover split sleeper, recap, home-time, or team-driver cases.
- Pickup reach time is state/market-level, not a street-level routing model.
- The exact hindsight DP is tractable only for small load prefixes; the
  LP-style full-horizon bound is intentionally loose (the Lagrangian bound is
  the tighter ceiling).
- Traffic, road closures, weather, and route-specific incident simulation are still future work.
- The stdlib surrogate is deliberately simple; the benchmark is the artifact,
  not the final method.

These limitations are acceptable for a benchmark paper if the claims stay
focused on reproducibility, calibration from public data, closed-loop
latency-profit evaluation, and honestly reported hindsight headroom.
