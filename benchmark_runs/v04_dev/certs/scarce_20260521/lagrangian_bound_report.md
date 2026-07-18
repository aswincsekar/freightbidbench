# FreightBidBench v0.3 Lagrangian-per-truck Upper Bound

## Configuration

- Scenario: `scarce` (`freightbidbench_scarce_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260521`
- Realized loads: `1176`
- Fleet size: `55`
- Subgradient iterations: `45`
- Step scale: `100.0`
- Runtime: `6729.99` seconds

## Bound Trajectory

| Quantity | Value |
| --- | ---: |
| Initial bound L(0) | $1,929,932 |
| Final best bound min_n L(lambda_n) | $1,572,173 |
| Final iteration constraint over-use count | 20 |

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
