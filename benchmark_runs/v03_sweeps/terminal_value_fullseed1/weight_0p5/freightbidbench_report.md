# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/terminal_value_fullseed1/configs/freightbidbench_v03_terminal_0p5.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 62.00 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $980 | $1,807 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $544 | $1,301 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $51,675 | +/- $0 | 6.3% | 0.000 | 0.0% | 0.0 | $0 | $51,675 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $703,733 | +/- $0 | 85.2% | 0.016 | 0.0% | 0.0 | $0 | $44,487 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $695,813 | +/- $0 | 84.3% | 0.000 | 0.0% | 789.0 | $7,920 | $44,487 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $695,973 | +/- $0 | 84.3% | 0.001 | 0.0% | 773.0 | $7,760 | $44,487 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $718,795 | +/- $0 | 87.0% | 0.004 | 0.0% | 95.0 | $950 | $51,675 | 1,100 | 412 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $825,777 | +/- $0 | 100.0% | 15.254 | 100.0% | 0.0 | $0 | $54,011 | 1,420 | 404 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $59,992 | +/- $0 | 5.8% | 0.000 | 0.0% | 0.0 | $0 | $59,992 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $934,011 | +/- $0 | 89.7% | 0.022 | 0.0% | 0.0 | $0 | $54,197 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $928,631 | +/- $0 | 89.2% | 0.000 | 0.0% | 522.0 | $5,380 | $54,197 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $928,751 | +/- $0 | 89.2% | 0.001 | 0.0% | 508.0 | $5,260 | $54,197 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $939,993 | +/- $0 | 90.3% | 0.004 | 0.0% | 504.0 | $5,070 | $56,126 | 1,720 | 638 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,041,147 | +/- $0 | 100.0% | 29.664 | 100.0% | 0.0 | $0 | $61,297 | 1,840 | 581 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 89.3% | $737,114 | 4.004 | 34.1% |
| `freightbidbench_tight_capacity` | 0 | 94.2% | $980,538 | 5.731 | 27.5% |

## Output Files

- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
