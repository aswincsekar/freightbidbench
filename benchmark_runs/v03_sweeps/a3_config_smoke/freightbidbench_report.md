# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `smoke` (One seed pair on the tight scenario for CI and quick checks.)
- Seed pairs: 20260506/20260507
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: 250
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 32.25 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 1 | 60.0% | $1,899 | $4,763 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | `reject_all` | - | $29,996 | +/- $0 | 7.2% | 0.000 | 0.0% | 0.0 | $0 | $29,996 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $460,684 | +/- $0 | 111.3% | 0.036 | 0.0% | 0.0 | $0 | $28,819 | 560 | 250 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $459,994 | +/- $0 | 111.1% | 0.000 | 0.0% | 68.0 | $690 | $28,819 | 560 | 250 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $459,994 | +/- $0 | 111.1% | 0.001 | 0.0% | 68.0 | $690 | $28,819 | 560 | 250 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $398,468 | +/- $0 | 96.2% | 0.005 | 0.0% | 6.0 | $60 | $29,996 | 130 | 207 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $414,027 | +/- $0 | 100.0% | 43.056 | 100.0% | 0.0 | $0 | $29,136 | 160 | 181 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_tight_capacity` | 0 | 96.4% | $398,919 | 6.297 | 34.4% |

## Output Files

- `benchmark_runs/v03_sweeps/a3_config_smoke/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/a3_config_smoke/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/a3_config_smoke/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/a3_config_smoke/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/a3_config_smoke/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
