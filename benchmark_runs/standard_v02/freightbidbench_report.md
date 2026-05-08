# FreightBidBench v0.2 Report

## Configuration

- Benchmark version: `freightbidbench-v0.2`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 600
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 1269.34 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mild` | `freightbidbench_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 3 | 58.8% | $1,991 | $4,324 |
| `freightbidbench_scarce_capacity` | 3 | 68.3% | $2,185 | $3,844 |
| `freightbidbench_tight_capacity` | 3 | 60.9% | $2,027 | $3,818 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_mild_capacity` | `accept_all_feasible` | - | $1,082,891 | +/- $190,549 | 101.7% | 0.040 | 0.0% | 0.0 | 2,053 | 783 |
| `freightbidbench_mild_capacity` | `myopic_margin` | - | $1,082,891 | +/- $190,549 | 101.7% | 0.000 | 0.0% | 323.7 | 2,053 | 783 |
| `freightbidbench_mild_capacity` | `bid_price` | - | $1,083,424 | +/- $190,200 | 101.8% | 0.001 | 0.0% | 312.0 | 2,050 | 782 |
| `freightbidbench_mild_capacity` | `surrogate_linear` | - | $917,369 | +/- $85,097 | 86.3% | 0.005 | 0.0% | 112.3 | 1,540 | 666 |
| `freightbidbench_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $976,891 | +/- $48,143 | 91.9% | 15.923 | 35.1% | 76.3 | 1,627 | 676 |
| `freightbidbench_mild_capacity` | `rollout_teacher` | - | $1,064,003 | +/- $122,520 | 100.0% | 45.574 | 100.0% | 0.0 | 1,840 | 676 |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $714,150 | +/- $163,866 | 94.3% | 0.016 | 0.0% | 0.0 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $718,085 | +/- $180,196 | 94.8% | 0.000 | 0.0% | 754.3 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $718,085 | +/- $180,196 | 94.8% | 0.001 | 0.0% | 740.0 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $487,441 | +/- $164,575 | 64.4% | 0.004 | 0.0% | 40.3 | 813 | 373 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $577,343 | +/- $216,688 | 76.3% | 7.354 | 38.0% | 0.0 | 950 | 370 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $757,682 | +/- $23,712 | 100.0% | 17.438 | 100.0% | 0.0 | 1,403 | 420 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $864,383 | +/- $101,177 | 91.7% | 0.023 | 0.0% | 0.0 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $866,894 | +/- $108,553 | 92.0% | 0.000 | 0.0% | 546.7 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $866,894 | +/- $108,553 | 92.0% | 0.001 | 0.0% | 533.7 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $739,135 | +/- $16,760 | 78.5% | 0.004 | 0.0% | 87.3 | 1,217 | 539 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $812,794 | +/- $51,897 | 86.3% | 11.069 | 41.3% | 34.3 | 1,363 | 538 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $942,219 | +/- $98,905 | 100.0% | 28.549 | 100.0% | 0.0 | 1,753 | 567 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 0 | 87.4% | $927,944 | 1.494 | 5.8% |
| `freightbidbench_mild_capacity` | 100 | 88.1% | $936,463 | 4.354 | 11.9% |
| `freightbidbench_mild_capacity` | 250 | 89.0% | $946,216 | 8.357 | 19.9% |
| `freightbidbench_mild_capacity` | 500 | 91.9% | $976,891 | 15.923 | 35.1% |
| `freightbidbench_mild_capacity` | 700 | 94.3% | $1,003,078 | 20.039 | 44.6% |
| `freightbidbench_mild_capacity` | 900 | 97.3% | $1,034,688 | 25.519 | 57.3% |
| `freightbidbench_mild_capacity` | 1,200 | 97.1% | $1,033,558 | 29.333 | 63.1% |
| `freightbidbench_scarce_capacity` | 0 | 66.8% | $505,383 | 0.980 | 9.5% |
| `freightbidbench_scarce_capacity` | 100 | 67.6% | $511,592 | 2.263 | 15.2% |
| `freightbidbench_scarce_capacity` | 250 | 70.0% | $529,932 | 4.133 | 24.3% |
| `freightbidbench_scarce_capacity` | 500 | 76.3% | $577,343 | 7.354 | 38.0% |
| `freightbidbench_scarce_capacity` | 700 | 79.3% | $600,379 | 8.538 | 44.1% |
| `freightbidbench_scarce_capacity` | 900 | 81.8% | $619,290 | 9.165 | 48.2% |
| `freightbidbench_scarce_capacity` | 1,200 | 90.5% | $685,250 | 12.053 | 64.5% |
| `freightbidbench_tight_capacity` | 0 | 78.3% | $737,665 | 1.083 | 7.5% |
| `freightbidbench_tight_capacity` | 100 | 79.6% | $749,398 | 3.110 | 13.6% |
| `freightbidbench_tight_capacity` | 250 | 80.8% | $760,765 | 5.862 | 22.9% |
| `freightbidbench_tight_capacity` | 500 | 86.3% | $812,794 | 11.069 | 41.3% |
| `freightbidbench_tight_capacity` | 700 | 87.3% | $823,089 | 14.364 | 50.4% |
| `freightbidbench_tight_capacity` | 900 | 91.4% | $860,554 | 17.533 | 59.4% |
| `freightbidbench_tight_capacity` | 1,200 | 91.8% | $864,724 | 19.140 | 66.9% |

## Output Files

- `benchmark_runs/standard_v02/freightbidbench_policy_runs.csv`
- `benchmark_runs/standard_v02/freightbidbench_static_label_fit.csv`
- `benchmark_runs/standard_v02/freightbidbench_policy_summary.csv`
- `benchmark_runs/standard_v02/freightbidbench_frontier_summary.csv`
- `benchmark_runs/standard_v02/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
