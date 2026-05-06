# FreightBidBench v0 Report

## Configuration

- Benchmark version: `freightbidbench-v0.1`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 1,200
- Total runtime: 14.63 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 1 | 78.8% | $1,776 | $3,675 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,555,588 | +/- $0 | 93.6% | 0.000 | 0.0% |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,606,667 | +/- $0 | 96.7% | 0.000 | 0.0% |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,562,445 | +/- $0 | 94.0% | 0.002 | 0.0% |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,614,759 | +/- $0 | 97.2% | 0.905 | 40.3% |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,661,623 | +/- $0 | 100.0% | 2.744 | 100.0% |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 95.1% | $1,579,424 | 0.246 | 16.5% |
| `freightbidbench_tight_capacity` | 100 | 95.2% | $1,582,638 | 0.412 | 22.3% |
| `freightbidbench_tight_capacity` | 250 | 95.6% | $1,589,198 | 0.671 | 31.8% |
| `freightbidbench_tight_capacity` | 500 | 97.2% | $1,614,759 | 0.905 | 40.3% |
| `freightbidbench_tight_capacity` | 700 | 98.0% | $1,628,166 | 1.172 | 49.4% |
| `freightbidbench_tight_capacity` | 900 | 99.1% | $1,646,977 | 1.420 | 60.4% |
| `freightbidbench_tight_capacity` | 1,200 | 99.0% | $1,645,832 | 1.618 | 67.4% |

## Output Files

- `faster_planning/benchmark_runs/smoke/freightbidbench_policy_runs.csv`
- `faster_planning/benchmark_runs/smoke/freightbidbench_static_label_fit.csv`
- `faster_planning/benchmark_runs/smoke/freightbidbench_policy_summary.csv`
- `faster_planning/benchmark_runs/smoke/freightbidbench_frontier_summary.csv`
- `faster_planning/benchmark_runs/smoke/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
