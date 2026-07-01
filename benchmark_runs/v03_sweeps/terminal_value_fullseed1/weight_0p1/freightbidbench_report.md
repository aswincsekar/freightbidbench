# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/terminal_value_fullseed1/configs/freightbidbench_v03_terminal_0p1.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 67.02 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $979 | $1,810 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $551 | $1,365 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $10,335 | +/- $0 | 1.3% | 0.000 | 0.0% | 0.0 | $0 | $10,335 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $668,143 | +/- $0 | 85.4% | 0.017 | 0.0% | 0.0 | $0 | $8,897 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $660,223 | +/- $0 | 84.4% | 0.000 | 0.0% | 789.0 | $7,920 | $8,897 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $660,383 | +/- $0 | 84.4% | 0.001 | 0.0% | 773.0 | $7,760 | $8,897 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $707,730 | +/- $0 | 90.4% | 0.004 | 0.0% | 210.0 | $2,100 | $10,335 | 1,250 | 460 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $782,568 | +/- $0 | 100.0% | 15.516 | 100.0% | 0.0 | $0 | $10,802 | 1,420 | 404 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $11,998 | +/- $0 | 1.3% | 0.000 | 0.0% | 0.0 | $0 | $11,998 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $890,653 | +/- $0 | 93.8% | 0.023 | 0.0% | 0.0 | $0 | $10,839 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $885,273 | +/- $0 | 93.3% | 0.000 | 0.0% | 522.0 | $5,380 | $10,839 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $885,393 | +/- $0 | 93.3% | 0.001 | 0.0% | 508.0 | $5,260 | $10,839 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $896,076 | +/- $0 | 94.4% | 0.004 | 0.0% | 506.0 | $5,100 | $11,183 | 1,740 | 641 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $949,352 | +/- $0 | 100.0% | 29.372 | 100.0% | 0.0 | $0 | $11,788 | 1,740 | 563 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 92.3% | $722,251 | 8.282 | 63.7% |
| `freightbidbench_tight_capacity` | 0 | 97.8% | $928,022 | 5.768 | 27.5% |

## Output Files

- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p1/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p1/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p1/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p1/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed1/weight_0p1/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
