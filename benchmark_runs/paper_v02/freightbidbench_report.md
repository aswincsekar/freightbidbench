# FreightBidBench v0.2 Report

## Configuration

- Benchmark version: `freightbidbench-v0.2`
- Preset: `paper` (Ten seed pairs across all regimes for preliminary paper tables.)
- Seed pairs: 20260506/20260507, 20260508/20260509, 20260510/20260511, 20260512/20260513, 20260514/20260515, 20260516/20260517, 20260518/20260519, 20260520/20260521, 20260522/20260523, 20260524/20260525
- Policies: `reject_all`, `accept_all_feasible`, `myopic_margin`, `bid_price`, `surrogate_linear`, `rollout_teacher`, `cascade_surrogate_rollout`
- Cascade bands: +/- $0, +/- $100, +/- $250, +/- $500, +/- $700, +/- $900, +/- $1,200
- Rollout labels per train/eval stream: up to 1,200
- Evaluation load limit: full horizon
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Disabled feasibility features: none
- Total runtime: 4898.54 seconds

| Key | Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `mild` | `freightbidbench_mild_capacity` | 72h | 12 | 90 | $2.95 | $2,400 |
| `tight` | `freightbidbench_tight_capacity` | 72h | 14 | 70 | $3.10 | $3,000 |
| `scarce` | `freightbidbench_scarce_capacity` | 72h | 16 | 55 | $3.20 | $3,400 |

## Offline Label Fit

| Scenario | Runs | Agreement | MAE | p90 Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 10 | 60.9% | $1,989 | $4,332 |
| `freightbidbench_scarce_capacity` | 10 | 69.8% | $2,181 | $3,764 |
| `freightbidbench_tight_capacity` | 10 | 62.6% | $2,099 | $3,851 |

## Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- $500 escalation band.

| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share | Infeasible | HOS Rest h | Yard Delay h |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_mild_capacity` | `accept_all_feasible` | - | $1,052,952 | +/- $38,153 | 99.8% | 0.037 | 0.0% | 0.0 | 2,009 | 758 |
| `freightbidbench_mild_capacity` | `myopic_margin` | - | $1,053,025 | +/- $38,112 | 99.8% | 0.000 | 0.0% | 333.0 | 2,008 | 757 |
| `freightbidbench_mild_capacity` | `bid_price` | - | $1,058,794 | +/- $37,128 | 100.3% | 0.001 | 0.0% | 318.4 | 2,009 | 759 |
| `freightbidbench_mild_capacity` | `surrogate_linear` | - | $875,158 | +/- $64,383 | 82.8% | 0.005 | 0.0% | 113.3 | 1,436 | 641 |
| `freightbidbench_mild_capacity` | `cascade_surrogate_rollout` | 500.00 | $969,668 | +/- $53,197 | 91.8% | 17.293 | 39.3% | 50.2 | 1,619 | 674 |
| `freightbidbench_mild_capacity` | `rollout_teacher` | - | $1,056,144 | +/- $28,206 | 100.0% | 46.170 | 100.0% | 0.0 | 1,825 | 672 |
| `freightbidbench_scarce_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_scarce_capacity` | `accept_all_feasible` | - | $705,492 | +/- $34,440 | 94.0% | 0.016 | 0.0% | 0.0 | 1,353 | 505 |
| `freightbidbench_scarce_capacity` | `myopic_margin` | - | $706,779 | +/- $36,074 | 94.2% | 0.000 | 0.0% | 769.9 | 1,353 | 505 |
| `freightbidbench_scarce_capacity` | `bid_price` | - | $705,933 | +/- $35,514 | 94.1% | 0.001 | 0.0% | 756.5 | 1,348 | 503 |
| `freightbidbench_scarce_capacity` | `surrogate_linear` | - | $518,511 | +/- $28,954 | 69.1% | 0.004 | 0.0% | 117.5 | 876 | 391 |
| `freightbidbench_scarce_capacity` | `cascade_surrogate_rollout` | 500.00 | $574,895 | +/- $36,217 | 76.6% | 6.809 | 36.6% | 9.4 | 960 | 380 |
| `freightbidbench_scarce_capacity` | `rollout_teacher` | - | $750,179 | +/- $10,847 | 100.0% | 17.067 | 100.0% | 0.0 | 1,428 | 430 |
| `freightbidbench_tight_capacity` | `reject_all` | - | $0 | +/- $0 | 0.0% | 0.000 | 0.0% | 0.0 | 0 | 0 |
| `freightbidbench_tight_capacity` | `accept_all_feasible` | - | $846,820 | +/- $25,738 | 92.3% | 0.024 | 0.0% | 0.0 | 1,627 | 615 |
| `freightbidbench_tight_capacity` | `myopic_margin` | - | $850,562 | +/- $24,972 | 92.7% | 0.000 | 0.0% | 552.8 | 1,629 | 616 |
| `freightbidbench_tight_capacity` | `bid_price` | - | $851,672 | +/- $25,250 | 92.9% | 0.001 | 0.0% | 540.1 | 1,629 | 615 |
| `freightbidbench_tight_capacity` | `surrogate_linear` | - | $715,801 | +/- $35,999 | 78.1% | 0.004 | 0.0% | 102.5 | 1,220 | 519 |
| `freightbidbench_tight_capacity` | `cascade_surrogate_rollout` | 500.00 | $777,309 | +/- $32,969 | 84.8% | 10.352 | 38.9% | 32.5 | 1,323 | 521 |
| `freightbidbench_tight_capacity` | `rollout_teacher` | - | $917,440 | +/- $25,147 | 100.0% | 28.813 | 100.0% | 0.0 | 1,711 | 553 |

## Cascade Frontier

| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| `freightbidbench_mild_capacity` | 0 | 84.0% | $886,730 | 2.337 | 8.6% |
| `freightbidbench_mild_capacity` | 100 | 85.5% | $902,514 | 5.490 | 15.1% |
| `freightbidbench_mild_capacity` | 250 | 88.0% | $929,153 | 10.093 | 24.6% |
| `freightbidbench_mild_capacity` | 500 | 91.8% | $969,668 | 17.293 | 39.3% |
| `freightbidbench_mild_capacity` | 700 | 93.3% | $984,829 | 23.302 | 51.0% |
| `freightbidbench_mild_capacity` | 900 | 94.8% | $1,000,692 | 28.215 | 61.0% |
| `freightbidbench_mild_capacity` | 1,200 | 96.0% | $1,013,399 | 32.776 | 70.1% |
| `freightbidbench_scarce_capacity` | 0 | 71.3% | $534,624 | 0.909 | 10.4% |
| `freightbidbench_scarce_capacity` | 100 | 71.7% | $537,584 | 2.208 | 16.2% |
| `freightbidbench_scarce_capacity` | 250 | 72.8% | $545,669 | 4.313 | 26.8% |
| `freightbidbench_scarce_capacity` | 500 | 76.6% | $574,895 | 6.809 | 36.6% |
| `freightbidbench_scarce_capacity` | 700 | 78.6% | $589,394 | 8.149 | 44.1% |
| `freightbidbench_scarce_capacity` | 900 | 83.1% | $622,930 | 9.531 | 52.4% |
| `freightbidbench_scarce_capacity` | 1,200 | 88.9% | $666,945 | 11.153 | 61.3% |
| `freightbidbench_tight_capacity` | 0 | 79.2% | $725,815 | 1.545 | 10.2% |
| `freightbidbench_tight_capacity` | 100 | 79.9% | $732,090 | 3.504 | 16.3% |
| `freightbidbench_tight_capacity` | 250 | 82.6% | $757,356 | 6.164 | 25.8% |
| `freightbidbench_tight_capacity` | 500 | 84.8% | $777,309 | 10.352 | 38.9% |
| `freightbidbench_tight_capacity` | 700 | 87.3% | $800,267 | 13.206 | 48.2% |
| `freightbidbench_tight_capacity` | 900 | 88.0% | $807,035 | 15.780 | 55.7% |
| `freightbidbench_tight_capacity` | 1,200 | 90.5% | $830,346 | 19.323 | 64.6% |

## Output Files

- `benchmark_runs/paper_v02/freightbidbench_policy_runs.csv`
- `benchmark_runs/paper_v02/freightbidbench_static_label_fit.csv`
- `benchmark_runs/paper_v02/freightbidbench_policy_summary.csv`
- `benchmark_runs/paper_v02/freightbidbench_frontier_summary.csv`
- `benchmark_runs/paper_v02/freightbidbench_manifest.json`

## Benchmark Notes

FreightBidBench v0.2 is a public-calibrated synthetic benchmark. It is meant to
test closed-loop bid-evaluation policies under controlled stochastic freight
conditions, not to claim calibrated production-dollar performance.

The finite rollout teacher is a stochastic benchmark, not an oracle. A policy
can exceed 100% retention when it earns higher realized closed-loop profit than
the finite-lookahead rollout teacher on the same seed average.
