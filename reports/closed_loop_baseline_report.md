# Closed-Loop Baseline Report

## Configuration

- Random seed: 20260506
- Input lane table: `data/processed/v1_usda_faf_mapped_lanes.csv`

| Scenario | Horizon | Loads | Fleet | Loads/Hour | Cost/Mile | Value Scale |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| base_public_calibrated | 168h | 3,027 | 250 | 18 | $2.85 | $2,200 |
| tight_capacity | 168h | 4,045 | 150 | 24 | $3.10 | $2,200 |
| scarce_capacity_high_demand | 168h | 4,045 | 100 | 24 | $3.10 | $3,000 |

## Key Findings

- `base_public_calibrated` best policy: `myopic_margin` ($6,492,757); lift over myopic: $0.
- `tight_capacity` best policy: `bid_price_conservative` ($7,500,928); lift over myopic: $1,121,045.
- `scarce_capacity_high_demand` best policy: `bid_price_strong_future` ($5,379,267); lift over myopic: $1,182,893.

## Policy Results


### base_public_calibrated

| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | p95 Latency ms | Stranded Trucks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| myopic_margin | $6,492,757 | 100.0% | 2900 | 81 | 39.6% | 0.000209 | 64 |
| lane_score_weak | $6,478,381 | 99.8% | 2880 | 90 | 37.9% | 0.000209 | 57 |
| bid_price | $6,378,207 | 98.2% | 2843 | 113 | 35.8% | 0.000209 | 36 |
| bid_price_conservative | $6,355,949 | 97.9% | 2833 | 112 | 35.4% | 0.000209 | 35 |
| bid_price_strong_future | $6,342,518 | 97.7% | 2831 | 123 | 35.5% | 0.000209 | 35 |
| always_reject | $0 | 0.0% | 0 | 0 | 0.0% | 0.000084 | 0 |

### tight_capacity

| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | p95 Latency ms | Stranded Trucks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bid_price_conservative | $7,500,928 | 100.0% | 3472 | 430 | 71.4% | 0.000208 | 27 |
| bid_price | $7,484,995 | 99.8% | 3459 | 463 | 71.5% | 0.000208 | 30 |
| bid_price_strong_future | $7,424,684 | 99.0% | 3453 | 464 | 71.3% | 0.000208 | 26 |
| lane_score_weak | $6,625,236 | 88.3% | 3025 | 933 | 66.2% | 0.000208 | 66 |
| myopic_margin | $6,379,883 | 85.1% | 2920 | 1041 | 66.3% | 0.000208 | 69 |
| always_reject | $0 | 0.0% | 0 | 0 | 0.0% | 0.000084 | 0 |

### scarce_capacity_high_demand

| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | p95 Latency ms | Stranded Trucks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bid_price_strong_future | $5,379,267 | 100.0% | 2487 | 1423 | 77.1% | 0.000208 | 17 |
| bid_price | $5,229,182 | 97.2% | 2434 | 1482 | 74.9% | 0.000208 | 18 |
| bid_price_conservative | $5,210,347 | 96.9% | 2427 | 1473 | 74.7% | 0.000208 | 18 |
| lane_score_weak | $4,489,482 | 83.5% | 2049 | 1898 | 66.6% | 0.000208 | 40 |
| myopic_margin | $4,196,374 | 78.0% | 1914 | 2047 | 64.7% | 0.000208 | 48 |
| always_reject | $0 | 0.0% | 0 | 0 | 0.0% | 0.000084 | 0 |

## Highest State Opportunity Values In Base Scenario

The first bid-price policies use a simple future-value proxy derived from seed-lane outbound intensity and FAF state imbalance.

- Texas (48): $2,032
- Georgia (13): $-1,091
- Illinois (17): $-1,296
- Massachusetts (25): $-1,408
- California (06): $-1,423
- Maryland (24): $-1,433
- Pennsylvania (42): $-1,494
- Arizona (04): $-1,602
- Colorado (08): $-1,609
- Washington (53): $-1,728

## Interpretation

This is the first closed-loop harness: accepted loads move trucks to destination states and make those trucks unavailable until delivery. The result is not an ADP or rollout teacher yet, but it verifies that policy choices compound through fleet state.

The base public-calibrated setting is intentionally mild. It shows whether simple direct-margin bidding is already enough. The tight-capacity scenarios are stress tests designed to expose downstream opportunity cost by making truck placement scarce.

The next benchmark step is to add a rollout teacher that evaluates accept versus reject by simulating future loads from this same environment.
