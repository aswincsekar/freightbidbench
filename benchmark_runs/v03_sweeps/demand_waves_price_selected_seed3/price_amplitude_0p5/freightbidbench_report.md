# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/configs/freightbidbench_v03_wave_price_0p5.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 201.69 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 60.0% | $2,929 | $7,239 |
| `freightbidbench_tight_capacity` | 3 | 78.3% | $4,180 | $10,070 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $28,805 | +/- $6,709 | 2.8% | 0.000 | 0.0% | 0.0 | $0 | $28,805 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $884,962 | +/- $206,813 | 85.6% | 0.016 | 0.0% | 0.0 | $0 | $26,928 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $881,765 | +/- $225,818 | 85.3% | 0.000 | 0.0% | 761.3 | $7,777 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $881,852 | +/- $225,731 | 85.3% | 0.001 | 0.0% | 747.7 | $7,690 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $438,392 | +/- $990,721 | 43.0% | 0.004 | 0.0% | 180.3 | $1,863 | $28,766 | 467 | 241 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,034,740 | +/- $70,807 | 100.0% | 21.632 | 100.0% | 0.0 | $0 | $28,593 | 1,363 | 421 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,539 | +/- $7,243 | 2.6% | 0.000 | 0.0% | 0.0 | $0 | $32,539 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,116,373 | +/- $93,586 | 88.9% | 0.024 | 0.0% | 0.0 | $0 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,110,709 | +/- $94,106 | 88.5% | 0.000 | 0.0% | 549.0 | $5,663 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,114,910 | +/- $110,204 | 88.8% | 0.001 | 0.0% | 538.3 | $5,567 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $558,941 | +/- $1,334,211 | 44.1% | 0.005 | 0.0% | 94.7 | $947 | $32,307 | 593 | 310 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,255,357 | +/- $49,580 | 100.0% | 31.728 | 100.0% | 0.0 | $0 | $31,939 | 1,737 | 565 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 43.3% | $441,479 | 1.754 | 14.0% |
| `freightbidbench_tight_capacity` | 0 | 44.4% | $562,304 | 3.271 | 15.0% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_selected_seed3/price_amplitude_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
