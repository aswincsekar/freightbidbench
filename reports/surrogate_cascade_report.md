# Surrogate And Cascade Report

## Configuration

- Scenario: `surrogate_probe_tight_capacity`
- Train seed: 20260506
- Eval seed: 20260507
- Train rollout labels: 1,023
- Eval rollout labels: 996
- Rollout label target: `rollout_incremental_value`
- Linear target scale: $5,000
- Cascade rollout escalation band: +/- $500
- Total script runtime: 15.60 seconds

## Offline Label Fit

- Held-out rollout accept/reject agreement: 78.8%
- Held-out incremental-value MAE: $1,776
- Held-out p90 absolute error: $3,675

## Closed-Loop Policy Results

| Policy | Profit | Retention vs Rollout | Accepted | No Truck | Mean Latency ms | p95 Latency ms | Rollout Stage Share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rollout_teacher | $1,661,623 | 100.0% | 755 | 0 | 2.755 | 3.585 | 100.0% |
| cascade_surrogate_rollout | $1,614,759 | 97.2% | 733 | 0 | 0.902 | 3.487 | 40.3% |
| bid_price | $1,606,667 | 96.7% | 743 | 224 | 0.000 | 0.001 | 0.0% |
| surrogate_linear | $1,562,445 | 94.0% | 701 | 3 | 0.003 | 0.003 | 0.0% |
| myopic_margin | $1,555,588 | 93.6% | 716 | 258 | 0.000 | 0.000 | 0.0% |

## Cascade Frontier

| Band +/- $ | Profit Retention | Rollout Share | Mean Latency ms | Profit |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 95.1% | 16.5% | 0.258 | $1,579,424 |
| 100 | 95.2% | 22.3% | 0.416 | $1,582,638 |
| 250 | 95.6% | 31.8% | 0.684 | $1,589,198 |
| 500 | 97.2% | 40.3% | 0.903 | $1,614,759 |
| 700 | 98.0% | 49.4% | 1.187 | $1,628,166 |
| 900 | 99.1% | 60.4% | 1.440 | $1,646,977 |
| 1,200 | 99.0% | 67.4% | 1.618 | $1,645,832 |

## Key Findings

- Rollout profit lift over myopic: $106,035
- Linear surrogate profit retention versus rollout: 94.0%
- Cascade profit retention versus rollout: 97.2%
- Mean latency: rollout 2.755 ms, cascade 0.902 ms, surrogate 0.003 ms.

## Interpretation

This is the first end-to-end value-distillation test. The model is deliberately simple, so the important result is not final accuracy. The important question is whether a cheap approximation and a selective rollout cascade can recover useful rollout behavior while reducing online latency.

Next step: replace the linear surrogate with a stronger dependency-light model or generate a larger rollout-label set for an MLP/gradient-boosted baseline.
