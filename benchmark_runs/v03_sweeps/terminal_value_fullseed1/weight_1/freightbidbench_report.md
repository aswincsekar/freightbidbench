# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/terminal_value_fullseed1/configs/freightbidbench_v03_terminal_1.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 58.70 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $981 | $1,804 |
| `freightbidbench_tight_capacity` | 1 | 95.0% | $536 | $1,153 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $103,350 | +/- $0 | 11.7% | 0.000 | 0.0% | 0.0 | $0 | $103,350 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $748,221 | +/- $0 | 85.0% | 0.015 | 0.0% | 0.0 | $0 | $88,975 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $740,301 | +/- $0 | 84.1% | 0.000 | 0.0% | 789.0 | $7,920 | $88,975 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $740,461 | +/- $0 | 84.2% | 0.001 | 0.0% | 773.0 | $7,760 | $88,975 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $645,685 | +/- $0 | 73.4% | 0.004 | 0.0% | 41.0 | $410 | $103,350 | 830 | 349 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $879,789 | +/- $0 | 100.0% | 14.941 | 100.0% | 0.0 | $0 | $108,023 | 1,420 | 404 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $119,983 | +/- $0 | 10.9% | 0.000 | 0.0% | 0.0 | $0 | $119,983 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $988,208 | +/- $0 | 89.8% | 0.022 | 0.0% | 0.0 | $0 | $108,394 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $982,828 | +/- $0 | 89.3% | 0.000 | 0.0% | 522.0 | $5,380 | $108,394 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $982,948 | +/- $0 | 89.3% | 0.001 | 0.0% | 508.0 | $5,260 | $108,394 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $996,528 | +/- $0 | 90.5% | 0.004 | 0.0% | 504.0 | $5,070 | $112,251 | 1,730 | 640 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,100,707 | +/- $0 | 100.0% | 29.063 | 100.0% | 0.0 | $0 | $124,106 | 1,830 | 563 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 77.2% | $679,512 | 2.272 | 18.8% |
| `freightbidbench_tight_capacity` | 0 | 94.2% | $1,036,988 | 5.478 | 27.5% |

## Output Files

- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_1/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_1/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_1/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_1/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_1/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
