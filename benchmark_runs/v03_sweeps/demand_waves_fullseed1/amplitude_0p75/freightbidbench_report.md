# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_fullseed1/configs/freightbidbench_v03_wave_0p75.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 55.56 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 80.0% | $999 | $2,050 |
| `freightbidbench_tight_capacity` | 1 | 90.0% | $637 | $1,191 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $675,918 | +/- $0 | 89.4% | 0.015 | 0.0% | 0.0 | $0 | $23,839 | 1,280 | 468 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $668,308 | +/- $0 | 88.4% | 0.000 | 0.0% | 743.0 | $7,610 | $23,839 | 1,280 | 468 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $669,316 | +/- $0 | 88.5% | 0.001 | 0.0% | 742.0 | $7,470 | $23,839 | 1,280 | 469 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $688,933 | +/- $0 | 91.1% | 0.005 | 0.0% | 713.0 | $7,380 | $23,888 | 1,330 | 483 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $755,980 | +/- $0 | 100.0% | 15.441 | 100.0% | 0.0 | $0 | $26,577 | 1,260 | 379 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.3% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $885,346 | +/- $0 | 97.8% | 0.022 | 0.0% | 0.0 | $0 | $27,855 | 1,620 | 609 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $879,976 | +/- $0 | 97.2% | 0.000 | 0.0% | 517.0 | $5,370 | $27,855 | 1,620 | 609 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $880,066 | +/- $0 | 97.2% | 0.001 | 0.0% | 503.0 | $5,280 | $27,855 | 1,620 | 609 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $898,879 | +/- $0 | 99.3% | 0.004 | 0.0% | 330.0 | $3,330 | $27,650 | 1,670 | 634 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $905,625 | +/- $0 | 100.0% | 28.146 | 100.0% | 0.0 | $0 | $28,784 | 1,460 | 508 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 89.5% | $676,556 | 3.309 | 37.1% |
| `freightbidbench_tight_capacity` | 0 | 96.0% | $868,995 | 2.993 | 17.6% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p75/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p75/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p75/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p75/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p75/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
