# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/configs/freightbidbench_v03_wave_price_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 198.76 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 63.3% | $2,566 | $5,921 |
| `freightbidbench_tight_capacity` | 3 | 86.7% | $3,376 | $7,890 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $28,805 | +/- $6,709 | 3.1% | 0.000 | 0.0% | 0.0 | $0 | $28,805 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $813,020 | +/- $190,224 | 88.6% | 0.016 | 0.0% | 0.0 | $0 | $26,928 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $809,550 | +/- $208,326 | 88.2% | 0.000 | 0.0% | 760.0 | $7,753 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $809,647 | +/- $208,199 | 88.2% | 0.001 | 0.0% | 744.7 | $7,657 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $627,606 | +/- $745,156 | 69.2% | 0.004 | 0.0% | 326.3 | $3,287 | $28,400 | 940 | 388 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $916,261 | +/- $84,497 | 100.0% | 20.048 | 100.0% | 0.0 | $0 | $29,138 | 1,470 | 438 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,539 | +/- $7,243 | 2.9% | 0.000 | 0.0% | 0.0 | $0 | $32,539 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,005,658 | +/- $97,764 | 90.8% | 0.024 | 0.0% | 0.0 | $0 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,003,405 | +/- $110,465 | 90.6% | 0.000 | 0.0% | 547.7 | $5,647 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,003,505 | +/- $110,566 | 90.6% | 0.001 | 0.0% | 536.7 | $5,547 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $492,566 | +/- $1,141,916 | 44.1% | 0.004 | 0.0% | 170.0 | $1,713 | $31,860 | 603 | 320 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,107,321 | +/- $67,085 | 100.0% | 32.032 | 100.0% | 0.0 | $0 | $32,191 | 1,737 | 558 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 69.4% | $628,674 | 3.229 | 23.8% |
| `freightbidbench_tight_capacity` | 0 | 45.9% | $512,664 | 2.071 | 11.0% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
