# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/configs/freightbidbench_v03_penalty_50.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: 250
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 22.72 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $1,078 | $2,127 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $565 | $1,391 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $272,281 | +/- $0 | 111.6% | 0.022 | 0.0% | 0.0 | $0 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $266,881 | +/- $0 | 109.3% | 0.000 | 0.0% | 108.0 | $5,400 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $267,081 | +/- $0 | 109.4% | 0.001 | 0.0% | 104.0 | $5,200 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $51,036 | +/- $0 | 20.9% | 0.004 | 0.0% | 0.0 | $0 | 0 | 32 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $244,088 | +/- $0 | 100.0% | 22.300 | 100.0% | 0.0 | $0 | 140 | 111 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $353,418 | +/- $0 | 117.4% | 0.034 | 0.0% | 0.0 | $0 | 560 | 250 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $350,018 | +/- $0 | 116.3% | 0.000 | 0.0% | 67.0 | $3,400 | 560 | 250 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $350,118 | +/- $0 | 116.3% | 0.001 | 0.0% | 65.0 | $3,300 | 560 | 250 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $351,411 | +/- $0 | 116.8% | 0.004 | 0.0% | 63.0 | $3,250 | 550 | 248 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $300,966 | +/- $0 | 100.0% | 39.200 | 100.0% | 0.0 | $0 | 200 | 168 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 21.3% | $52,055 | 0.853 | 4.4% |
| `freightbidbench_tight_capacity` | 0 | 105.0% | $316,124 | 10.735 | 55.2% |

## Output Files

- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_50/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_50/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_50/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_50/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_50/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
