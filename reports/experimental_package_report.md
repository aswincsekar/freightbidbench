# Experimental Package Report

## Configuration

- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Baseline policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 1,200
- Total package runtime: 113.27 seconds

| Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| `surrogate_probe_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `surrogate_probe_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `surrogate_probe_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `surrogate_probe_mild_capacity` | 3 | 97.3% | $683 | $1,138 |
| `surrogate_probe_scarce_capacity` | 3 | 67.4% | $2,096 | $3,649 |
| `surrogate_probe_tight_capacity` | 3 | 78.3% | $1,845 | $3,653 |

## Representative Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band; the full
frontier is below.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `surrogate_probe_mild_capacity` | `myopic_margin` | - | $1,734,798 | +/- $161,668 | 100.0% | 0.000 | 0.0% |
| `surrogate_probe_mild_capacity` | `bid_price` | - | $1,717,520 | +/- $128,835 | 99.0% | 0.000 | 0.0% |
| `surrogate_probe_mild_capacity` | `surrogate_linear` | - | $1,731,829 | +/- $172,618 | 99.8% | 0.002 | 0.0% |
| `surrogate_probe_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,729,747 | +/- $169,894 | 99.7% | 0.165 | 7.9% |
| `surrogate_probe_mild_capacity` | `rollout_teacher` | - | $1,734,852 | +/- $156,396 | 100.0% | 3.531 | 100.0% |
| `surrogate_probe_scarce_capacity` | `myopic_margin` | - | $1,273,255 | +/- $105,077 | 88.2% | 0.000 | 0.0% |
| `surrogate_probe_scarce_capacity` | `bid_price` | - | $1,335,584 | +/- $134,765 | 92.5% | 0.000 | 0.0% |
| `surrogate_probe_scarce_capacity` | `surrogate_linear` | - | $1,238,460 | +/- $189,033 | 85.7% | 0.002 | 0.0% |
| `surrogate_probe_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,327,477 | +/- $148,255 | 91.9% | 0.730 | 31.2% |
| `surrogate_probe_scarce_capacity` | `rollout_teacher` | - | $1,443,588 | +/- $125,786 | 100.0% | 2.020 | 100.0% |
| `surrogate_probe_tight_capacity` | `myopic_margin` | - | $1,587,796 | +/- $70,558 | 95.4% | 0.000 | 0.0% |
| `surrogate_probe_tight_capacity` | `bid_price` | - | $1,676,454 | +/- $153,109 | 100.7% | 0.000 | 0.0% |
| `surrogate_probe_tight_capacity` | `surrogate_linear` | - | $1,634,453 | +/- $188,212 | 98.2% | 0.002 | 0.0% |
| `surrogate_probe_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,668,455 | +/- $147,371 | 100.2% | 0.941 | 43.0% |
| `surrogate_probe_tight_capacity` | `rollout_teacher` | - | $1,665,064 | +/- $21,676 | 100.0% | 2.608 | 100.0% |

## Aggregate Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `surrogate_probe_mild_capacity` | 0 | 99.7% | $1,730,610 | 0.129 | 7.0% |
| `surrogate_probe_mild_capacity` | 100 | 99.8% | $1,730,733 | 0.135 | 7.1% |
| `surrogate_probe_mild_capacity` | 250 | 99.8% | $1,731,358 | 0.151 | 7.6% |
| `surrogate_probe_mild_capacity` | 500 | 99.7% | $1,729,747 | 0.165 | 7.9% |
| `surrogate_probe_mild_capacity` | 700 | 99.7% | $1,729,747 | 0.196 | 8.8% |
| `surrogate_probe_mild_capacity` | 900 | 99.7% | $1,729,747 | 0.254 | 10.4% |
| `surrogate_probe_mild_capacity` | 1,200 | 99.7% | $1,729,958 | 0.394 | 14.3% |
| `surrogate_probe_scarce_capacity` | 0 | 87.0% | $1,256,763 | 0.149 | 12.6% |
| `surrogate_probe_scarce_capacity` | 100 | 87.7% | $1,266,772 | 0.297 | 17.8% |
| `surrogate_probe_scarce_capacity` | 250 | 89.3% | $1,290,006 | 0.468 | 22.9% |
| `surrogate_probe_scarce_capacity` | 500 | 91.9% | $1,327,477 | 0.730 | 31.2% |
| `surrogate_probe_scarce_capacity` | 700 | 94.1% | $1,358,940 | 0.940 | 40.8% |
| `surrogate_probe_scarce_capacity` | 900 | 95.7% | $1,382,156 | 1.113 | 49.0% |
| `surrogate_probe_scarce_capacity` | 1,200 | 98.7% | $1,424,406 | 1.461 | 68.3% |
| `surrogate_probe_tight_capacity` | 0 | 98.6% | $1,641,590 | 0.248 | 15.7% |
| `surrogate_probe_tight_capacity` | 100 | 98.7% | $1,644,161 | 0.402 | 21.0% |
| `surrogate_probe_tight_capacity` | 250 | 99.9% | $1,664,178 | 0.630 | 29.9% |
| `surrogate_probe_tight_capacity` | 500 | 100.2% | $1,668,455 | 0.941 | 43.0% |
| `surrogate_probe_tight_capacity` | 700 | 101.2% | $1,684,870 | 1.172 | 51.9% |
| `surrogate_probe_tight_capacity` | 900 | 101.5% | $1,689,598 | 1.366 | 59.4% |
| `surrogate_probe_tight_capacity` | 1,200 | 100.6% | $1,675,013 | 1.636 | 67.8% |

## Package Artifacts

- `data/processed/experimental_policy_runs.csv`: one row per seed, policy, and cascade band.
- `data/processed/experimental_static_label_fit.csv`: one row per seed with held-out rollout-label fit.
- `data/processed/experimental_policy_summary.csv`: aggregate policy table with variance and confidence intervals.
- `data/processed/experimental_frontier_summary.csv`: aggregate cascade frontier table.

## Interpretation

This is now a paper-style experimental package rather than a single illustrative
run. It gives the paper a reproducible protocol, repeated stochastic seeds,
scenario stress tests, held-out rollout-label diagnostics, and a latency-profit
frontier.

The finite rollout teacher should be interpreted as a stochastic benchmark, not
as an oracle. When a cheap policy exceeds 100% retention, it means that policy
earned more realized closed-loop profit than the finite-lookahead teacher on
that seed average.

The package is still a preliminary version. Before making final claims, the
next upgrades are a stronger surrogate, plotting scripts, and a public release
README that pins the data-preparation commands.
