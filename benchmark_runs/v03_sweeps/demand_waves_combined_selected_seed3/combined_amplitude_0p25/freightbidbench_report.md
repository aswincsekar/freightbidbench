# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/configs/freightbidbench_v03_wave_combined_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 204.28 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 80.0% | $2,397 | $6,547 |
| `freightbidbench_tight_capacity` | 3 | 95.0% | $1,122 | $2,885 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $28,805 | +/- $6,709 | 3.6% | 0.000 | 0.0% | 0.0 | $0 | $28,805 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $726,941 | +/- $81,450 | 89.8% | 0.016 | 0.0% | 0.0 | $0 | $27,425 | 1,350 | 502 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $724,098 | +/- $97,654 | 89.5% | 0.000 | 0.0% | 753.0 | $7,747 | $27,334 | 1,360 | 507 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $728,814 | +/- $92,664 | 90.1% | 0.001 | 0.0% | 731.3 | $7,583 | $28,139 | 1,367 | 510 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $574,708 | +/- $600,717 | 71.2% | 0.004 | 0.0% | 428.0 | $4,407 | $27,818 | 950 | 398 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $808,853 | +/- $27,123 | 100.0% | 20.137 | 100.0% | 0.0 | $0 | $29,115 | 1,460 | 439 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,539 | +/- $7,243 | 3.3% | 0.000 | 0.0% | 0.0 | $0 | $32,539 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $899,292 | +/- $77,467 | 91.5% | 0.023 | 0.0% | 0.0 | $0 | $30,206 | 1,683 | 632 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $900,255 | +/- $91,426 | 91.6% | 0.000 | 0.0% | 541.0 | $5,523 | $30,252 | 1,687 | 636 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $886,974 | +/- $73,314 | 90.2% | 0.001 | 0.0% | 534.0 | $5,473 | $30,607 | 1,647 | 627 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $877,295 | +/- $135,285 | 89.3% | 0.004 | 0.0% | 350.3 | $3,513 | $31,218 | 1,557 | 592 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $983,434 | +/- $87,804 | 100.0% | 30.880 | 100.0% | 0.0 | $0 | $32,406 | 1,783 | 580 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 71.6% | $577,979 | 3.130 | 27.3% |
| `freightbidbench_tight_capacity` | 0 | 87.5% | $859,874 | 5.389 | 24.8% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/combined_amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/combined_amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/combined_amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/combined_amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_combined_selected_seed3/combined_amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
