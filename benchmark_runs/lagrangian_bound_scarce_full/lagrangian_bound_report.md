# FreightBidBench v0.3 Lagrangian-per-truck Upper Bound

## Configuration

- Scenario: `scarce` (`freightbidbench_scarce_capacity`)
- Scenario config: `configs/freightbidbench_v03_scenarios.json`
- Eval seed: `20260507`
- Realized loads: `1154`
- Fleet size: `55`
- Subgradient iterations: `30`
- Step scale: `100.0`
- Runtime: `6414.69` seconds

## Bound Trajectory

| Quantity | Value |
| --- | ---: |
| Initial bound L(0) | $2,018,131 |
| Final best bound min_n L(lambda_n) | $1,623,084 |
| Final iteration constraint over-use count | 19 |

The initial bound at lambda = 0 corresponds to the per-truck offline DP
without any inter-truck assignment penalty: each truck is allowed to
accept any feasible load independently, with potential duplication across
trucks. As lambda climbs through subgradient ascent, duplicate accepts
become costly to the per-truck sub-MDP solver and the bound tightens.

## Comparison vs LP Relaxation

- LP relaxation upper bound (reference): $2,675,525
- Lagrangian best bound: $1,623,084
- Relative tightness: Lagrangian is 39.3% tighter than LP.

## Validity Check vs Rollout Teacher

- Rollout teacher realized profit (reference): $1,065,656
- Lagrangian best bound: $1,623,084
- Validity (bound >= rollout): PASS

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
