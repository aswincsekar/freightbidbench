# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/configs/freightbidbench_v03_penalty_25.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: 250
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 22.21 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 70.0% | $1,065 | $2,099 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $558 | $1,372 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $272,281 | +/- $0 | 111.6% | 0.023 | 0.0% | 0.0 | $0 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $269,581 | +/- $0 | 110.4% | 0.000 | 0.0% | 108.0 | $2,700 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $269,681 | +/- $0 | 110.5% | 0.001 | 0.0% | 104.0 | $2,600 | 430 | 184 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $52,894 | +/- $0 | 21.7% | 0.004 | 0.0% | 0.0 | $0 | 0 | 33 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $244,088 | +/- $0 | 100.0% | 22.555 | 100.0% | 0.0 | $0 | 140 | 111 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $353,418 | +/- $0 | 114.8% | 0.033 | 0.0% | 0.0 | $0 | 560 | 250 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $351,718 | +/- $0 | 114.3% | 0.000 | 0.0% | 67.0 | $1,700 | 560 | 250 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $351,768 | +/- $0 | 114.3% | 0.001 | 0.0% | 65.0 | $1,650 | 560 | 250 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $353,036 | +/- $0 | 114.7% | 0.004 | 0.0% | 63.0 | $1,625 | 550 | 248 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $307,807 | +/- $0 | 100.0% | 37.393 | 100.0% | 0.0 | $0 | 240 | 182 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 22.1% | $53,913 | 0.851 | 4.4% |
| `freightbidbench_tight_capacity` | 0 | 102.8% | $316,274 | 10.521 | 55.2% |

## Output Files

- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_eval250/penalty_25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
