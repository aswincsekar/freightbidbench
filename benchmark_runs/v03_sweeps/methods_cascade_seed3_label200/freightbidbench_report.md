# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $250, +/- $500, +/- $700, +/- $900
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 735.61 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 73.7% | $1,210 | $2,573 |
| `freightbidbench_tight_capacity` | 3 | 82.7% | $1,176 | $2,404 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $28,805 | +/- $6,709 | 2.8% | 0.000 | 0.0% | 0.0 | $0 | $28,805 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $884,962 | +/- $206,813 | 85.6% | 0.017 | 0.0% | 0.0 | $0 | $26,928 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $881,765 | +/- $225,818 | 85.3% | 0.000 | 0.0% | 761.3 | $7,777 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $881,852 | +/- $225,731 | 85.3% | 0.001 | 0.0% | 747.7 | $7,690 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $867,616 | +/- $252,771 | 84.1% | 0.038 | 0.0% | 0.0 | $0 | $28,376 | 1,050 | 358 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,017,027 | +/- $45,355 | 98.3% | 16.679 | 62.4% | 0.0 | $0 | $28,853 | 1,300 | 407 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,034,740 | +/- $70,807 | 100.0% | 23.273 | 100.0% | 0.0 | $0 | $28,593 | 1,363 | 421 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,539 | +/- $7,243 | 2.6% | 0.000 | 0.0% | 0.0 | $0 | $32,539 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,116,373 | +/- $93,586 | 88.9% | 0.023 | 0.0% | 0.0 | $0 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,110,709 | +/- $94,106 | 88.5% | 0.000 | 0.0% | 549.0 | $5,663 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,114,910 | +/- $110,204 | 88.8% | 0.001 | 0.0% | 538.3 | $5,567 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,183,303 | +/- $122,727 | 94.3% | 0.035 | 0.0% | 0.0 | $0 | $31,554 | 1,620 | 553 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,206,913 | +/- $279,431 | 96.1% | 14.612 | 50.8% | 0.0 | $0 | $32,170 | 1,657 | 543 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,255,357 | +/- $49,580 | 100.0% | 31.668 | 100.0% | 0.0 | $0 | $31,939 | 1,737 | 565 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 88.9% | $917,816 | 6.981 | 38.4% |
| `freightbidbench_scarce_capacity` | 250 | 95.2% | $983,805 | 15.428 | 52.2% |
| `freightbidbench_scarce_capacity` | 500 | 98.3% | $1,017,027 | 16.679 | 62.4% |
| `freightbidbench_scarce_capacity` | 700 | 98.0% | $1,013,498 | 16.583 | 64.2% |
| `freightbidbench_scarce_capacity` | 900 | 99.6% | $1,030,556 | 18.004 | 71.3% |
| `freightbidbench_tight_capacity` | 0 | 99.9% | $1,254,564 | 7.877 | 34.8% |
| `freightbidbench_tight_capacity` | 250 | 96.7% | $1,214,095 | 9.011 | 33.2% |
| `freightbidbench_tight_capacity` | 500 | 96.1% | $1,206,913 | 14.612 | 50.8% |
| `freightbidbench_tight_capacity` | 700 | 97.5% | $1,224,694 | 15.325 | 48.2% |
| `freightbidbench_tight_capacity` | 900 | 98.0% | $1,230,568 | 20.290 | 65.0% |

## Output Files

- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed3_label200/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
