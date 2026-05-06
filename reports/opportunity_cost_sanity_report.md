# Opportunity-Cost Sanity Report

## Configuration

- Random seed: 20260505
- Simulated candidate loads: 5,000
- Base cost per loaded mile: $2.75
- Fixed load cost: $250
- State opportunity-value scale: $2500
- Input lane table: `data/processed/v1_usda_faf_mapped_lanes.csv`

## Decision Disagreement

- Agree accept: 4,885
- Agree reject: 25
- Myopic accepts but value-aware rejects: 51
- Myopic rejects but value-aware accepts: 39
- Total disagreement rate: 1.8%

## Objective Comparison

This sanity objective is immediate margin plus downstream state opportunity value, not final closed-loop fleet profit.

- Myopic accepted-load objective: $10,659,213
- Value-aware accepted-load objective: $10,744,322
- Objective lift: $85,109
- Myopic direct accepted-load margin: $10,866,786
- Value-aware direct accepted-load margin: $10,760,647

## Trap Examples

These loads have positive direct margin but negative downstream-adjusted value.

- Texas -> Miami (Florida): margin $1,719, opp delta $-4,365, adjusted $-2,646
- Texas -> Miami (Florida): margin $1,852, opp delta $-4,365, adjusted $-2,513
- Texas -> Miami (Florida): margin $1,907, opp delta $-4,365, adjusted $-2,458
- Texas -> Miami (Florida): margin $1,915, opp delta $-4,365, adjusted $-2,450
- Texas -> Miami (Florida): margin $1,983, opp delta $-4,365, adjusted $-2,382

## Repositioning Examples

These loads have negative direct margin but positive downstream-adjusted value.

- California -> Dallas (Texas): margin $-15, opp delta $2,002, adjusted $1,987
- California -> Dallas (Texas): margin $-51, opp delta $2,002, adjusted $1,951
- California -> Dallas (Texas): margin $-74, opp delta $2,002, adjusted $1,928
- California -> Dallas (Texas): margin $-92, opp delta $2,002, adjusted $1,910
- California -> Chicago (Illinois): margin $-119, opp delta $1,061, adjusted $943

## Interpretation

The seed benchmark passes the first sanity check if both trap and repositioning cases appear in nontrivial numbers. That means the public-calibrated lane table can support experiments where myopic margin rules are measurably different from opportunity-cost-aware policies.

Next step: replace this one-shot value rule with a closed-loop simulator where accepted loads move trucks and future load arrivals are sampled over a horizon.
