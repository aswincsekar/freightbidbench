# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.4-dev`
- Scenario config: `configs/freightbidbench_v04_scenarios.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `dual_price`, `dual_price_vf`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 114.92 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 2 | 82.2% | $1,191 | $2,384 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,858 | +/- $36,369 | 2.6% | 0.000 | 0.0% | 0.0 | $0 | $32,858 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,134,630 | +/- $260,113 | 89.6% | 0.023 | 0.0% | 0.0 | $0 | $30,774 | 1,730 | 652 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,129,140 | +/- $259,097 | 89.2% | 0.000 | 0.0% | 525.0 | $5,490 | $30,774 | 1,730 | 652 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,135,415 | +/- $337,686 | 89.7% | 0.001 | 0.0% | 511.5 | $5,370 | $31,032 | 1,725 | 652 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,199,884 | +/- $510,717 | 94.8% | 0.034 | 0.0% | 0.0 | $0 | $32,137 | 1,610 | 552 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,266,076 | +/- $92,992 | 100.0% | 31.794 | 100.0% | 0.0 | $0 | $32,274 | 1,715 | 557 |
| `freightbidbench_tight_capacity` | `dual_price` | - | $1,140,785 | +/- $338,322 | 90.1% | 0.024 | 0.0% | 0.0 | $0 | $31,032 | 1,725 | 652 |
| `freightbidbench_tight_capacity` | `dual_price_vf` | - | $1,199,712 | +/- $149,736 | 94.8% | 0.026 | 0.0% | 0.0 | $0 | $32,407 | 1,795 | 669 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 100.9% | $1,276,856 | 6.524 | 29.8% |

## Output Files

- `benchmark_runs/v04_dev/harness_crosscheck/freightbidbench_policy_runs.csv`
- `benchmark_runs/v04_dev/harness_crosscheck/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v04_dev/harness_crosscheck/freightbidbench_policy_summary.csv`
- `benchmark_runs/v04_dev/harness_crosscheck/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v04_dev/harness_crosscheck/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
