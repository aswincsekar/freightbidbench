# Paired Policy Delta Summary

Negative values mean the policy earns less closed-loop profit than the finite rollout teacher on the same train/eval seed pair.

| Scenario | Policy | N | Mean Delta | Paired Bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: |
| `mild` | Accept all feasible | 10 | $873 | [-$23,409, $25,635] |
| `mild` | Myopic | 10 | -$2,506 | [-$27,093, $21,821] |
| `mild` | Bid price | 10 | $1,369 | [-$22,469, $25,525] |
| `mild` | Linear surrogate | 10 | -$25,392 | [-$47,721, -$2,942] |
| `mild` | Cascade +/- $500 | 10 | -$4,178 | [-$18,200, $11,036] |
| `tight` | Accept all feasible | 10 | -$111,182 | [-$133,100, -$86,492] |
| `tight` | Myopic | 10 | -$112,717 | [-$137,070, -$87,354] |
| `tight` | Bid price | 10 | -$109,541 | [-$134,845, -$83,402] |
| `tight` | Linear surrogate | 10 | -$70,979 | [-$98,442, -$37,747] |
| `tight` | Cascade +/- $500 | 10 | -$23,314 | [-$61,173, $11,641] |
| `scarce` | Accept all feasible | 10 | -$136,763 | [-$171,657, -$105,385] |
| `scarce` | Myopic | 10 | -$143,212 | [-$179,487, -$109,938] |
| `scarce` | Bid price | 10 | -$144,819 | [-$179,732, -$112,144] |
| `scarce` | Linear surrogate | 10 | -$109,592 | [-$162,897, -$65,188] |
| `scarce` | Cascade +/- $500 | 10 | -$20,734 | [-$33,394, -$7,200] |
