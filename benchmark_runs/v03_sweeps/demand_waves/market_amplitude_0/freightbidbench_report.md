# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/demand_waves/configs/freightbidbench_v03_wave_market_0.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 5
- Evaluation load limit: 10
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 2.20 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 40.0% | $1,085 | $2,056 |
| `freightbidbench_tight_capacity` | 1 | 80.0% | $386 | $835 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 64.3% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $45,172 | +/- $0 | 112.4% | 0.051 | 0.0% | 0.0 | $0 | $25,837 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $45,172 | +/- $0 | 112.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $45,172 | +/- $0 | 112.4% | 0.001 | 0.0% | 0.0 | $0 | $25,837 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $33,834 | +/- $0 | 84.2% | 0.005 | 0.0% | 0.0 | $0 | $25,837 | 0 | 5 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $40,204 | +/- $0 | 100.0% | 41.728 | 100.0% | 0.0 | $0 | $25,837 | 0 | 7 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 62.5% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $49,466 | +/- $0 | 103.1% | 0.062 | 0.0% | 0.0 | $0 | $29,996 | 0 | 12 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $49,466 | +/- $0 | 103.1% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 12 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $49,466 | +/- $0 | 103.1% | 0.001 | 0.0% | 0.0 | $0 | $29,996 | 0 | 12 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $49,466 | +/- $0 | 103.1% | 0.006 | 0.0% | 0.0 | $0 | $29,996 | 0 | 12 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $47,970 | +/- $0 | 100.0% | 63.608 | 100.0% | 0.0 | $0 | $29,996 | 0 | 8 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 84.2% | $33,834 | 0.007 | 0.0% |
| `freightbidbench_tight_capacity` | 0 | 103.1% | $49,466 | 0.010 | 0.0% |

## Output Files

- `benchmark_runs/v03_sweeps/demand_waves/market_amplitude_0/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/demand_waves/market_amplitude_0/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/demand_waves/market_amplitude_0/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves/market_amplitude_0/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/demand_waves/market_amplitude_0/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
