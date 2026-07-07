# FreightBidBench v0.3 Paper Tables

Generated from existing benchmark artifacts. Values are draft table inputs, not prose-ready claims.

## Methods Frontier

| Scenario | Best Simple | Simple Retention | Surrogate Retention | Cascade Band | Cascade Retention | Cascade Latency | Rollout Latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `mild` | `bid_price` | 100.1% | 98.2% | $0 | 99.0% | 5.58 ms | 47.53 ms |
| `tight` | `bid_price` | 91.0% | 94.2% | $500 | 98.2% | 12.88 ms | 31.70 ms |
| `scarce` | `accept_all_feasible` | 86.5% | 89.3% | $700 | 98.4% | 13.97 ms | 20.87 ms |

## Relaxed Full-Horizon Bound

| Scenario | Loads | Relaxed Bound | Best Simple | Simple Retention | Rollout Retention |
| --- | ---: | ---: | --- | ---: | ---: |
| `tight` | 995 | $2,377,500 | `accept_all_feasible` | 46.9% | 53.6% |
| `scarce` | 1154 | $2,675,525 | `accept_all_feasible` | 30.2% | 39.8% |

## Exact Small-Prefix Hindsight

| Scenario | Loads | Hindsight | States | Best Simple | Simple Retention | Rollout Retention |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `tight` | 12 | $53,419 | 8,191 | `accept_all_feasible` | 100.0% | 90.0% |
