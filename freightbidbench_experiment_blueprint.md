# FreightBidBench Experiment Blueprint

## Goal

Build a reproducible benchmark and method comparison for real-time truckload bid acceptance without private load-level data.

Primary research question:

> How much closed-loop profit can fast bid evaluators retain relative to high-fidelity stochastic rollout, and how much online latency do they save?

Secondary research question:

> Does a cascaded selective evaluator dominate single-method policies by using stochastic rollout only when the decision is ambiguous or strategically important?

## V1 Scope

Use a refrigerated specialty-crop truckload case:

- FAF calibrates broad OD flow intensity and imbalance.
- USDA FVWTRK calibrates reefer spot-rate ranges and truck availability.
- Synthetic tender generation creates event-level load arrivals and fleet states.
- Policies make accept/reject decisions first.
- Minimum acceptable price is a later extension.

## Environment Specification

### State

```text
S_t = {
  trucks_by_region_and_availability_time,
  current_candidate_load,
  demand_forecast_features,
  lane_rate_features,
  truck_availability_features,
  time_bucket,
  recent_market_shock_state
}
```

### Action

V1 action:

```text
a_t in {accept, reject}
```

Future pricing action:

```text
a_t = minimum_acceptable_price
```

### Reward

```text
reward = load_price - loaded_mile_cost - waiting_cost - repositioning_cost
```

Rejected loads receive zero immediate reward but preserve truck capacity.

### Transition

- If accepted, assign an available truck and update its destination and next availability time.
- If rejected, leave fleet state unchanged.
- Sample future load arrivals from public-calibrated stochastic lane processes.
- Apply demand, price, and capacity shocks according to scenario settings.

## Synthetic Generator

### Inputs

- Region list.
- Lane distance matrix.
- FAF-derived lane intensity.
- FAF-derived inbound/outbound imbalance.
- USDA-derived reefer rate ranges for observed lanes.
- USDA-derived availability categories.
- User-chosen fleet size, horizon, and demand scale.

### Load Generation

For each time bucket:

1. Sample number of candidate loads.
2. Sample origin-destination lane from calibrated lane intensities.
3. Sample commodity/equipment type.
4. Sample pickup and delivery time.
5. Sample price from:

```text
price = base_distance_rate
      + lane_imbalance_premium
      + scarcity_premium
      + random_market_noise
```

6. Mark some loads as trap/repositioning cases through the generator, not by policy labels.

### Truck Generation

- Initialize trucks across regions from inbound/outbound flow structure.
- Assign availability times.
- Assign equipment type.
- Include optional home-region preference only after v1 works.

## Policies To Compare

### Myopic Margin

Accept if immediate price minus direct cost is positive.

### Lane Score

Accept if immediate margin plus historical destination/lane score clears a threshold.

### Bid-Price Heuristic

Estimate opportunity cost by region and time bucket:

```text
accept if immediate_margin >= bid_price(origin, time) - bid_price(destination, delivery_time)
```

### CPU Rollout Teacher

For accept and reject branches:

1. Simulate future demand scenarios.
2. Run a base dispatch/acceptance policy.
3. Estimate expected downstream profit.
4. Choose the action with higher expected value.

### GPU/Vectorized Rollout

Same decision logic as rollout teacher, but vectorize scenarios using JAX or PyTorch.

### MLP Value Surrogate

Train offline to predict:

```text
incremental_value = rollout_value_accept - rollout_value_reject
```

Accept when predicted incremental value is positive.

### Optional GNN

Use only if the benchmark includes transfer tests across sparse or held-out lanes.

### Cascaded Selective Evaluator

Stages:

1. Rule-based screen for obvious decisions.
2. MLP value estimate for normal decisions.
3. Rollout for ambiguous or high-stakes decisions.

Escalate if:

- Predicted incremental value is near zero.
- Surrogate uncertainty is high.
- Load price is unusually high.
- Destination is a trap market.
- Truck scarcity is high.
- Lane is sparse or out-of-distribution.

## Metrics

Primary:

- Closed-loop profit.
- Profit retention versus rollout teacher.
- Mean, p50, and p95 decision latency.
- Regret versus teacher.

Operational:

- Loaded miles.
- Empty miles.
- Truck utilization.
- Rejection rate.
- Service failures if included.

Cascade-specific:

- Share handled by rule stage.
- Share handled by surrogate stage.
- Share escalated to rollout.
- Profit and regret by stage.
- Latency by stage.

Calibration:

- OD intensity correlation with FAF.
- Imbalance rank correlation with FAF.
- USDA-observed lane-rate fit.
- Availability shock distribution.

## Experiments

### E1: Calibration Validity

Show generated loads preserve public marginals:

- OD intensity.
- Regional imbalance.
- Rate ranges on USDA-observed lanes.
- Availability categories.

### E2: Opportunity-Cost Sanity Checks

Construct diagnostic scenarios:

- High-margin trap destination.
- Low-margin repositioning move.
- Scarce truck in strong market.
- Demand shock.

Expected result: rollout and value-aware policies behave differently from myopic policies.

### E3: Latency-Profit Frontier

Run all policies across identical seeds.

Expected result: cascaded evaluator sits near rollout profit with far lower latency.

### E4: Robustness

Stress test:

- Demand volatility.
- Price volatility.
- Capacity shortage.
- Held-out lanes.
- Seasonal shift.

Expected result: simple surrogates degrade first; cascade remains more stable because it escalates uncertainty.

### E5: Ablations

Remove:

- Public calibration.
- Future-value features.
- Cascade escalation.
- Scarcity signal.
- GPU vectorization.

Expected result: each removal clarifies what drives the frontier.

## First Implementation Milestones

1. Data loader stubs for FAF and USDA.
2. Synthetic generator with manually configurable lane intensities.
3. Myopic, lane-score, and bid-price policies.
4. CPU rollout teacher.
5. Offline teacher-label generation.
6. MLP surrogate.
7. Cascaded evaluator.
8. Closed-loop evaluation harness.
9. Calibration and latency-profit plots.

## Go/No-Go Criteria

Go:

- Myopic policy visibly fails on opportunity-cost cases.
- Rollout improves closed-loop profit.
- MLP learns useful incremental values.
- Cascade uses rollout on a minority of loads while retaining near-teacher profit.

Pivot:

- Public calibration cannot produce plausible flow/rate structure.
- Myopic policy nearly matches rollout.
- Surrogate errors compound badly in closed-loop evaluation.
- Latency accounting shows no practical advantage.

