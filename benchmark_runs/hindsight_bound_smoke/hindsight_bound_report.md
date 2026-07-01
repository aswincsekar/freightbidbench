# FreightBidBench v0.3 Hindsight-Bound Prototype

## Configuration

- Scenario: `tight` (`freightbidbench_tight_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260507`
- Realized load prefix: `12`
- Fleet size: `70`
- Feasibility layer: pickup reach time, pickup/delivery windows, HOS clocks, stochastic yard delays
- Search states evaluated: `8,191`
- Runtime: `0.42` seconds

## Exact Truncated-Stream Bound

The hindsight optimizer earned $53,419 by accepting
12 of 12 realized loads.

This is an exact accept/reject optimum for the truncated stream under the
current deterministic assignment rule. It is intended as a v0.3 diagnostic
ceiling for small realized streams, not as the final paper-scale bound.

## Policy Comparison

| Policy | Profit | Retention vs Hindsight | Gap | Accepted | Infeasible | Mean Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `reject_all` | $29,996 | 56.2% | $23,423 | 0 | 0 | 0.000 |
| `accept_all_feasible` | $53,419 | 100.0% | $-0 | 12 | 0 | 0.067 |
| `myopic_margin` | $53,419 | 100.0% | $-0 | 12 | 0 | 0.000 |
| `bid_price` | $53,419 | 100.0% | $-0 | 12 | 0 | 0.001 |
| `rollout_teacher` | $48,093 | 90.0% | $5,326 | 9 | 0 | 68.584 |

## Interpretation Rules

- Use this output to debug whether rollout and simple policies sit below a
  realized-seed ceiling on small instances.
- Do not report this as a production dispatch optimum.
- Increase `--max-loads` only after checking `--state-limit`, because the exact
  search can grow exponentially.
