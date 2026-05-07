# FreightBidBench v0.2 Benchmark Specification

This document pins the public benchmark contract used by
`scripts/run_freightbidbench.py`.

## Versioned Configuration

The benchmark reads scenario and policy metadata from
`configs/freightbidbench_v02_scenarios.json`.

| Field | Current value | Meaning |
| --- | --- | --- |
| `benchmark_version` | `freightbidbench-v0.2` | Public benchmark family. |
| `scenario_config_version` | `scenario-v0.2.1` | Scenario and preset contract. |
| `policy_set_version` | `policy-set-v0.2.1` | Default public policy set. |
| `default_first_seed` | `20260506` | First train seed used when no override is supplied. |

Changing scenario parameters, default policies, cascade bands, or preset seed
counts should bump the relevant config version.

## Decision Event

At each simulated hour, the environment generates candidate loads from the
public-calibrated lane table. For each load, a policy receives the current load,
fleet state, lane table, scenario configuration, state future-value features,
and optional trained surrogate model. The policy returns:

```python
return wants_accept, score, stage_name
```

The benchmark then applies the decision. If `wants_accept` is true, the
feasibility layer attempts to assign a truck and mutates the fleet only on a
successful assignment.

## State And Feasibility

Version 0.2 exposes:

- individual truck locations and availability times,
- candidate load origin, destination, price, cost, distance, and scarcity,
- pickup deadhead time and miles inside the origin market,
- pickup and delivery appointment windows,
- simplified 11/14/10 HOS clocks,
- stochastic pickup and dropoff yard delays,
- state-level future-value features.

The benchmark does not model street-level routing, traffic, weather, road
closures, equipment maintenance, home-time preferences, teams, or split-sleeper
rules.

## Scenarios And Presets

The public scenarios are:

| Key | Purpose |
| --- | --- |
| `mild` | Loose capacity where myopic policies should remain competitive. |
| `tight` | Moderate scarcity where opportunity cost should matter. |
| `scarce` | High demand and low fleet count where poor decisions compound. |

The public presets are:

| Preset | Purpose |
| --- | --- |
| `smoke` | One-seed correctness run for CI and local sanity checks. |
| `standard` | Three-seed local development result across all scenarios. |
| `paper` | Ten-seed preliminary paper table across all scenarios. |

Exact numeric values live in `configs/freightbidbench_v02_scenarios.json` and
are copied into every run manifest.

## Public Policies

The default policy set is:

| Policy | Role |
| --- | --- |
| `reject_all` | Lower-bound sanity check; rejects every load. |
| `accept_all_feasible` | Upper-pressure sanity check; accepts only loads feasible at decision time. |
| `myopic_margin` | Accepts non-negative immediate margin. |
| `bid_price` | Adds a simple destination-origin future-value proxy. |
| `surrogate_linear` | Uses a dependency-free linear model trained on rollout labels. |
| `rollout_teacher` | Finite-lookahead stochastic rollout benchmark. |

The cascade policy `cascade_surrogate_rollout` is evaluated separately for each
cascade band in `cascade_bands_dollars`.

## Output Contract

Every run writes these files:

- `freightbidbench_policy_runs.csv`
- `freightbidbench_static_label_fit.csv`
- `freightbidbench_policy_summary.csv`
- `freightbidbench_frontier_summary.csv`
- `freightbidbench_manifest.json`
- `freightbidbench_report.md`

The manifest is the reproducibility anchor. It records the command, benchmark
version, scenario-config version, policy-set version, default policy list,
cascade policy, evaluated policy list, seed pairs, source input paths,
feasibility config, scenarios, output paths, and row counts.

## Golden Smoke Contract

The repository includes a tiny golden smoke test:

```bash
python3 scripts/run_freightbidbench.py \
  --preset smoke \
  --seed-count 1 \
  --label-limit 5 \
  --eval-load-limit 10 \
  --cascade-bands 0 \
  --output-dir benchmark_runs/ci_smoke
```

That contract should produce one static-fit row, seven policy-run rows, seven
policy-summary rows, and one cascade-frontier row. It is not a scientific
result; it is a compatibility check for the benchmark interface.

## Comparable Reporting

Comparable benchmark submissions should report:

1. Full manifest.
2. Scenario list, seed count, and first seed.
3. Label limit and evaluation load limit.
4. Policy-summary mean profit, confidence intervals, latency, and feasibility metrics.
5. Cascade frontier with rollout-call share.
6. Any code or hardware changes affecting latency measurements.
