# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_fullseed1/configs/freightbidbench_v03_wave_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 56.63 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 90.0% | $750 | $1,515 |
| `freightbidbench_tight_capacity` | 1 | 90.0% | $642 | $1,177 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $730,386 | +/- $0 | 90.1% | 0.015 | 0.0% | 0.0 | $0 | $22,982 | 1,370 | 524 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $722,896 | +/- $0 | 89.1% | 0.000 | 0.0% | 730.0 | $7,490 | $22,982 | 1,370 | 524 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $723,076 | +/- $0 | 89.2% | 0.001 | 0.0% | 712.0 | $7,310 | $22,982 | 1,370 | 524 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $737,332 | +/- $0 | 90.9% | 0.004 | 0.0% | 643.0 | $6,480 | $25,292 | 1,380 | 531 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $811,046 | +/- $0 | 100.0% | 14.810 | 100.0% | 0.0 | $0 | $27,006 | 1,470 | 456 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.1% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $887,960 | +/- $0 | 90.7% | 0.022 | 0.0% | 0.0 | $0 | $28,337 | 1,610 | 646 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $882,250 | +/- $0 | 90.1% | 0.000 | 0.0% | 571.0 | $5,710 | $28,337 | 1,610 | 646 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $882,370 | +/- $0 | 90.2% | 0.001 | 0.0% | 558.0 | $5,590 | $28,337 | 1,610 | 646 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $521,437 | +/- $0 | 53.3% | 0.004 | 0.0% | 29.0 | $290 | $29,996 | 590 | 373 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $978,733 | +/- $0 | 100.0% | 26.680 | 100.0% | 0.0 | $0 | $29,471 | 1,790 | 598 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 93.1% | $754,942 | 5.398 | 44.1% |
| `freightbidbench_tight_capacity` | 0 | 54.0% | $528,125 | 2.232 | 9.2% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_fullseed1/amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
