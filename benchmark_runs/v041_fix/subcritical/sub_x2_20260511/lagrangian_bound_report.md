# FreightBidBench v0.3 Lagrangian-per-truck Upper Bound

## Configuration

- Scenario: `sub_x2` (`freightbidbench_sub_x2`)
- Scenario config: `configs/freightbidbench_v041_subcritical.json`
- Eval seed: `20260511`
- Realized loads: `1735`
- Fleet size: `240`
- Subgradient iterations: `25`
- Step scale: `100.0`
- Runtime: `180871.99` seconds

## Bound Trajectory

| Quantity | Value |
| --- | ---: |
| Initial bound L(0) | $8,862,911 |
| Final best bound min_n L(lambda_n) | $7,694,285 |
| Final iteration constraint over-use count | 24 |

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
