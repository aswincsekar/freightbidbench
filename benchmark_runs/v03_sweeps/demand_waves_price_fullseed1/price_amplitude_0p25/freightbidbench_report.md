# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/configs/freightbidbench_v03_wave_price_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 70.51 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $890 | $1,945 |
| `freightbidbench_tight_capacity` | 1 | 95.0% | $634 | $1,452 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 2.9% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $744,815 | +/- $0 | 84.5% | 0.016 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $736,845 | +/- $0 | 83.6% | 0.000 | 0.0% | 794.0 | $7,970 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $736,985 | +/- $0 | 83.6% | 0.001 | 0.0% | 780.0 | $7,830 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $780,130 | +/- $0 | 88.5% | 0.004 | 0.0% | 502.0 | $5,070 | $23,765 | 1,300 | 497 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $881,875 | +/- $0 | 100.0% | 19.821 | 100.0% | 0.0 | $0 | $25,671 | 1,420 | 413 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 2.7% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,010,535 | +/- $0 | 90.0% | 0.022 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,005,125 | +/- $0 | 89.5% | 0.000 | 0.0% | 523.0 | $5,410 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,005,245 | +/- $0 | 89.5% | 0.001 | 0.0% | 510.0 | $5,290 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,018,585 | +/- $0 | 90.7% | 0.004 | 0.0% | 508.0 | $5,120 | $27,959 | 1,750 | 642 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,123,014 | +/- $0 | 100.0% | 31.582 | 100.0% | 0.0 | $0 | $29,584 | 1,820 | 573 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 90.7% | $799,846 | 4.571 | 33.8% |
| `freightbidbench_tight_capacity` | 0 | 96.0% | $1,078,333 | 6.081 | 27.5% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
