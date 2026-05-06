# Rollout Teacher Report

## Configuration

- Scenario: `rollout_probe_tight_capacity`
- Horizon: 72 hours
- Loads/hour target: 14
- Fleet size: 70
- Rollout replications per decision: 5
- Rollout lookahead window: 18 hours
- Future rollout load rate: 10 loads/hour
- Future base policy: `rollout_base_bid_price`
- Total script runtime: 2.60 seconds

## Policy Results

| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | Mean Latency ms | p95 Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rollout_teacher | $1,660,405 | 100.0% | 744 | 0 | 81.9% | 2.528 | 3.492 |
| bid_price | $1,627,144 | 98.0% | 754 | 231 | 80.1% | 0.001 | 0.001 |
| myopic_margin | $1,437,245 | 86.6% | 664 | 336 | 79.3% | 0.000 | 0.000 |

## Key Findings

- Rollout profit lift over myopic: $223,160
- Rollout profit retention versus best policy in this probe: 100.0%
- The rollout teacher is much slower than the analytic bid-price policies, which is exactly the latency gap the paper should later exploit with surrogates or cascades.

## Interpretation

This is the first CPU rollout teacher. For each online candidate load, it compares accept and reject by running common-random-number future simulations from the branch fleet states. It is intentionally small and not optimized.

The next step is to turn rollout decisions into offline labels and test whether a cheap surrogate or cascade can recover most of the rollout behavior at bid-price-like latency.
