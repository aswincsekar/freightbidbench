# FreightBidBench v0.2 Report

## Configuration

- Benchmark version: `freightbidbench-v0.2`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: 250
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, and stochastic yard delays
- Total runtime: 49.04 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 1 | 65.0% | $1,704 | $4,177 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $353,418 | +/- $0 | 116.5% | 0.000 | 0.0% | 67.0 | 560 | 250 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $353,418 | +/- $0 | 116.5% | 0.001 | 0.0% | 65.0 | 560 | 250 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $301,529 | +/- $0 | 99.4% | 0.004 | 0.0% | 13.0 | 260 | 233 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $286,697 | +/- $0 | 94.5% | 15.631 | 51.2% | 4.0 | 130 | 198 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $303,237 | +/- $0 | 100.0% | 36.521 | 100.0% | 0.0 | 220 | 179 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 89.1% | $270,327 | 3.726 | 25.6% |
| `freightbidbench_tight_capacity` | 100 | 92.1% | $279,231 | 6.748 | 31.2% |
| `freightbidbench_tight_capacity` | 250 | 91.2% | $276,481 | 9.595 | 38.0% |
| `freightbidbench_tight_capacity` | 500 | 94.5% | $286,697 | 15.631 | 51.2% |
| `freightbidbench_tight_capacity` | 700 | 95.7% | $290,346 | 17.308 | 57.6% |
| `freightbidbench_tight_capacity` | 900 | 102.6% | $311,000 | 21.384 | 68.4% |
| `freightbidbench_tight_capacity` | 1,200 | 97.7% | $296,168 | 20.743 | 73.6% |

## Output Files

- `benchmark_runs/smoke_v02/freightbidbench_policy_runs.csv`
- `benchmark_runs/smoke_v02/freightbidbench_static_label_fit.csv`
- `benchmark_runs/smoke_v02/freightbidbench_policy_summary.csv`
- `benchmark_runs/smoke_v02/freightbidbench_frontier_summary.csv`
- `benchmark_runs/smoke_v02/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
