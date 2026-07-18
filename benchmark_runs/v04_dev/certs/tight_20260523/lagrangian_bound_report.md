# FreightBidBench v0.3 Lagrangian-per-truck Upper Bound

## Configuration

- Scenario: `tight` (`freightbidbench_tight_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260523`
- Realized loads: `1037`
- Fleet size: `70`
- Subgradient iterations: `45`
- Step scale: `100.0`
- Runtime: `7031.42` seconds

## Bound Trajectory

| Quantity | Value |
| --- | ---: |
| Initial bound L(0) | $2,519,983 |
| Final best bound min_n L(lambda_n) | $1,984,516 |
| Final iteration constraint over-use count | 17 |

The initial bound at lambda = 0 corresponds to the per-truck offline DP
without any inter-truck assignment penalty: each truck is allowed to
accept any feasible load independently, with potential duplication across
trucks. As lambda climbs through subgradient ascent, duplicate accepts
become costly to the per-truck sub-MDP solver and the bound tightens.

## Interpretation

This is an information-relaxation upper bound in the sense of Brown,
Smith, and Sun (2010): the relaxation provides perfect future
information to each truck independently while the assignment constraint
is dualized. The bound is valid by weak duality. Tightness depends on
how well the dualized assignment constraint approximates the joint
single-assignment integrality.

State-space bucketing favors the upper bound: clocks are rounded down
to the most-permissive corner of each bucket so the per-truck DP can
only over-estimate the per-truck Lagrangian sup, preserving the
joint upper-bound guarantee.
