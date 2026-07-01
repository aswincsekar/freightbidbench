# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $500
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: 100
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 11.18 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 1 | 80.0% | $714 | $1,230 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 18.3% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $216,026 | +/- $0 | 132.1% | 0.042 | 0.0% | 0.0 | $0 | $29,575 | 50 | 145 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $215,976 | +/- $0 | 132.0% | 0.000 | 0.0% | 5.0 | $50 | $29,575 | 50 | 145 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $215,976 | +/- $0 | 132.0% | 0.001 | 0.0% | 5.0 | $50 | $29,575 | 50 | 145 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $177,742 | +/- $0 | 108.7% | 0.052 | 0.0% | 0.0 | $0 | $29,996 | 0 | 97 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $170,501 | +/- $0 | 104.2% | 21.141 | 40.0% | 0.0 | $0 | $29,892 | 10 | 87 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $163,590 | +/- $0 | 100.0% | 57.771 | 100.0% | 0.0 | $0 | $29,514 | 10 | 70 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 106.1% | $173,508 | 5.516 | 15.0% |
| `freightbidbench_tight_capacity` | 500 | 104.2% | $170,501 | 21.141 | 40.0% |

## Output Files

- `benchmark_runs/v03_sweeps/surrogate_features_smoke/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_smoke/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_smoke/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_smoke/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_smoke/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
