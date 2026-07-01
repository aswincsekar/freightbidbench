# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/service_failure_penalty/configs/freightbidbench_v03_penalty_0.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 5
- Evaluation load limit: 10
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 2.20 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 40.0% | $1,081 | $2,043 |
| `freightbidbench_tight_capacity` | 1 | 80.0% | $385 | $935 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $19,334 | +/- $0 | 134.6% | 0.050 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $19,334 | +/- $0 | 134.6% | 0.000 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $19,334 | +/- $0 | 134.6% | 0.001 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $7,996 | +/- $0 | 55.7% | 0.005 | 0.0% | 0.0 | $0 | 0 | 5 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $14,366 | +/- $0 | 100.0% | 41.244 | 100.0% | 0.0 | $0 | 0 | 7 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $19,470 | +/- $0 | 108.3% | 0.066 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $19,470 | +/- $0 | 108.3% | 0.000 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $19,470 | +/- $0 | 108.3% | 0.002 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $19,470 | +/- $0 | 108.3% | 0.006 | 0.0% | 0.0 | $0 | 0 | 12 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $17,974 | +/- $0 | 100.0% | 64.467 | 100.0% | 0.0 | $0 | 0 | 8 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 55.7% | $7,996 | 0.008 | 0.0% |
| `freightbidbench_tight_capacity` | 0 | 108.3% | $19,470 | 0.009 | 0.0% |

## Output Files

- `benchmark_runs/v03_sweeps/service_failure_penalty/penalty_0/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty/penalty_0/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty/penalty_0/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty/penalty_0/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty/penalty_0/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
