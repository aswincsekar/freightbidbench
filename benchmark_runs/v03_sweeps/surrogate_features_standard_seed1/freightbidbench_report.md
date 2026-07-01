# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $500
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 93.83 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 1 | 60.0% | $902 | $1,797 |
| `freightbidbench_tight_capacity` | 1 | 80.0% | $714 | $1,230 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $25,837 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $25,837 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $808,139 | +/- $0 | 75.8% | 0.016 | 0.0% | 0.0 | $0 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $800,139 | +/- $0 | 75.1% | 0.000 | 0.0% | 796.0 | $8,000 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $800,259 | +/- $0 | 75.1% | 0.001 | 0.0% | 784.0 | $7,880 | $22,244 | 1,270 | 479 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $159,252 | +/- $0 | 14.9% | 0.054 | 0.0% | 1.0 | $10 | $25,837 | 0 | 69 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $157,203 | +/- $0 | 14.8% | 3.259 | 10.6% | 0.0 | $0 | $25,671 | 20 | 62 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,065,656 | +/- $0 | 100.0% | 19.865 | 100.0% | 0.0 | $0 | $24,464 | 1,410 | 418 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 2.4% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,114,158 | +/- $0 | 87.5% | 0.022 | 0.0% | 0.0 | $0 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,108,748 | +/- $0 | 87.1% | 0.000 | 0.0% | 523.0 | $5,410 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,108,838 | +/- $0 | 87.1% | 0.001 | 0.0% | 513.0 | $5,320 | $27,099 | 1,720 | 633 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,185,142 | +/- $0 | 93.1% | 0.035 | 0.0% | 0.0 | $0 | $29,240 | 1,630 | 592 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,213,060 | +/- $0 | 95.3% | 13.693 | 51.3% | 0.0 | $0 | $30,649 | 1,680 | 571 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,273,395 | +/- $0 | 100.0% | 31.725 | 100.0% | 0.0 | $0 | $29,206 | 1,780 | 546 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 15.3% | $162,733 | 1.025 | 4.9% |
| `freightbidbench_scarce_capacity` | 500 | 14.8% | $157,203 | 3.259 | 10.6% |
| `freightbidbench_tight_capacity` | 0 | 96.5% | $1,228,475 | 15.890 | 60.7% |
| `freightbidbench_tight_capacity` | 500 | 95.3% | $1,213,060 | 13.693 | 51.3% |

## Output Files

- `benchmark_runs/v03_sweeps/surrogate_features_standard_seed1/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_standard_seed1/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_standard_seed1/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_standard_seed1/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/surrogate_features_standard_seed1/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
