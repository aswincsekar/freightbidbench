# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/configs/freightbidbench_v03_wave_market_0.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 81.89 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 65.0% | $979 | $1,809 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $548 | $1,371 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $681,490 | +/- $0 | 85.3% | 0.016 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $673,570 | +/- $0 | 84.3% | 0.000 | 0.0% | 789.0 | $7,920 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $673,730 | +/- $0 | 84.3% | 0.001 | 0.0% | 773.0 | $7,760 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $696,422 | +/- $0 | 87.2% | 0.004 | 0.0% | 246.0 | $2,460 | $25,837 | 1,100 | 446 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $798,772 | +/- $0 | 100.0% | 15.460 | 100.0% | 0.0 | $0 | $27,006 | 1,420 | 404 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.0% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $906,912 | +/- $0 | 89.8% | 0.046 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $901,532 | +/- $0 | 89.3% | 0.000 | 0.0% | 522.0 | $5,380 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $901,652 | +/- $0 | 89.3% | 0.001 | 0.0% | 508.0 | $5,260 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $911,920 | +/- $0 | 90.3% | 0.011 | 0.0% | 505.0 | $5,080 | $28,063 | 1,720 | 638 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,009,859 | +/- $0 | 100.0% | 45.807 | 100.0% | 0.0 | $0 | $30,271 | 1,850 | 580 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 88.4% | $706,377 | 4.617 | 39.0% |
| `freightbidbench_tight_capacity` | 0 | 94.1% | $950,567 | 5.644 | 27.5% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
