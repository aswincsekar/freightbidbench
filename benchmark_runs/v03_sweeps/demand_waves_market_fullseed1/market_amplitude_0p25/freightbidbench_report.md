# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/configs/freightbidbench_v03_wave_market_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 68.74 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 55.0% | $917 | $1,895 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $476 | $919 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $752,959 | +/- $0 | 93.6% | 0.015 | 0.0% | 0.0 | $0 | $23,529 | 1,430 | 544 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $745,309 | +/- $0 | 92.6% | 0.000 | 0.0% | 762.0 | $7,650 | $23,529 | 1,430 | 544 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $745,409 | +/- $0 | 92.6% | 0.001 | 0.0% | 752.0 | $7,550 | $23,529 | 1,430 | 544 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $735,685 | +/- $0 | 91.4% | 0.004 | 0.0% | 436.0 | $4,360 | $24,981 | 1,390 | 491 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $804,804 | +/- $0 | 100.0% | 17.969 | 100.0% | 0.0 | $0 | $27,006 | 1,440 | 426 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.0% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $928,807 | +/- $0 | 91.9% | 0.022 | 0.0% | 0.0 | $0 | $28,072 | 1,760 | 636 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $923,497 | +/- $0 | 91.3% | 0.000 | 0.0% | 508.0 | $5,310 | $28,072 | 1,760 | 636 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $940,030 | +/- $0 | 93.0% | 0.001 | 0.0% | 493.0 | $5,190 | $29,137 | 1,760 | 646 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $791,931 | +/- $0 | 78.3% | 0.004 | 0.0% | 80.0 | $800 | $29,996 | 1,170 | 542 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,011,018 | +/- $0 | 100.0% | 30.334 | 100.0% | 0.0 | $0 | $31,027 | 1,840 | 590 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 94.5% | $760,405 | 8.331 | 45.0% |
| `freightbidbench_tight_capacity` | 0 | 85.2% | $861,578 | 3.571 | 15.9% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
