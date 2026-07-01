# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $500
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 63.06 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 70.5% | $1,088 | $2,517 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $808,139 | +/- $0 | 75.8% | 0.015 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $800,139 | +/- $0 | 75.1% | 0.000 | 0.0% | 796.0 | $8,000 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $800,259 | +/- $0 | 75.1% | 0.001 | 0.0% | 784.0 | $7,880 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $768,504 | +/- $0 | 72.1% | 0.035 | 0.0% | 0.0 | $0 | $24,552 | 930 | 289 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,025,578 | +/- $0 | 96.2% | 16.716 | 83.8% | 0.0 | $0 | $25,242 | 1,320 | 392 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,065,656 | +/- $0 | 100.0% | 20.140 | 100.0% | 0.0 | $0 | $24,464 | 1,410 | 418 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 79.4% | $846,494 | 6.604 | 51.9% |
| `freightbidbench_scarce_capacity` | 500 | 96.2% | $1,025,578 | 16.716 | 83.8% |

## Output Files

- `benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_guard_scarce_label200/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
