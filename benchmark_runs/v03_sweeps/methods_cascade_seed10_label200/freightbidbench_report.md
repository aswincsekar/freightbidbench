# FreightBidBench Report

## Configuration

- Benchmark version: `freightbidbench-v0.3-dev`
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Preset: `standard` (Three seed pairs across mild, tight, and scarce regimes.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511, 20260512/20260513, 20260514/20260515, 20260516/20260517, 20260518/20260519, 20260520/20260521, 20260522/20260523, 20260524/20260525
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $250, +/- $500, +/- $700, +/- $900
- Rollout labels per train/eval stream: up to 200
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 3271.22 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mild` | `freightbidbench_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 10 | 92.6% | $982 | $2,159 |
| `freightbidbench_scarce_capacity` | 10 | 75.0% | $1,163 | $2,419 |
| `freightbidbench_tight_capacity` | 10 | 80.8% | $1,140 | $2,364 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | Service Failure Cost | Terminal Value | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | `reject_all` | - | $34,164 | +/- $2,252 | 2.5% | 0.000 | 0.0% | 0.0 | $0 | $34,164 | 0 | 0 |
| `freightbidbench_mild_capacity` | `accept_all_feasible` | - | $1,373,279 | +/- $55,750 | 100.0% | 0.038 | 0.0% | 0.0 | $0 | $31,930 | 2,009 | 758 |
| `freightbidbench_mild_capacity` | `myopic_margin` | - | $1,369,899 | +/- $55,971 | 99.8% | 0.000 | 0.0% | 336.0 | $3,445 | $31,922 | 2,008 | 757 |
| `freightbidbench_mild_capacity` | `bid_price` | - | $1,373,775 | +/- $52,932 | 100.1% | 0.001 | 0.0% | 326.2 | $3,358 | $32,301 | 2,005 | 758 |
| `freightbidbench_mild_capacity` | `surrogate_linear` | - | $1,347,013 | +/- $44,098 | 98.2% | 0.046 | 0.0% | 0.0 | $0 | $32,906 | 1,932 | 744 |
| `freightbidbench_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,368,228 | +/- $46,304 | 99.7% | 8.313 | 22.2% | 0.0 | $0 | $33,221 | 1,939 | 731 |
| `freightbidbench_mild_capacity` | `rollout_teacher` | - | $1,372,406 | +/- $37,781 | 100.0% | 49.498 | 100.0% | 0.0 | $0 | $33,259 | 1,856 | 687 |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $30,015 | +/- $2,276 | 3.0% | 0.000 | 0.0% | 0.0 | $0 | $30,015 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $874,281 | +/- $42,184 | 86.5% | 0.016 | 0.0% | 0.0 | $0 | $28,580 | 1,353 | 505 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $867,832 | +/- $44,171 | 85.9% | 0.000 | 0.0% | 776.6 | $7,917 | $28,583 | 1,353 | 505 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $866,225 | +/- $43,686 | 85.7% | 0.001 | 0.0% | 764.3 | $7,830 | $28,716 | 1,348 | 503 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $901,452 | +/- $50,805 | 89.3% | 0.032 | 0.0% | 0.0 | $0 | $29,781 | 1,175 | 412 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $990,310 | +/- $25,246 | 98.0% | 11.543 | 59.6% | 0.0 | $0 | $30,023 | 1,318 | 426 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $1,011,044 | +/- $23,710 | 100.0% | 20.588 | 100.0% | 0.0 | $0 | $29,855 | 1,399 | 429 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $33,608 | +/- $2,534 | 2.8% | 0.000 | 0.0% | 0.0 | $0 | $33,608 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $1,095,854 | +/- $34,695 | 90.8% | 0.024 | 0.0% | 0.0 | $0 | $31,598 | 1,627 | 615 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $1,094,319 | +/- $30,441 | 90.7% | 0.000 | 0.0% | 557.5 | $5,701 | $31,612 | 1,631 | 616 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $1,097,495 | +/- $31,443 | 91.0% | 0.001 | 0.0% | 546.3 | $5,605 | $31,914 | 1,634 | 615 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $1,136,058 | +/- $36,270 | 94.2% | 0.036 | 0.0% | 0.0 | $0 | $33,019 | 1,578 | 570 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $1,183,722 | +/- $42,494 | 98.2% | 12.952 | 44.7% | 0.0 | $0 | $33,305 | 1,619 | 558 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $1,207,036 | +/- $34,775 | 100.0% | 32.107 | 100.0% | 0.0 | $0 | $33,140 | 1,641 | 543 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 0 | 99.0% | $1,358,603 | 5.770 | 16.4% |
| `freightbidbench_mild_capacity` | 250 | 99.6% | $1,366,402 | 6.757 | 18.8% |
| `freightbidbench_mild_capacity` | 500 | 99.7% | $1,368,228 | 8.313 | 22.2% |
| `freightbidbench_mild_capacity` | 700 | 100.1% | $1,374,048 | 10.059 | 25.6% |
| `freightbidbench_mild_capacity` | 900 | 100.2% | $1,375,423 | 12.582 | 29.9% |
| `freightbidbench_scarce_capacity` | 0 | 93.7% | $945,796 | 6.091 | 45.4% |
| `freightbidbench_scarce_capacity` | 250 | 96.1% | $970,815 | 9.435 | 53.0% |
| `freightbidbench_scarce_capacity` | 500 | 98.0% | $990,310 | 11.543 | 59.6% |
| `freightbidbench_scarce_capacity` | 700 | 98.4% | $994,217 | 13.799 | 66.5% |
| `freightbidbench_scarce_capacity` | 900 | 99.5% | $1,005,565 | 15.723 | 78.6% |
| `freightbidbench_tight_capacity` | 0 | 97.7% | $1,178,464 | 6.271 | 28.6% |
| `freightbidbench_tight_capacity` | 250 | 97.9% | $1,180,658 | 8.303 | 32.9% |
| `freightbidbench_tight_capacity` | 500 | 98.2% | $1,183,722 | 12.952 | 44.7% |
| `freightbidbench_tight_capacity` | 700 | 98.4% | $1,187,220 | 14.717 | 47.8% |
| `freightbidbench_tight_capacity` | 900 | 99.0% | $1,194,884 | 17.720 | 57.0% |

## Output Files

- `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/freightbidbench_policy_runs.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/freightbidbench_static_label_fit.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/freightbidbench_policy_summary.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/freightbidbench_frontier_summary.csv`
- `benchmark_runs/v03_sweeps/methods_cascade_seed10_label200/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
