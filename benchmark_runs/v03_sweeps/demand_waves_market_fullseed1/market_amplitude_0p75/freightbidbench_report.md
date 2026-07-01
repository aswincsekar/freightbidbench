# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/configs/freightbidbench_v03_wave_market_0p75.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 66.80 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 85.0% | $2,258 | $3,585 |
| `freightbidbench_tight_capacity` | 1 | 100.0% | $650 | $849 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 3.2% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $744,569 | +/- $0 | 92.4% | 0.014 | 0.0% | 0.0 | $0 | $23,957 | 1,390 | 496 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $737,089 | +/- $0 | 91.4% | 0.000 | 0.0% | 742.0 | $7,480 | $23,957 | 1,390 | 496 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $737,381 | +/- $0 | 91.5% | 0.001 | 0.0% | 718.0 | $7,250 | $23,957 | 1,390 | 497 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $289,489 | +/- $0 | 35.9% | 0.004 | 0.0% | 39.0 | $390 | $17,815 | 270 | 200 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $806,066 | +/- $0 | 100.0% | 18.050 | 100.0% | 0.0 | $0 | $25,671 | 1,450 | 443 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 3.1% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $808,139 | +/- $0 | 82.6% | 0.037 | 0.0% | 0.0 | $0 | $28,015 | 1,560 | 584 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $816,505 | +/- $0 | 83.4% | 0.000 | 0.0% | 509.0 | $5,440 | $27,625 | 1,560 | 587 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $816,605 | +/- $0 | 83.4% | 0.001 | 0.0% | 491.0 | $5,340 | $27,625 | 1,560 | 587 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $875,239 | +/- $0 | 89.4% | 0.007 | 0.0% | 357.0 | $3,620 | $27,959 | 1,630 | 617 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $978,838 | +/- $0 | 100.0% | 32.557 | 100.0% | 0.0 | $0 | $29,962 | 1,680 | 560 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 41.4% | $333,557 | 2.022 | 26.3% |
| `freightbidbench_tight_capacity` | 0 | 92.9% | $909,483 | 4.888 | 39.1% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p75/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p75/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p75/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p75/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves_market_fullseed1/market_amplitude_0p75/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
