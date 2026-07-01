# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `benchmark_runs/v03_sweeps/terminal_value_fullseed3/configs/freightbidbench_v03_terminal_0p25.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0
- Rollout labels per train/eval stream: up to 20
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 181.19 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 3 | 60.0% | $2,235 | $3,586 |
| `freightbidbench_tight_capacity` | 3 | 85.0% | $3,511 | $9,012 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $28,805 | +/- $6,709 | 3.7% | 0.000 | 0.0% | 0.0 | $0 | $28,805 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $741,078 | +/- $174,091 | 93.9% | 0.016 | 0.0% | 0.0 | $0 | $26,928 | 1,373 | 512 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $737,385 | +/- $191,264 | 93.4% | 0.000 | 0.0% | 754.3 | $7,680 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $737,475 | +/- $191,113 | 93.4% | 0.001 | 0.0% | 740.0 | $7,590 | $26,980 | 1,377 | 515 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $552,553 | +/- $665,439 | 69.9% | 0.004 | 0.0% | 234.7 | $2,347 | $28,685 | 860 | 356 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $789,637 | +/- $19,673 | 100.0% | 17.433 | 100.0% | 0.0 | $0 | $29,583 | 1,420 | 425 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $32,539 | +/- $7,243 | 3.3% | 0.000 | 0.0% | 0.0 | $0 | $32,539 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $894,944 | +/- $104,166 | 89.6% | 0.024 | 0.0% | 0.0 | $0 | $30,561 | 1,683 | 625 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $892,007 | +/- $113,371 | 89.3% | 0.000 | 0.0% | 546.7 | $5,620 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $892,124 | +/- $113,457 | 89.4% | 0.001 | 0.0% | 533.7 | $5,503 | $30,733 | 1,680 | 625 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $460,270 | +/- $973,065 | 45.9% | 0.004 | 0.0% | 168.7 | $1,697 | $31,894 | 593 | 320 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $998,035 | +/- $90,115 | 100.0% | 30.064 | 100.0% | 0.0 | $0 | $32,581 | 1,790 | 577 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_scarce_capacity` | 0 | 70.5% | $557,755 | 3.034 | 25.8% |
| `freightbidbench_tight_capacity` | 0 | 47.2% | $473,289 | 1.871 | 11.0% |

## Output Files

- `benchmark_runs/v03_sweeps/terminal_value_fullseed3/weight_0p25/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed3/weight_0p25/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed3/weight_0p25/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed3/weight_0p25/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/terminal_value_fullseed3/weight_0p25/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
