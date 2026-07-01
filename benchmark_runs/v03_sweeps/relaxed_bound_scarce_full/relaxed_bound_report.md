# FreightBidBench v0.3 Relaxed Hindsight Bound

## Configuration

- Scenario: `scarce` (`freightbidbench_scarce_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260507`
- Realized loads: `1154`
- Fleet size: `55`
- Relaxed truck-hour capacity: `5912.67`
- Runtime: `0.03` seconds

## Relaxed Bounds

| Bound | Profit Ceiling |
| --- | ---: |
| Positive-profit relaxation | $2,710,856 |
| Fractional truck-hour relaxation | $2,675,525 |
| Terminal fleet-value add-on | $43,187 |
| Selected reported bound | $2,675,525 |

The selected bound is the minimum of the listed relaxations. It is an upper
bound because it ignores location, exact sequencing, and integrality while
preserving only relaxed profit and truck-hour capacity constraints.

## Policy Comparison

| Policy | Profit | Retention vs Bound | Gap | Accepted | Infeasible | Mean Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `reject_all` | $25,837 | 1.0% | $2,649,688 | 0 | 0 | 0.000 |
| `accept_all_feasible` | $808,139 | 30.2% | $1,867,386 | 334 | 0 | 0.029 |
| `myopic_margin` | $800,139 | 29.9% | $1,875,386 | 334 | 796 | 0.000 |
| `bid_price` | $800,259 | 29.9% | $1,875,266 | 334 | 784 | 0.001 |

## Interpretation Rules

- Report this as a relaxed full-horizon ceiling, not as an achievable plan.
- Pair it with exact DP on small prefixes when presenting v0.3 results.
- If the gap is loose, report the looseness directly instead of tuning the
  relaxation until it resembles a policy.
