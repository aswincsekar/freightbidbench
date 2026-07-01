# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/terminal_value/configs/freightbidbench_v03_terminal_0p5.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 5
- Evaluation load limit: 10
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 2.11 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 40.0% | $1,085 | $2,056 |
| `freightbidbench_tight_capacity` | 1 | 80.0% | $385 | $733 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $51,675 | +/- $0 | 78.2% | 0.000 | 0.0% | 0.0 | $0 | $51,675 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $71,009 | +/- $0 | 107.5% | 0.048 | 0.0% | 0.0 | $0 | $51,675 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $71,009 | +/- $0 | 107.5% | 0.000 | 0.0% | 0.0 | $0 | $51,675 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $71,009 | +/- $0 | 107.5% | 0.001 | 0.0% | 0.0 | $0 | $51,675 | 0 | 12 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $59,671 | +/- $0 | 90.4% | 0.005 | 0.0% | 0.0 | $0 | $51,675 | 0 | 5 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $66,041 | +/- $0 | 100.0% | 39.623 | 100.0% | 0.0 | $0 | $51,675 | 0 | 7 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $59,992 | +/- $0 | 76.9% | 0.000 | 0.0% | 0.0 | $0 | $59,992 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $79,462 | +/- $0 | 101.9% | 0.061 | 0.0% | 0.0 | $0 | $59,992 | 0 | 12 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $79,462 | +/- $0 | 101.9% | 0.000 | 0.0% | 0.0 | $0 | $59,992 | 0 | 12 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $79,462 | +/- $0 | 101.9% | 0.001 | 0.0% | 0.0 | $0 | $59,992 | 0 | 12 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $79,462 | +/- $0 | 101.9% | 0.006 | 0.0% | 0.0 | $0 | $59,992 | 0 | 12 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $77,965 | +/- $0 | 100.0% | 61.924 | 100.0% | 0.0 | $0 | $59,992 | 0 | 8 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 90.4% | $59,671 | 0.007 | 0.0% |
| `freightbidbench_tight_capacity` | 0 | 101.9% | $79,462 | 0.008 | 0.0% |

## Output Files

- `benchmark_runs/v03_sweeps/terminal_value/weight_0p5/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/terminal_value/weight_0p5/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/terminal_value/weight_0p5/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value/weight_0p5/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value/weight_0p5/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
