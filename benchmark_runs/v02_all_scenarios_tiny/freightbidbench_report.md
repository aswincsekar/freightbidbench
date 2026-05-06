# FreightBidBench v0.2 Report

## Configuration

- Benchmark version: `freightbidbench-v0.2`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $500
- Rollout labels per train/eval stream: up to 40
- Evaluation load limit: 50
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, and stochastic yard delays
- Total runtime: 24.65 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mild` | `freightbidbench_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 1 | 100.0% | $483 | $971 |
| `freightbidbench_scarce_capacity` | 1 | 55.0% | $1,000 | $1,769 |
| `freightbidbench_tight_capacity` | 1 | 82.5% | $750 | $1,514 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | `myopic_margin` | - | $95,432 | +/- $0 | 101.5% | 0.000 | 0.0% | 2.0 | 10 | 74 |
| `freightbidbench_mild_capacity` | `bid_price` | - | $95,432 | +/- $0 | 101.5% | 0.001 | 0.0% | 1.0 | 10 | 74 |
| `freightbidbench_mild_capacity` | `surrogate_linear` | - | $94,175 | +/- $0 | 100.2% | 0.005 | 0.0% | 0.0 | 0 | 73 |
| `freightbidbench_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $94,175 | +/- $0 | 100.2% | 0.007 | 0.0% | 0.0 | 0 | 73 |
| `freightbidbench_mild_capacity` | `rollout_teacher` | - | $93,978 | +/- $0 | 100.0% | 80.155 | 100.0% | 0.0 | 10 | 69 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $99,072 | +/- $0 | 150.3% | 0.000 | 0.0% | 0.0 | 10 | 76 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $99,072 | +/- $0 | 150.3% | 0.001 | 0.0% | 0.0 | 10 | 76 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $69,178 | +/- $0 | 104.9% | 0.004 | 0.0% | 0.0 | 0 | 55 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $70,479 | +/- $0 | 106.9% | 17.301 | 48.0% | 0.0 | 10 | 41 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $65,924 | +/- $0 | 100.0% | 36.191 | 100.0% | 0.0 | 10 | 30 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $96,911 | +/- $0 | 120.3% | 0.000 | 0.0% | 1.0 | 10 | 75 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $96,911 | +/- $0 | 120.3% | 0.001 | 0.0% | 1.0 | 10 | 75 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $93,420 | +/- $0 | 116.0% | 0.005 | 0.0% | 0.0 | 0 | 74 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $93,037 | +/- $0 | 115.5% | 7.309 | 14.0% | 0.0 | 10 | 71 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $80,553 | +/- $0 | 100.0% | 56.253 | 100.0% | 0.0 | 10 | 50 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 0 | 100.2% | $94,175 | 0.007 | 0.0% |
| `freightbidbench_mild_capacity` | 500 | 100.2% | $94,175 | 0.007 | 0.0% |
| `freightbidbench_scarce_capacity` | 0 | 106.5% | $70,197 | 0.596 | 2.0% |
| `freightbidbench_scarce_capacity` | 500 | 106.9% | $70,479 | 17.301 | 48.0% |
| `freightbidbench_tight_capacity` | 0 | 117.4% | $94,534 | 1.542 | 4.0% |
| `freightbidbench_tight_capacity` | 500 | 115.5% | $93,037 | 7.309 | 14.0% |

## Output Files

- `benchmark_runs/v02_all_scenarios_tiny/freightbidbench_policy_runs.csv`
- `benchmark_runs/v02_all_scenarios_tiny/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v02_all_scenarios_tiny/freightbidbench_policy_summary.csv`
- `benchmark_runs/v02_all_scenarios_tiny/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v02_all_scenarios_tiny/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
