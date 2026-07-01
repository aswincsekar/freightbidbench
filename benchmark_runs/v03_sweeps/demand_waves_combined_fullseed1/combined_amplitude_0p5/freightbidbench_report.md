# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/configs/freightbidbench_v03_wave_combined_0p5.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 70.79 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $1,250 | $1,774 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $616 | $927 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $710,762 | +/- $0 | 92.2% | 0.015 | 0.0% | 0.0 | $0 | $22,982 | 1,330 | 481 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $703,062 | +/- $0 | 91.2% | 0.000 | 0.0% | 758.0 | $7,700 | $22,982 | 1,330 | 481 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $703,302 | +/- $0 | 91.3% | 0.001 | 0.0% | 734.0 | $7,460 | $22,982 | 1,330 | 481 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $729,326 | +/- $0 | 94.6% | 0.004 | 0.0% | 752.0 | $7,640 | $23,411 | 1,420 | 500 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $770,667 | +/- $0 | 100.0% | 16.638 | 100.0% | 0.0 | $0 | $25,553 | 1,310 | 427 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $961,961 | +/- $0 | 104.2% | 0.022 | 0.0% | 0.0 | $0 | $28,406 | 1,760 | 632 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $956,711 | +/- $0 | 103.6% | 0.000 | 0.0% | 520.0 | $5,250 | $28,406 | 1,760 | 632 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $953,862 | +/- $0 | 103.3% | 0.001 | 0.0% | 502.0 | $5,070 | $29,471 | 1,760 | 635 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $956,631 | +/- $0 | 103.6% | 0.004 | 0.0% | 527.0 | $5,330 | $28,406 | 1,760 | 632 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $923,076 | +/- $0 | 100.0% | 29.790 | 100.0% | 0.0 | $0 | $29,471 | 1,590 | 558 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 97.0% | $747,298 | 9.837 | 63.1% |
| `freightbidbench_tight_capacity` | 0 | 96.1% | $887,437 | 6.256 | 31.2% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_fullseed1/combined_amplitude_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
