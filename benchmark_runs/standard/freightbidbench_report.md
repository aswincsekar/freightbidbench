# FreightBidBench v0 Report

## Configuration

- Benchmark version: `freightbidbench-v0.1`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 1,200
- Total runtime: 104.50 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mild` | `freightbidbench_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 3 | 97.3% | $683 | $1,138 |
| `freightbidbench_scarce_capacity` | 3 | 67.4% | $2,096 | $3,649 |
| `freightbidbench_tight_capacity` | 3 | 78.3% | $1,845 | $3,653 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | `myopic_margin` | - | $1,734,798 | +/- $161,668 | 100.0% | 0.000 | 0.0% |
| `freightbidbench_mild_capacity` | `bid_price` | - | $1,717,520 | +/- $128,835 | 99.0% | 0.000 | 0.0% |
| `freightbidbench_mild_capacity` | `surrogate_linear` | - | $1,731,829 | +/- $172,618 | 99.8% | 0.002 | 0.0% |
| `freightbidbench_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,729,747 | +/- $169,894 | 99.7% | 0.152 | 7.9% |
| `freightbidbench_mild_capacity` | `rollout_teacher` | - | $1,734,852 | +/- $156,396 | 100.0% | 3.223 | 100.0% |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $1,273,255 | +/- $105,077 | 88.2% | 0.000 | 0.0% |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $1,335,584 | +/- $134,765 | 92.5% | 0.000 | 0.0% |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $1,238,460 | +/- $189,033 | 85.7% | 0.002 | 0.0% |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,327,477 | +/- $148,255 | 91.9% | 0.661 | 31.2% |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,443,588 | +/- $125,786 | 100.0% | 1.883 | 100.0% |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,587,796 | +/- $70,558 | 95.4% | 0.000 | 0.0% |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,676,454 | +/- $153,109 | 100.7% | 0.000 | 0.0% |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,634,453 | +/- $188,212 | 98.2% | 0.002 | 0.0% |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,668,455 | +/- $147,371 | 100.2% | 0.856 | 43.0% |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,665,064 | +/- $21,676 | 100.0% | 2.428 | 100.0% |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 0 | 99.7% | $1,730,610 | 0.118 | 7.0% |
| `freightbidbench_mild_capacity` | 100 | 99.8% | $1,730,733 | 0.125 | 7.1% |
| `freightbidbench_mild_capacity` | 250 | 99.8% | $1,731,358 | 0.139 | 7.6% |
| `freightbidbench_mild_capacity` | 500 | 99.7% | $1,729,747 | 0.152 | 7.9% |
| `freightbidbench_mild_capacity` | 700 | 99.7% | $1,729,747 | 0.179 | 8.8% |
| `freightbidbench_mild_capacity` | 900 | 99.7% | $1,729,747 | 0.231 | 10.4% |
| `freightbidbench_mild_capacity` | 1,200 | 99.7% | $1,729,958 | 0.362 | 14.3% |
| `freightbidbench_scarce_capacity` | 0 | 87.0% | $1,256,763 | 0.136 | 12.6% |
| `freightbidbench_scarce_capacity` | 100 | 87.7% | $1,266,772 | 0.274 | 17.8% |
| `freightbidbench_scarce_capacity` | 250 | 89.3% | $1,290,006 | 0.424 | 22.9% |
| `freightbidbench_scarce_capacity` | 500 | 91.9% | $1,327,477 | 0.661 | 31.2% |
| `freightbidbench_scarce_capacity` | 700 | 94.1% | $1,358,940 | 0.884 | 40.8% |
| `freightbidbench_scarce_capacity` | 900 | 95.7% | $1,382,156 | 1.032 | 49.0% |
| `freightbidbench_scarce_capacity` | 1,200 | 98.7% | $1,424,406 | 1.334 | 68.3% |
| `freightbidbench_tight_capacity` | 0 | 98.6% | $1,641,590 | 0.226 | 15.7% |
| `freightbidbench_tight_capacity` | 100 | 98.7% | $1,644,161 | 0.362 | 21.0% |
| `freightbidbench_tight_capacity` | 250 | 99.9% | $1,664,178 | 0.587 | 29.9% |
| `freightbidbench_tight_capacity` | 500 | 100.2% | $1,668,455 | 0.856 | 43.0% |
| `freightbidbench_tight_capacity` | 700 | 101.2% | $1,684,870 | 1.077 | 51.9% |
| `freightbidbench_tight_capacity` | 900 | 101.5% | $1,689,598 | 1.258 | 59.4% |
| `freightbidbench_tight_capacity` | 1,200 | 100.6% | $1,675,013 | 1.475 | 67.8% |

## Output Files

- `benchmark_runs/standard/freightbidbench_policy_runs.csv`
- `benchmark_runs/standard/freightbidbench_static_label_fit.csv`
- `benchmark_runs/standard/freightbidbench_policy_summary.csv`
- `benchmark_runs/standard/freightbidbench_frontier_summary.csv`
- `benchmark_runs/standard/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
