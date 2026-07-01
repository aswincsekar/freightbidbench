# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/configs/freightbidbench_v03_wave_combined_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 64.80 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 85.0% | $784 | $1,665 |
| `freightbidbench_tight_capacity` | 1 | 95.0% | $548 | $961 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $738,967 | +/- $0 | 90.6% | 0.015 | 0.0% | 0.0 | $0 | $24,514 | 1,380 | 514 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $731,487 | +/- $0 | 89.7% | 0.000 | 0.0% | 725.0 | $7,480 | $24,514 | 1,380 | 514 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $739,866 | +/- $0 | 90.7% | 0.001 | 0.0% | 705.0 | $7,320 | $25,721 | 1,400 | 522 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $721,605 | +/- $0 | 88.5% | 0.004 | 0.0% | 643.0 | $6,810 | $23,307 | 1,370 | 502 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $815,602 | +/- $0 | 100.0% | 19.479 | 100.0% | 0.0 | $0 | $27,006 | 1,470 | 451 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.1% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $863,833 | +/- $0 | 88.3% | 0.022 | 0.0% | 0.0 | $0 | $27,581 | 1,580 | 637 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $858,053 | +/- $0 | 87.7% | 0.000 | 0.0% | 578.0 | $5,780 | $27,581 | 1,580 | 637 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $858,173 | +/- $0 | 87.7% | 0.001 | 0.0% | 566.0 | $5,660 | $27,581 | 1,580 | 637 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $818,280 | +/- $0 | 83.6% | 0.004 | 0.0% | 89.0 | $890 | $29,996 | 1,310 | 555 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $978,603 | +/- $0 | 100.0% | 29.305 | 100.0% | 0.0 | $0 | $29,849 | 1,770 | 587 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 92.8% | $756,790 | 4.586 | 35.1% |
| `freightbidbench_tight_capacity` | 0 | 83.1% | $813,265 | 3.037 | 15.8% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
