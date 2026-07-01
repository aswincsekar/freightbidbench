# FreightBidBench v0.3 Relaxed Hindsight Bound

## Configuration

- Scenario: `tight` (`freightbidbench_tight_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260507`
- Realized loads: `250`
- Fleet size: `70`
- Relaxed truck-hour capacity: `7434.65`
- Runtime: `0.01` seconds

## Relaxed Bounds

| Bound | Profit Ceiling |
| --- | ---: |
| Positive-profit relaxation | $657,237 |
| Fractional truck-hour relaxation | $657,237 |
| Terminal fleet-value add-on | $48,499 |
| Selected reported bound | $657,237 |

The selected bound is the minimum of the listed relaxations. It is an upper
bound because it ignores location, exact sequencing, and integrality while
preserving only relaxed profit and truck-hour capacity constraints.

## Policy Comparison

| Policy | Profit | Retention vs Bound | Gap | Accepted | Infeasible | Mean Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| _Skipped_ | | | | | | |

## Interpretation Rules

- Report this as a relaxed full-horizon ceiling, not as an achievable plan.
- Pair it with exact DP on small prefixes when presenting v0.3 results.
- If the gap is loose, report the looseness directly instead of tuning the
  relaxation until it resembles a policy.
