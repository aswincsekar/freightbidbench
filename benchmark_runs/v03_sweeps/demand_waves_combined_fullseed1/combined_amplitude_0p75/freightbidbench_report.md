# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/configs/freightbidbench_v03_wave_combined_0p75.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 54.41 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 100.0% | $1,114 | $2,259 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $853 | $1,332 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.6% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $680,773 | +/- $0 | 93.9% | 0.014 | 0.0% | 0.0 | $0 | $22,982 | 1,300 | 462 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $673,283 | +/- $0 | 92.8% | 0.000 | 0.0% | 723.0 | $7,490 | $22,982 | 1,300 | 462 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $673,653 | +/- $0 | 92.9% | 0.001 | 0.0% | 680.0 | $7,120 | $22,982 | 1,300 | 462 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $677,871 | +/- $0 | 93.5% | 0.004 | 0.0% | 251.0 | $2,510 | $25,837 | 1,140 | 439 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $725,368 | +/- $0 | 100.0% | 14.592 | 100.0% | 0.0 | $0 | $25,553 | 1,250 | 394 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $880,637 | +/- $0 | 94.2% | 0.022 | 0.0% | 0.0 | $0 | $26,790 | 1,650 | 622 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $875,277 | +/- $0 | 93.7% | 0.000 | 0.0% | 512.0 | $5,360 | $26,790 | 1,650 | 622 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $884,839 | +/- $0 | 94.7% | 0.001 | 0.0% | 456.0 | $4,770 | $27,855 | 1,700 | 638 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $858,677 | +/- $0 | 91.9% | 0.004 | 0.0% | 431.0 | $4,330 | $26,311 | 1,530 | 589 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $934,543 | +/- $0 | 100.0% | 25.167 | 100.0% | 0.0 | $0 | $28,680 | 1,590 | 544 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 85.0% | $616,747 | 3.072 | 32.9% |
| `freightbidbench_tight_capacity` | 0 | 89.1% | $832,311 | 6.056 | 39.5% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p75/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p75/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p75/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p75/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p75/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
