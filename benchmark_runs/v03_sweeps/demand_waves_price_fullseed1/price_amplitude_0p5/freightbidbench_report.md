# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/configs/freightbidbench_v03_wave_price_0p5.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 69.90 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 50.0% | $918 | $1,929 |
| `freightbidbench_tight_capacity` | 1 | 75.0% | $787 | $1,413 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $808,139 | +/- $0 | 75.8% | 0.015 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $800,139 | +/- $0 | 75.1% | 0.000 | 0.0% | 796.0 | $8,000 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $800,259 | +/- $0 | 75.1% | 0.001 | 0.0% | 784.0 | $7,880 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $171,901 | +/- $0 | 16.1% | 0.004 | 0.0% | 0.0 | $0 | $25,837 | 10 | 99 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,065,656 | +/- $0 | 100.0% | 20.037 | 100.0% | 0.0 | $0 | $24,464 | 1,410 | 418 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,114,158 | +/- $0 | 87.5% | 0.022 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,108,748 | +/- $0 | 87.1% | 0.000 | 0.0% | 523.0 | $5,410 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,108,838 | +/- $0 | 87.1% | 0.001 | 0.0% | 513.0 | $5,320 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,163,878 | +/- $0 | 91.4% | 0.004 | 0.0% | 275.0 | $2,750 | $29,301 | 1,570 | 596 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,273,395 | +/- $0 | 100.0% | 31.638 | 100.0% | 0.0 | $0 | $29,206 | 1,780 | 546 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 16.5% | $175,372 | 0.952 | 4.9% |
| `freightbidbench_tight_capacity` | 0 | 92.1% | $1,172,971 | 9.468 | 39.6% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_price_fullseed1/price_amplitude_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
