# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/configs/freightbidbench_v03_wave_price_0p75.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 67.35 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 25.0% | $1,209 | $2,344 |
| `freightbidbench_tight_capacity` | 1 | 70.0% | $1,015 | $2,438 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 2.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $871,464 | +/- $0 | 73.4% | 0.016 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $863,454 | +/- $0 | 72.8% | 0.000 | 0.0% | 797.0 | $8,010 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $863,554 | +/- $0 | 72.8% | 0.001 | 0.0% | 787.0 | $7,910 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $111,235 | +/- $0 | 9.4% | 0.004 | 0.0% | 0.0 | $0 | $25,837 | 0 | 65 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,186,553 | +/- $0 | 100.0% | 21.154 | 100.0% | 0.0 | $0 | $25,671 | 1,420 | 420 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 2.2% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,217,781 | +/- $0 | 87.5% | 0.022 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,212,371 | +/- $0 | 87.1% | 0.000 | 0.0% | 523.0 | $5,410 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,212,451 | +/- $0 | 87.2% | 0.001 | 0.0% | 514.0 | $5,330 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,276,066 | +/- $0 | 91.7% | 0.004 | 0.0% | 232.0 | $2,320 | $29,240 | 1,570 | 597 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,391,171 | +/- $0 | 100.0% | 31.576 | 100.0% | 0.0 | $0 | $30,271 | 1,710 | 559 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 9.7% | $115,214 | 1.085 | 4.9% |
| `freightbidbench_tight_capacity` | 0 | 92.6% | $1,287,625 | 5.474 | 25.0% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p75/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p75/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p75/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p75/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p75/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
