# Paired Policy Delta Summary

Negative values mean the policy earns less closed-loop profit than the finite rollout teacher on the same train/eval seed pair.

| Scenario | Policy | N | Mean Delta | Paired Bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: |
| `mild` | Accept all feasible | 10 | -$3,192 | [-$40,126, $27,767] |
| `mild` | Myopic | 10 | -$3,119 | [-$39,436, $28,024] |
| `mild` | Bid price | 10 | $2,650 | [-$30,887, $31,101] |
| `mild` | Linear surrogate | 10 | -$180,986 | [-$231,733, -$136,927] |
| `mild` | Cascade +/- $500 | 10 | -$86,475 | [-$127,858, -$56,708] |
| `tight` | Accept all feasible | 10 | -$70,619 | [-$86,166, -$56,837] |
| `tight` | Myopic | 10 | -$66,877 | [-$84,158, -$52,347] |
| `tight` | Bid price | 10 | -$65,768 | [-$83,425, -$50,163] |
| `tight` | Linear surrogate | 10 | -$201,639 | [-$236,164, -$166,962] |
| `tight` | Cascade +/- $500 | 10 | -$140,130 | [-$166,453, -$114,757] |
| `scarce` | Accept all feasible | 10 | -$44,687 | [-$71,016, -$17,338] |
| `scarce` | Myopic | 10 | -$43,399 | [-$71,023, -$14,574] |
| `scarce` | Bid price | 10 | -$44,246 | [-$71,048, -$15,662] |
| `scarce` | Linear surrogate | 10 | -$231,668 | [-$258,311, -$206,792] |
| `scarce` | Cascade +/- $500 | 10 | -$175,283 | [-$204,922, -$146,102] |
