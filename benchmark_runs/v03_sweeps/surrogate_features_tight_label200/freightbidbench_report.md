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
- Total runtime: 79.43 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 1 | 81.0% | $1,098 | $2,192 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,114,158 | +/- $0 | 87.5% | 0.022 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,108,748 | +/- $0 | 87.1% | 0.000 | 0.0% | 523.0 | $5,410 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,108,838 | +/- $0 | 87.1% | 0.001 | 0.0% | 513.0 | $5,320 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,156,679 | +/- $0 | 90.8% | 0.034 | 0.0% | 301.0 | $3,010 | $28,553 | 1,580 | 554 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,279,403 | +/- $0 | 100.5% | 20.798 | 74.5% | 74.0 | $740 | $29,584 | 1,810 | 550 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,273,395 | +/- $0 | 100.0% | 31.365 | 100.0% | 0.0 | $0 | $29,206 | 1,780 | 546 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 98.5% | $1,254,536 | 8.907 | 37.8% |
| `freightbidbench_tight_capacity` | 500 | 100.5% | $1,279,403 | 20.798 | 74.5% |

## Output Files

- `benchmark_runs/v03_sweeps/surrogate_features_tight_label200/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_tight_label200/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_tight_label200/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_tight_label200/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_tight_label200/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
