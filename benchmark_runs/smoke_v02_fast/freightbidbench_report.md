# FreightBidBench v0.2 Report

## Configuration

- Benchmark version: `freightbidbench-v0.2`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 200
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, and stochastic yard delays
- Total runtime: 110.53 seconds

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
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $879,814 | +/- $0 | 92.5% | 0.000 | 0.0% | 522.0 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $879,814 | +/- $0 | 92.5% | 0.000 | 0.0% | 508.0 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $834,711 | +/- $0 | 87.8% | 0.004 | 0.0% | 240.0 | 1,540 | 611 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $854,801 | +/- $0 | 89.9% | 9.362 | 36.1% | 168.0 | 1,610 | 577 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $951,052 | +/- $0 | 100.0% | 25.663 | 100.0% | 0.0 | 1,790 | 544 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 88.7% | $843,960 | 2.075 | 12.9% |
| `freightbidbench_tight_capacity` | 100 | 89.8% | $853,698 | 5.293 | 24.2% |
| `freightbidbench_tight_capacity` | 250 | 88.1% | $838,067 | 5.683 | 24.6% |
| `freightbidbench_tight_capacity` | 500 | 89.9% | $854,801 | 9.362 | 36.1% |
| `freightbidbench_tight_capacity` | 700 | 94.7% | $901,007 | 12.548 | 48.4% |
| `freightbidbench_tight_capacity` | 900 | 97.4% | $926,371 | 15.708 | 60.9% |
| `freightbidbench_tight_capacity` | 1,200 | 99.1% | $942,409 | 18.616 | 73.0% |

## Output Files

- `benchmark_runs/smoke_v02_fast/freightbidbench_policy_runs.csv`
- `benchmark_runs/smoke_v02_fast/freightbidbench_static_label_fit.csv`
- `benchmark_runs/smoke_v02_fast/freightbidbench_policy_summary.csv`
- `benchmark_runs/smoke_v02_fast/freightbidbench_frontier_summary.csv`
- `benchmark_runs/smoke_v02_fast/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
