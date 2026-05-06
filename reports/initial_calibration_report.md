# Initial Calibration Report

## Inputs Inspected

- FAF state package: `data/raw/faf/FAF5.7.1_State.zip`
- USDA truck-rate PDF text: `data/raw/usda/fvwtrk.txt`

## FAF State Schema Summary

- Total CSV rows inspected: 1,198,666
- Domestic truck rows used for v1 summaries: 90,245
- Mode counts:

- mode 1 (Truck): 398,085 rows
- mode 4 (Air (include truck-air)): 311,835 rows
- mode 5 (Multiple modes & mail): 247,728 rows
- mode 2 (Rail): 188,008 rows
- mode 3 (Water): 36,247 rows
- mode 7 (Other and unknown): 14,816 rows
- mode 6 (Pipeline): 1,868 rows
- mode 8 (No domestic mode): 79 rows

The FAF metadata workbook confirms `dms_mode == 1` maps to Truck.

## Top FAF State Truck Lanes By 2024 Tons

- Texas -> Texas: 1,384,702.7 tons
- California -> California: 686,896.1 tons
- Florida -> Florida: 556,814.9 tons
- Illinois -> Illinois: 483,328.2 tons
- Ohio -> Ohio: 344,832.2 tons
- New York -> New York: 322,589.6 tons
- Iowa -> Iowa: 302,043.1 tons
- Wisconsin -> Wisconsin: 298,222.1 tons
- Minnesota -> Minnesota: 294,291.4 tons
- Pennsylvania -> Pennsylvania: 293,798.1 tons

## Largest State Imbalances By 2024 Truck Tons

- Florida: -26,436.1 net outbound tons
- Iowa: +20,306.3 net outbound tons
- Texas: +19,720.1 net outbound tons
- Tennessee: +16,032.0 net outbound tons
- Minnesota: -13,169.1 net outbound tons
- Alabama: +10,300.7 net outbound tons
- New Hampshire: -9,922.8 net outbound tons
- Illinois: +9,774.1 net outbound tons
- Nebraska: -9,751.4 net outbound tons
- North Carolina: -9,468.7 net outbound tons

## Top FAF Truck Commodities By 2024 Tons

- SCTG 12 (Gravel): 1,764,725.4 tons
- SCTG 31 (Nonmetal min. prods.): 1,020,169.7 tons
- SCTG 02 (Cereal grains): 1,008,343.9 tons
- SCTG 17 (Gasoline): 851,748.2 tons
- SCTG 41 (Waste/scrap): 617,604.3 tons
- SCTG 07 (Other foodstuffs): 577,227.9 tons
- SCTG 25 (Logs): 573,860.8 tons
- SCTG 11 (Natural sands): 566,282.0 tons
- SCTG 18 (Fuel oils): 563,892.0 tons
- SCTG 03 (Other ag prods.): 552,917.0 tons

## USDA FVWTRK Summary

- Report date parsed from PDF: April 29,2026
- Parsed lane-rate quotes: 74
- Availability categories observed:

- Slight Shortage: 34 lane quotes
- Adequate: 30 lane quotes
- Shortage: 6 lane quotes
- Slight Surplus: 4 lane quotes

## USDA-To-FAF Lane Mapping

- USDA quotes with mapped origin/destination states: 74 of 74
- Mapped USDA quotes with positive FAF 2024 truck flow on the same state OD lane: 74

Sample mapped lanes:

- Arizona -> Atlanta (Georgia): $6,100, Slight Surplus, FAF tons 169.1
- Arizona -> Baltimore (Maryland): $8,100, Adequate, FAF tons 36.7
- Arizona -> Boston (Massachusetts): $9,100, Slight Surplus, FAF tons 70.9
- Arizona -> Chicago (Illinois): $5,300, Adequate, FAF tons 235.5
- Arizona -> Dallas (Texas): $3,600, Slight Surplus, FAF tons 1,828.7
- Arizona -> Los Angeles (California): $2,000, Slight Surplus, FAF tons 8,362.7
- Arizona -> New York (New York): $8,500, Adequate, FAF tons 115.8
- Arizona -> Philadelphia (Pennsylvania): $8,300, Adequate, FAF tons 109.7
- California -> Atlanta (Georgia): $6,450, Slight Shortage, FAF tons 1,459.5
- California -> Boston (Massachusetts): $9,300, Slight Shortage, FAF tons 509.2

## Calibration Decision

The first benchmark can proceed with a state-level FAF backbone and a USDA reefer rate subset.

Recommended v1:

1. Use FAF state-level domestic truck rows for OD intensity and imbalance.
2. Use USDA FVWTRK lane quotes for reefer rate ranges and availability shocks.
3. Use `data/processed/v1_usda_faf_mapped_lanes.csv` as the first seed lane table.
4. Generate synthetic event-level tenders from those public marginals.
5. Keep all realism claims constrained to public calibration, not real tender validation.

## Immediate Next Build Steps

1. Refine mixed-origin USDA mappings, especially CA/AZ border districts.
2. Decide whether v1 should use all truck FAF flows or only food/agricultural SCTG groups.
3. Implement the first synthetic tender generator from the processed CSV summaries.
4. Run opportunity-cost sanity checks before training any model.
