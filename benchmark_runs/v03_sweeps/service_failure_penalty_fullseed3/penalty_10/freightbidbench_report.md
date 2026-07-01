# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/configs/freightbidbench_v03_penalty_10.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 183.29 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 60.0% | $2,133 | $3,468 |
| `freightbidbench_tight_capacity` | 3 | 86.7% | $3,500 | $8,900 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $714,150 | +/- $163,866 | 94.5% | 0.016 | 0.0% | 0.0 | $0 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $710,405 | +/- $180,930 | 94.0% | 0.000 | 0.0% | 754.3 | $7,680 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $710,495 | +/- $180,780 | 94.0% | 0.001 | 0.0% | 740.0 | $7,590 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $534,922 | +/- $700,172 | 70.6% | 0.004 | 0.0% | 234.0 | $2,340 | 923 | 361 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $756,368 | +/- $35,585 | 100.0% | 17.339 | 100.0% | 0.0 | $0 | 1,403 | 423 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | $0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $864,383 | +/- $101,177 | 92.2% | 0.023 | 0.0% | 0.0 | $0 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $861,274 | +/- $109,238 | 91.9% | 0.000 | 0.0% | 546.7 | $5,620 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $861,391 | +/- $109,324 | 91.9% | 0.001 | 0.0% | 533.7 | $5,503 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $431,847 | +/- $975,706 | 46.3% | 0.004 | 0.0% | 169.3 | $1,707 | 603 | 323 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $937,810 | +/- $126,868 | 100.0% | 29.171 | 100.0% | 0.0 | $0 | 1,733 | 565 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 71.1% | $538,419 | 4.431 | 32.9% |
| `freightbidbench_tight_capacity` | 0 | 47.4% | $442,540 | 1.925 | 11.0% |

## Output Files

- `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/penalty_10/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/penalty_10/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/penalty_10/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/penalty_10/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/service_failure_penalty_fullseed3/penalty_10/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
