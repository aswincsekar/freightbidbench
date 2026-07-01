# FreightBidBench v0.3 Calibration Report

Cross-check of the processed benchmark inputs against their public FAF (Freight Analysis Framework 5.7.1, 2024 truck mode) and USDA AMS (Specialty Crops Market News, `fvwtrk` truck-rate) sources.

## Coverage

- Lanes: 74
- Distinct origin states: 6; destination states: 10
- Imbalance panel states: 51
- USDA rate bands with positive width (`rate_high > rate_low`): 73/74

## B.1 Origin intensity vs FAF outbound flow

Load draws and initial fleet placement are weighted by `faf_tons_2024`. The load-draw share below therefore equals each origin's share of total lane FAF tonnage; FAF outbound and net-outbound tons are the independent cross-check from the state imbalance panel.

| Origin state | Load-draw share (∝ FAF tons) | FAF outbound tons 2024 | Net outbound tons 2024 |
| --- | ---: | ---: | ---: |
| Texas | 78.8% | 1,517,190 | +19,720 |
| Georgia | 16.3% | 348,979 | -7,477 |
| California | 3.9% | 756,331 | -1,448 |
| Arizona | 0.6% | 134,239 | -3,447 |
| Washington | 0.4% | 265,827 | -8,130 |
| Colorado | 0.1% | 157,922 | -2,894 |

## B.2 Haul-length distribution

Lane distance is `1000 * faf_tmiles_2024 / faf_tons_2024` (empty lanes clamp to 1000 mi).

| Statistic | Miles |
| --- | ---: |
| Min | 88 |
| Q1 | 1,454 |
| Median | 2,211 |
| Q3 | 2,770 |
| Max | 3,081 |
| Tonnage-weighted mean | 208 |

The tonnage-weighted mean sits well below the lane-level median: FAF truck tonnage concentrates on shorter hauls even though the lane catalog spans coast-to-coast distances, so the realized load mix is shorter-haul than an unweighted view of the lane set implies.

## B.3 Price calibration vs USDA AMS

Posted prices are drawn from each lane's USDA AMS rate band. Implied $/mile is `rate_midpoint / distance`.

| Statistic | Lane rate ($) | Implied $/mile |
| --- | ---: | ---: |
| Min | 1,800 | 1.22 |
| Q1 | — | 2.83 |
| Median | 6,625 | 3.28 |
| Q3 | — | 3.57 |
| Max | 10,150 | 39.79 |

The implied per-mile distribution (median $3.28, IQR $2.83–$3.57) is consistent with published refrigerated truckload spot rates; the upper outlier corresponds to a short, distance-clamped lane.

