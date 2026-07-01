# FreightBidBench v0.3 Relaxed Hindsight Bound

## Configuration

- Scenario: `tight` (`freightbidbench_tight_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260507`
- Realized loads: `995`
- Fleet size: `70`
- Relaxed truck-hour capacity: `7516.75`
- Runtime: `0.01` seconds

## Relaxed Bounds

| Bound | Profit Ceiling |
| --- | ---: |
| Positive-profit relaxation | $2,377,500 |
| Fractional truck-hour relaxation | $2,377,500 |
| Terminal fleet-value add-on | $48,499 |
| Selected reported bound | $2,377,500 |

The selected bound is the minimum of the listed relaxations. It is an upper
bound because it ignores location, exact sequencing, and integrality while
preserving only relaxed profit and truck-hour capacity constraints.

## Policy Comparison

| Policy | Profit | Retention vs Bound | Gap | Accepted | Infeasible | Mean Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `reject_all` | $29,996 | 1.3% | $2,347,504 | 0 | 0 | 0.000 |
| `accept_all_feasible` | $1,114,158 | 46.9% | $1,263,342 | 441 | 0 | 0.031 |
| `myopic_margin` | $1,108,748 | 46.6% | $1,268,752 | 441 | 523 | 0.000 |
| `bid_price` | $1,108,838 | 46.6% | $1,268,662 | 441 | 513 | 0.001 |

## Interpretation Rules

- Report this as a relaxed full-horizon ceiling, not as an achievable plan.
- Pair it with exact DP on small prefixes when presenting v0.3 results.
- If the gap is loose, report the looseness directly instead of tuning the
  relaxation until it resembles a policy.
