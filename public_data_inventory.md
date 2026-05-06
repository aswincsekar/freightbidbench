# Public Data Inventory For FreightBidBench

## Purpose

This file tracks public data sources we can use to calibrate a synthetic truckload bid-acceptance benchmark without private carrier, broker, or load-board data.

The intended claim is not that the benchmark reproduces real tender histories. The intended claim is:

> FreightBidBench generates synthetic stochastic tender streams calibrated to public freight-flow, truck-rate, and truck-availability marginals, then evaluates real-time bid-decision methods under transparent and reproducible conditions.

## Source Matrix

| Source | Owner | Coverage | Useful Fields | Use In Benchmark | Limitations | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| Freight Analysis Framework FAF5.7.1 regional database | BTS / FHWA | U.S. freight flows by origin-destination FAF regions, commodity type, and mode | Weight, value, activity/ton-miles, origin, destination, commodity, mode, annual estimates and forecasts | Calibrate OD demand intensity, commodity mix, regional imbalance, broad truck-flow backbone | Not tender-level; large FAF zones; annual rather than event-level | Must use |
| FAF5.7.1 state database | BTS / FHWA | U.S. freight flows by origin-destination state, commodity type, and mode | Weight, value, origin state, destination state, commodity, mode | Simpler alternative if FAF regions are too coarse or harder to explain | State-level aggregation hides metro/market structure | Use if helpful |
| FAF5 experimental county-level estimates | BTS | County-to-county estimates based on FAF5.6.1, with state-specific files and disaggregation factors | County/FAF mixed geography, five commodity groups, mode groups, tonnage | Optional finer geography for a focused regional case | Experimental; based on older FAF version; more complex; aggregated commodity/mode groups | Later |
| Specialty Crops National Truck Rate Report, FVWTRK report 2375 | USDA AMS / My Market News | Refrigerated specialty-crop truckload rates from major shipping areas to selected U.S. destination markets | Spot truckload rate ranges, origin shipping areas, destination cities, weekly report dates, truck availability categories | Calibrate reefer rate distributions, capacity scarcity, and selected benchmark lanes | Narrow commodity/equipment scope; selected destinations only; reports are not full load-board histories | Must use for reefer case |
| USDA Specialty Crops Market News datasets | USDA AMS | Specialty-crop prices, movement, truck rates, trends, terminal and shipping point reports | Movement, rate, trend, commodity and market signals depending on report | Optional seasonal and commodity demand signals for reefer benchmark | Requires report-specific extraction; not all fields align directly to tender generation | Use if easy |
| FAF truck network database / flow assignment | BTS / FHWA | Truck network and assigned flows for selected years | Network links and assigned truck flows | Optional distance/network realism and lane grouping | More infrastructure-heavy; not needed for first bid-decision benchmark | Later |

## Recommended V1 Dataset

Use a **reefer specialty-crop truckload benchmark**:

- FAF regional or state truck flows define the broad OD demand backbone.
- USDA FVWTRK rates define observed refrigerated lane rate ranges.
- USDA FVWTRK availability categories define capacity-scarcity shocks.
- Synthetic generation fills missing event-level details: arrival times, load sizes, truck states, accepted/rejected history, and unobserved lane prices.

This is narrow enough to calibrate honestly and broad enough to demonstrate opportunity-cost bidding.

## Data Extraction Plan

### FAF

1. Download the FAF5.7.1 regional CSV package.
2. Filter to truck mode.
3. Keep a small set of commodity groups relevant to refrigerated or agricultural freight first.
4. Aggregate OD annual weights and values into lane intensity scores.
5. Compute outbound/inbound imbalance by region:

```text
imbalance(region) = outbound_truck_weight(region) - inbound_truck_weight(region)
```

6. Convert annual lane intensity to stochastic load-arrival rates:

```text
lambda(origin, destination, commodity) proportional to FAF_weight_or_value
```

7. Normalize arrival rates so the simulator has a chosen operational scale, e.g. 500 trucks and 3,000 candidate loads per week.

### USDA FVWTRK

1. Query report id `2375` through My Market News or download PDFs/text reports.
2. Extract report date, origin shipping area, destination city, rate low/high if available, and availability category.
3. Map USDA shipping areas and destination cities to benchmark regions.
4. Fit a lane rate distribution:

```text
rate_per_load ~ distribution(center=reported_midpoint, spread=reported_range_or_default_noise)
```

5. Convert truck availability categories into scarcity multipliers:

```text
surplus -> low scarcity
adequate -> neutral scarcity
shortage -> high scarcity
```

6. Use scarcity multipliers to perturb arrival prices, truck availability, and opportunity cost.

## Calibration Outputs To Save

The eventual implementation should produce:

- `data/processed/regions.csv`
- `data/processed/lanes.csv`
- `data/processed/lane_intensities.csv`
- `data/processed/rate_distributions.csv`
- `data/processed/availability_shocks.csv`
- `data/processed/calibration_report.md`

## Calibration Acceptance Checks

- Top OD lanes in the generated benchmark match the top FAF truck-flow lanes for the selected geography.
- Synthetic inbound/outbound imbalance ranks correlate with FAF-derived imbalance.
- Synthetic reefer rates on USDA-observed lanes fall inside or near observed USDA ranges most of the time.
- Availability shocks reflect USDA categories without overfitting one weekly report.
- The generated environment produces both good immediate-margin decisions and good future-value decisions.

## Claims We Can Make

- Public-flow-calibrated OD structure.
- Public-rate-calibrated reefer lane prices where USDA rates exist.
- Transparent synthetic tender generation.
- Controlled opportunity-cost and latency experiments.

## Claims We Should Avoid

- Real carrier profit validation.
- Real load-board replication.
- Real accept/reject behavior.
- Exact fleet-position realism.
- Private-market bid-price realism.

