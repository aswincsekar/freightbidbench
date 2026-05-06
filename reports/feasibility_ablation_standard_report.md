# FreightBidBench Standard Feasibility Ablation Report

## Configuration

Command:

```bash
python3 scripts/run_feasibility_ablation_suite.py \
  --preset standard \
  --output-dir benchmark_runs/feasibility_ablations_standard
```

The suite ran six variants:

| Ablation | Disabled Features | Runtime |
| --- | --- | ---: |
| `full` | none | 1,273.81 s |
| `no_pickup_reach` | pickup reach time/cost | 1,383.02 s |
| `no_time_windows` | pickup and delivery appointment windows | 2,171.51 s |
| `no_hos` | simplified 11/14/10 HOS clocks | 1,916.06 s |
| `no_yard_delays` | pickup/dropoff yard delays and delay cost | 1,799.78 s |
| `minimal_feasibility` | pickup reach, windows, HOS, yard delays | 1,653.45 s |

Total runtime: 10,197.64 seconds.

Combined outputs:

- `benchmark_runs/feasibility_ablations_standard/feasibility_ablation_index.csv`
- `benchmark_runs/feasibility_ablations_standard/feasibility_ablation_policy_summary.csv`

## Main Result

The standard ablation confirms that the feasibility layer is not cosmetic.
Removing time windows or HOS changes the benchmark regime by more than the
current policy differences. This should become a paper table.

## Myopic Profit Sensitivity

Profit deltas are relative to the full-feasibility myopic policy in the same
scenario.

| Scenario | Full Profit | No Pickup Reach | No Windows | No HOS | No Yard Delays | Minimal Feasibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | $1,082,891 | +28.2% | +58.3% | +57.9% | +25.9% | +67.3% |
| `tight` | $866,894 | +35.1% | +124.3% | +115.5% | +32.5% | +144.9% |
| `scarce` | $718,085 | +30.9% | +194.0% | +154.5% | +27.9% | +218.6% |

## Rollout Teacher Sensitivity

Profit deltas are relative to the full-feasibility finite rollout teacher in
the same scenario.

| Scenario | Full Profit | No Pickup Reach | No Windows | No HOS | No Yard Delays | Minimal Feasibility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | $1,064,003 | +10.0% | +7.0% | +37.8% | +23.8% | +67.8% |
| `tight` | $942,219 | +8.5% | -4.2% | +26.7% | +22.2% | +92.0% |
| `scarce` | $757,682 | +6.8% | -7.6% | +33.8% | +26.7% | +91.9% |

The negative rollout deltas under `no_time_windows` in tight and scarce are a
reminder that the rollout teacher is finite-lookahead and stochastic, not an
oracle.

## Full-Feasibility Myopic Operational Metrics

| Scenario | Infeasible Accepts | Pickup Misses | Delivery Misses | Deadhead Miles | Yard Delay h | HOS Rest h |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | 323.7 | 315.0 | 8.7 | 18,425 | 783 | 2,053 |
| `tight` | 546.7 | 539.7 | 7.0 | 14,873 | 625 | 1,680 |
| `scarce` | 754.3 | 745.7 | 8.7 | 12,102 | 515 | 1,377 |

## Interpretation

The benchmark now has a strong local rigor story:

1. Appointment windows are the largest constraint for fast myopic policies.
   Removing them makes scarce-capacity myopic profit roughly triple.
2. HOS is also first-order: removing HOS more than doubles myopic profit in the
   tight and scarce scenarios.
3. Pickup reach and yard delays matter mainly as cost/time friction. They raise
   profits by roughly 25-35% when removed from fast policies.
4. Minimal feasibility produces a much easier benchmark, where many fast
   policies can match or exceed the finite rollout teacher.

This supports the benchmark-paper claim that closed-loop truckload bid
evaluation needs operational feasibility metrics, not only profit and latency.
