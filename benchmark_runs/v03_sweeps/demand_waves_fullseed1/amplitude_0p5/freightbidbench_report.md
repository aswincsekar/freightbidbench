# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_fullseed1/configs/freightbidbench_v03_wave_0p5.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 58.68 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 75.0% | $1,546 | $2,306 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $640 | $1,660 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.3% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $702,160 | +/- $0 | 90.4% | 0.015 | 0.0% | 0.0 | $0 | $21,815 | 1,290 | 452 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $694,450 | +/- $0 | 89.4% | 0.000 | 0.0% | 766.0 | $7,710 | $21,815 | 1,290 | 452 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $694,640 | +/- $0 | 89.4% | 0.001 | 0.0% | 747.0 | $7,520 | $21,815 | 1,290 | 452 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $764,875 | +/- $0 | 98.5% | 0.004 | 0.0% | 632.0 | $6,320 | $24,981 | 1,410 | 491 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $776,631 | +/- $0 | 100.0% | 16.152 | 100.0% | 0.0 | $0 | $25,671 | 1,400 | 437 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.3% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $872,334 | +/- $0 | 94.9% | 0.024 | 0.0% | 0.0 | $0 | $28,715 | 1,520 | 587 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $866,604 | +/- $0 | 94.2% | 0.000 | 0.0% | 569.0 | $5,730 | $28,715 | 1,520 | 587 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $866,774 | +/- $0 | 94.3% | 0.001 | 0.0% | 552.0 | $5,560 | $28,715 | 1,520 | 587 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $866,714 | +/- $0 | 94.3% | 0.004 | 0.0% | 558.0 | $5,620 | $28,715 | 1,520 | 587 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $919,573 | +/- $0 | 100.0% | 27.005 | 100.0% | 0.0 | $0 | $29,471 | 1,580 | 533 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 93.8% | $728,701 | 3.529 | 36.0% |
| `freightbidbench_tight_capacity` | 0 | 94.6% | $870,159 | 4.870 | 26.8% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
