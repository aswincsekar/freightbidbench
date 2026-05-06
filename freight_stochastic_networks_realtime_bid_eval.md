# Real-Time Stochastic Freight Bid Evaluation

## Working Thesis

Truckload carriers and brokers need bid and load-acceptance decisions in seconds, but high-quality stochastic fleet evaluation often depends on approximate dynamic programming, Monte Carlo rollouts, or solver-backed subproblems that are too slow for online execution.

The paper should study the **latency-profit frontier**: how much simulated profit can be retained when replacing a high-fidelity ADP or Monte Carlo evaluator with a much faster approximation.

Because we do not have private load-level carrier or broker data, the v1 paper should be a **public-calibrated benchmark plus methods paper**, not a private-data empirical case study.

Core claim to test:

> A fast bid-evaluation model can retain 95-99% of the profit of a classic ADP or rollout baseline while reducing online decision latency by 100x or more.

This is stronger than claiming a new truck-dispatch optimizer. The contribution is a tractability layer for stochastic freight networks: preserve most of the decision quality while making the decision fast enough to use in real tender workflows.

Revised v1 claim:

> A public-calibrated synthetic truckload benchmark can expose the opportunity-cost failures of myopic bidding and quantify how much closed-loop profit fast bid evaluators retain under realistic latency constraints.

## Why This Is Interesting

Freight bid acceptance is an online stochastic decision. A carrier is not only deciding whether the offered load is profitable by itself; it is deciding whether accepting that load moves a truck into a future state with good or bad downstream opportunity.

Classic ADP-style thinking handles this correctly:

- A truck in Dallas on Tuesday has an opportunity value based on future Dallas, Houston, Oklahoma City, and broader network freight.
- A load from Dallas to Denver has an immediate margin plus a repositioning effect.
- The right bid or accept/reject decision depends on future demand, capacity, driver constraints, and market imbalance.

The weakness is computation. If the online decision requires hundreds or thousands of simulated futures, it may be too slow for live freight brokerage or carrier automation.

The paper should therefore ask:

> Can we move expensive stochastic reasoning offline, or parallelize it aggressively, while preserving enough value quality for operational decisions?

## Candidate Paper Paths

| Path | Idea | Strength | Main Risk | Best Use |
| --- | --- | --- | --- | --- |
| Public-calibrated benchmark + methods | Build FreightBidBench from public freight-flow and truck-rate signals, then evaluate fast bid policies on latency-profit trade-offs. | Solves the no-private-data problem and creates a reproducible contribution. | Reviewers may question simulator realism unless calibration and stress tests are transparent. | Best v1 paper. |
| Cascaded selective evaluator | Use cheap rules for obvious loads, neural value estimates for medium cases, and rollout only for ambiguous or high-value tenders. | Strong practical architecture; does not require replacing ADP everywhere. | Needs careful threshold design and fair latency accounting. | Best v1 method inside the benchmark. |
| Neural surrogate VFA | Run expensive ADP or rollout offline, then train a neural model to approximate bid values or marginal truck values. | Cleanest latency story: offline training, millisecond inference. | Reviewers may say neural value approximation is already known unless the freight bid setting and latency-profit frontier are sharp. | Best first paper. |
| Graph neural network spatial evaluator | Model freight regions as a graph and learn value propagation across nearby markets. | Natural fit for freight geography and network imbalance. | More moving parts; hard to prove the GNN is needed instead of simpler features. | Strong second paper or ablation within the first paper. |
| GPU-parallel rollouts | Keep the stochastic simulation idea, but vectorize thousands of scenarios with JAX or PyTorch. | Lower conceptual risk; preserves interpretability of rollout baseline. | May look like engineering acceleration rather than methodological contribution. | Strong benchmark and practical appendix; possible standalone systems paper. |

## Recommended First Paper

Title direction:

**The Latency-Profit Frontier of Real-Time Stochastic Freight Bid Evaluation**

Alternative titles:

- **FreightBidBench: A Public-Calibrated Benchmark for Real-Time Truckload Bid Evaluation**
- **Selective Stochastic Evaluation for Real-Time Truckload Bid Acceptance**
- **Millisecond Truckload Bid Evaluation with Neural Surrogates for Approximate Dynamic Programming**
- **Fast Stochastic Bid Acceptance in Freight Networks via Offline Value Distillation**
- **Retaining ADP-Quality Decisions at Real-Time Latency in Dynamic Truckload Networks**

The most defensible first paper, given no private data, is a benchmark + methods paper. The primary method should be a cascaded selective evaluator, with neural surrogates and GPU-parallel rollouts as core components.

The central method:

1. Build a public-calibrated stochastic freight-network simulator.
2. Use a high-fidelity ADP or Monte Carlo rollout policy as the slow teacher.
3. Generate many offline states and teacher decisions.
4. Train a fast student model to predict bid value, accept/reject decisions, or marginal value of capacity.
5. Use a cascade that escalates only ambiguous or high-value decisions to expensive stochastic evaluation.
6. Compare speed and simulated profit against the teacher and simpler baselines.

This frames the work as **value distillation for operations research**, not merely generic deep learning.

It also frames the empirical artifact as a reproducible benchmark, which is important because no private tender-level data is available.

## Decision Setting

Use a simplified truckload spot-market setting:

- Freight market is divided into regions or lanes.
- Loads arrive stochastically over time.
- Each load has origin, destination, pickup time, delivery time, price, and service requirements.
- Trucks have current location, availability time, driver or equipment constraints, and possibly home-region preferences.
- The decision is whether to accept, reject, or price a tender.
- The objective is expected profit over a planning horizon.

For v1, use accept/reject bid evaluation rather than full dispatch optimization. Pricing can be introduced later by converting model value into a minimum acceptable price.

A useful value decomposition:

```text
accept load if:

  load_price - operating_cost
  + future_value(destination, delivery_time, remaining_capacity)
  - future_value(origin, current_time, current_capacity)
  >= threshold
```

The slow model estimates the future value terms with rollouts or ADP. The fast model learns to approximate the resulting decision or value difference.

## Public Data Calibration Strategy

The no-private-data constraint changes the contribution. We should not present the study as a validation on real carrier tenders. Instead, we should present a **public-calibrated synthetic benchmark** where the stochastic structure is transparent, reproducible, and stress-tested.

### Source 1: Freight Analysis Framework

Use BTS Freight Analysis Framework data to calibrate the national freight-flow backbone.

What FAF can support:

- Origin-destination flow intensity.
- Commodity mix.
- Mode filtering, especially truck flows.
- Region-level and state-level freight imbalance.
- Tonnage, value, and ton-mile scale.
- Forecast and historical variants for stress testing.

Recommended use:

- Start with FAF region-level truck flows because they are simpler and official.
- Use state-level flows only if FAF regions are too coarse for the benchmark narrative.
- Treat county-level FAF products as optional later detail, because they are experimental and more complex.

Source notes:

- BTS FAF page: `https://www.bts.gov/faf`
- Latest verified version during planning: FAF5.7.1.
- FAF includes regional and state CSV downloads, plus experimental county-level estimates.

### Source 2: USDA AMS Specialty Crops Truck Rates

Use USDA AMS Specialty Crops National Truck Rate Report data to calibrate a refrigerated truckload case study.

What USDA AMS can support:

- Open spot-market refrigerated truck rates.
- Origin shipping area to destination market rate ranges.
- Weekly market snapshots.
- Truck availability categories such as surplus, adequate, shortage, and related gradations.
- A plausible narrow domain: specialty-crop refrigerated truckload.

Recommended use:

- Make the first public-calibrated scenario a **reefer specialty-crop truckload benchmark**.
- Use USDA rates to fit lane-level rate distributions for lanes that appear in the reports.
- Use USDA truck availability categories to stress-test capacity scarcity.
- Use FAF to fill broader OD flow structure around the USDA-observed lane subset.

Source notes:

- USDA AMS Specialty Crops page: `https://www.ams.usda.gov/market-news/fruits-vegetables`
- USDA My Market News report: SC National Truck Rate Report, slug/report `FVWTRK`, report id `2375`.
- My Market News API examples are available on the report page.

### Calibration Principles

The simulator should be honest about what public data can and cannot provide.

Can claim:

- Public-data-calibrated OD intensity.
- Public-data-calibrated rate and availability patterns for a refrigerated subset.
- Synthetic tender streams that preserve observable public marginals.
- Controlled opportunity-cost phenomena for method evaluation.

Cannot claim:

- Exact replication of a carrier's load board.
- Real accept/reject decisions.
- Real carrier fleet positions.
- Real contract commitments or private bid histories.

The language should be:

> We calibrate synthetic stochastic tender streams to public freight-flow and spot-rate marginals, then use the benchmark to evaluate real-time decision architectures under controlled but freight-plausible conditions.

## FreightBidBench Design

FreightBidBench should be the named benchmark artifact.

Core entities:

- Regions: FAF zones, states, or a selected subset mapped to USDA shipping and receiving markets.
- Loads: origin, destination, commodity group, equipment type, pickup time, delivery time, price, distance, and service duration.
- Trucks: current region, available time, equipment type, operating cost, and optional home-region preference.
- Market state: regional demand forecast, truck availability signal, lane imbalance, and recent price trend.
- Event stream: stochastic load arrivals over a rolling horizon.

Core dynamics:

1. At each decision epoch, one or more candidate loads arrive.
2. The policy accepts, rejects, or assigns a minimum acceptable price.
3. Accepted loads update truck location and availability.
4. Rejected loads disappear.
5. Future load arrivals are sampled from calibrated OD and time distributions.
6. Profit accumulates as load revenue minus operating and repositioning cost.

Required freight phenomena:

- Headhaul/backhaul imbalance.
- Trap destinations with attractive inbound rates but weak outbound demand.
- Repositioning loads with low immediate margin but high future value.
- Seasonal or weekly demand shifts.
- Regional truck shortages and surpluses.
- Sparse lanes where generalization matters.

Benchmark outputs:

- Closed-loop profit.
- Profit retention versus rollout teacher.
- Decision latency, including p50 and p95.
- Empty miles.
- Loaded miles.
- Truck utilization.
- Rejection rate.
- Regret by load type and market condition.

## Cascaded Selective Evaluator

The strongest practical method is not a single model. It is a cascade that spends computation only when the decision deserves it.

Decision stages:

1. **Cheap rule stage**
   - Accept loads that are clearly profitable and land in strong markets.
   - Reject loads that are clearly unprofitable and land in weak markets.
   - Forward uncertain loads to the next stage.

2. **Fast value-surrogate stage**
   - Estimate incremental value of acceptance with a linear/tree model or MLP.
   - Accept or reject when the estimated value is far from zero.
   - Forward near-threshold or high-stakes decisions to rollout.

3. **Stochastic rollout stage**
   - Run CPU or GPU-vectorized rollouts only for ambiguous/high-value cases.
   - Use the rollout result as the final decision.
   - Log the decision for future teacher-label generation.

Escalation criteria:

- Absolute predicted value is near zero.
- Offered revenue is unusually high.
- Destination is a known trap or sparse lane.
- Truck availability is scarce.
- Surrogate uncertainty is high.
- The decision would consume a strategically valuable truck.

Why this is a better v1 method:

- It preserves the practical appeal of ADP/rollout where it matters.
- It avoids the brittle claim that a neural model should replace stochastic evaluation everywhere.
- It naturally produces a latency-profit frontier by changing escalation thresholds.
- It is defensible with no private data because the core claim is architectural and benchmarked under controlled scenarios.

## Baselines

The paper needs baselines that make the trade-off curve credible.

Slow high-quality baselines:

- ADP-style value function approximation with discretized regions and time buckets.
- Monte Carlo rollout using a base policy.
- Optional solver-backed dispatch subproblem if needed for a stronger oracle.

Fast operational baselines:

- Myopic margin rule: accept if immediate revenue minus cost is positive.
- Lane-average rule: accept if margin plus historical destination score is above threshold.
- Linear or gradient-boosted surrogate using hand-built features.
- Neural surrogate model.
- Optional GNN surrogate.
- Optional GPU-vectorized rollout.
- Cascaded selective evaluator.

The key comparison is not only neural model versus myopic model. It is neural model versus slow stochastic evaluator on both quality and latency.

## Metrics

Primary metrics:

- Online decision latency per load.
- Total simulated profit over the horizon.
- Profit retention versus slow teacher:

```text
profit_retention = fast_policy_profit / teacher_policy_profit
```

- Regret versus teacher:

```text
regret = teacher_policy_profit - fast_policy_profit
```

- Accept/reject agreement with teacher.

Secondary metrics:

- Calibration error for predicted value.
- Robustness under demand shocks.
- Robustness under capacity shocks.
- Performance by market density: dense lanes versus sparse lanes.
- Tail outcomes: worst decile profit, service failures, empty miles.

The signature result should be a plot:

```text
x-axis: online latency
y-axis: simulated profit retention
```

The target result is a curve where the surrogate is near the teacher on profit but much closer to myopic rules on latency.

## Benchmark Test Scenarios

These tests define whether FreightBidBench is credible enough to support the paper.

### Calibration Scenarios

- FAF-derived OD flow intensities are preserved in the synthetic load stream.
- Chosen commodity/equipment shares match the selected public marginals.
- USDA-observed reefer lane rates are reproduced within transparent tolerances.
- USDA truck availability categories map to capacity-scarcity parameters.
- Unobserved lanes use documented fallback generation rules.

### Opportunity-Cost Scenarios

- A high-margin load into a weak outbound market should sometimes be rejected.
- A low-margin repositioning load into a strong outbound market should sometimes be accepted.
- A scarce truck in a strong market should have a higher opportunity cost than an idle truck in a weak market.
- A market shock should change the learned or computed bid threshold.
- Sparse lanes should expose whether GNN or graph features improve generalization.

### Policy Comparison Scenarios

- Every policy sees identical random demand seeds.
- Every policy starts from identical truck positions.
- Runtime is measured at the actual decision point, excluding offline training.
- Teacher quality is reported separately from teacher latency.
- The cascade reports the fraction of decisions handled by each stage.

### Robustness Scenarios

- Demand shock: increase or decrease selected regional demand.
- Price shock: widen rate noise and market imbalance premiums.
- Capacity shock: reduce truck availability in a subset of markets.
- Geography shift: hold out a region or lane family during surrogate training.
- Seasonality shift: train on one seasonal pattern and evaluate on another.

### Ablations

- Remove public calibration and use random OD demand.
- Remove destination/future-value features.
- Remove cascade escalation and use the surrogate alone.
- Replace MLP with linear/tree model.
- Replace GPU rollout with CPU rollout.
- Remove scarce-capacity signals.

## Experimental Design

### Simulator

Create a synthetic but freight-plausible stochastic network:

- 25-100 regions, starting from FAF regions or a selected state/market subset.
- Directed lane demand between regions.
- Time buckets across a 3-7 day horizon.
- Demand generated by region-level and lane-level stochastic processes calibrated to public OD marginals.
- Prices generated from distance, market imbalance, public truck-rate signals where available, and noise.
- Operating cost based on distance and time.
- Trucks initialized across regions with availability times.

The simulator must be simple enough to explain but rich enough that myopic decisions fail.

Important phenomenon to include:

- Some destinations are traps: profitable immediate loads move capacity into weak future markets.
- Some weak immediate loads are good repositioning moves.
- Demand imbalance changes by day and region.
- Capacity scarcity creates opportunity cost.

Public-calibration checks:

- Synthetic OD volumes should preserve FAF-derived relative flow intensities.
- Synthetic commodity/equipment mix should preserve the chosen public marginals.
- Reefer lane rates should match USDA-observed rate ranges where USDA data is used.
- Availability shocks should reflect USDA availability categories in the reefer case.
- Unobserved lanes should be generated by transparent fallback rules based on distance, imbalance, and commodity/equipment type.

### Teacher

Use a high-fidelity stochastic evaluator:

- For each candidate load, simulate future demand scenarios.
- Evaluate accept versus reject using a base dispatch policy.
- Average future profit across scenarios.
- Use the difference as the teacher label.

Teacher labels can be:

- Binary accept/reject decision.
- Continuous incremental value of accepting the load.
- Minimum acceptable price.

The best first label is continuous incremental value, because it supports both accept/reject and pricing.

### Student Models

Start with three student tiers:

- Linear or tree model with engineered features.
- Multilayer perceptron surrogate.
- GNN surrogate over the freight-region graph.

The MLP should be the primary first-paper model. The GNN can be included only if it clearly improves spatial generalization.

Candidate input features:

- Load origin and destination.
- Pickup and delivery time bucket.
- Loaded miles and travel time.
- Offered price and expected cost.
- Current truck distribution by region and time bucket.
- Recent or forecast demand by region.
- Region imbalance features.
- Destination future-demand score.

Candidate outputs:

- Incremental value of accept versus reject.
- Probability teacher accepts.
- Minimum acceptable price.

### Evaluation

Evaluate policies in closed-loop simulation, not only on held-out prediction accuracy.

For each policy:

1. Generate the same stream of stochastic load arrivals.
2. Let the policy make online decisions.
3. Update truck states and network state.
4. Track realized profit, empty miles, utilization, and latency.

Prediction accuracy is secondary. A model can approximate teacher labels well but still make bad compounding decisions.

## Literature Review Map

### 1. ADP and dynamic freight/fleet management

This is the intellectual home base for the paper.

**Simão, Day, George, Gifford, Nienow, and Powell, "An Approximate Dynamic Programming Algorithm for Large-Scale Fleet Management: A Case Application," Transportation Science, 2009.**

- Models the movement of more than 6,000 drivers for Schneider National.
- Uses approximate dynamic programming to handle high-dimensional fleet state.
- Estimates marginal driver values across many driver types and locations.
- Shows that ADP can capture realistic truckload fleet operations, but the focus is operational fidelity and value estimation, not millisecond online bid evaluation.
- Relevance: this is the baseline tradition we are trying to compress or accelerate.

**Kim, Mahmassani, and Jaillet, "Dynamic Truckload Routing, Scheduling, and Load Acceptance for Large Fleet Operation with Priority Demands," Transportation Research Record, 2004.**

- Directly studies dynamic load acceptance and rejection for truckload routing with time windows.
- Frames the acceptance decision as an online decision that must be made when demand arrives or shortly after.
- Uses system-state information to approximate future ability to serve priority demand.
- Relevance: this is very close to the decision setting, but it predates modern neural surrogates and GPU/vectorized simulation.

**Kim, Mahmassani, and Jaillet, "Dynamic Truckload Truck Routing and Scheduling in Oversaturated Demand Situations," Transportation Research Record, 2002.**

- Discusses the relationship between computation time and solution quality in dynamic online truckload routing.
- Explicitly treats available time between successive demand requests as a computational resource.
- Relevance: supports the paper's focus on latency as a first-class metric, not only profit or optimality.

**Ulmer, Goodson, Mattfeld, and Hennig, "Offline-Online Approximate Dynamic Programming for Dynamic Vehicle Routing with Stochastic Requests," Transportation Science, 2019.**

- Combines offline value function approximation with online rollout.
- Targets real-time dynamic vehicle routing with stochastic requests.
- Shows that hybrid offline-online ADP can improve quality while reducing online computational burden.
- Relevance: very important adjacent work. Our paper must distinguish itself by focusing on truckload bid/load acceptance, explicit latency-profit frontier measurement, and learned surrogates that can replace most online rollout work.

**Ulmer and Thomas, "Meso-parametric Value Function Approximation for Dynamic Customer Acceptances in Delivery Routing," European Journal of Operational Research, 2020.**

- Studies stochastic dynamic customer acceptance.
- Combines parametric and non-parametric VFAs.
- Shows that VFA design matters for dynamic acceptance decisions.
- Relevance: supports the accept/reject framing and provides a strong comparison point for VFA-style methods.

Takeaway:

The freight/vehicle-routing literature already recognizes online load acceptance and downstream opportunity cost. The open space is not "use ADP for freight"; it is **make ADP-quality stochastic bid evaluation fast enough for online freight markets, and quantify the speed-quality trade-off**.

### 2. Neural value functions and surrogate optimization

This is the methodological bridge from OR to fast inference.

**van Heeswijk and La Poutré, "Approximate Dynamic Programming with Neural Networks in Linear Discrete Action Spaces," 2019.**

- Embeds neural-network VFAs into linear decision problems.
- Motivated by high-dimensional OR problems where hand-designed polynomial VFAs are restrictive.
- Shows neural VFAs can outperform polynomial VFAs on a transportation proof of concept.
- Relevance: validates neural VFAs in an OR/transportation context, but does not focus on truckload spot-market bid latency.

**Dumouchelle, Patel, Khalil, and Bodur, "Neur2SP: Neural Two-Stage Stochastic Programming," NeurIPS, 2022.**

- Approximates the expected second-stage value function in two-stage stochastic programs with a neural network.
- Motivated by the cost of evaluating expected recourse functions, especially with MIP/NLP second stages.
- Reports high-quality solutions with much faster solve times than generic extensive-form approaches.
- Relevance: very close in spirit. It supports the "replace expensive stochastic lookahead with a learned value surrogate" framing. Our distinction is sequential freight bid evaluation and closed-loop fleet simulation rather than generic two-stage stochastic benchmarks.

**Recent extensions of neural stochastic-programming surrogates.**

- Quantile neural-network approaches approximate second-stage cost distributions, not just expected values, enabling risk-aware objectives such as CVaR.
- Input-convex neural network approaches try to make neural recourse surrogates easier to embed in optimization models.
- Relevance: if the freight paper evolves beyond expected profit, these papers suggest a path toward risk-aware bid evaluation.

Takeaway:

Neural surrogates for stochastic value functions are now legitimate. The paper should not claim the surrogate idea is new. The novelty should be the **freight-specific online decision setting, closed-loop evaluation, and latency-profit frontier**.

### 3. Learned routing heuristics and reinforcement learning

This area shows that trained models can make routing decisions quickly after offline training, but it is not exactly our problem.

**Nazari, Oroojlooy, Snyder, and Takáč, "Deep Reinforcement Learning for Solving the Vehicle Routing Problem," NeurIPS, 2018.**

- Trains a policy model for VRP-like problems.
- After training, the model produces routes in real time without retraining per instance.
- Relevance: supports the feasibility of offline training plus fast online routing decisions, but focuses on constructing routes rather than stochastic truckload bid acceptance.

**Kool, van Hoof, and Welling, "Attention, Learn to Solve Routing Problems!" ICLR, 2019.**

- Uses an attention model trained with REINFORCE and rollout baselines.
- Learns strong heuristics for TSP, VRP, orienteering, and related routing problems.
- Relevance: useful architecture inspiration for graph/attention student models, but reviewers may view it as a different static-routing literature unless we connect it carefully to online freight decisions.

Takeaway:

Learned routing papers are useful for architecture and inference-speed arguments, but the paper should avoid drifting into generic neural combinatorial optimization. Our target decision is bid/load acceptance under stochastic future freight, not route construction alone.

### 4. GNNs for transportation and spatial propagation

This supports the graph path, especially for representing freight markets as spatially connected nodes.

**Derrow-Pinion et al., "ETA Prediction with Graph Neural Networks in Google Maps," CIKM, 2021.**

- Uses GNNs for travel-time prediction in road networks at Google Maps scale.
- Models topological and spatiotemporal interactions in transportation networks.
- Reports production deployment and large improvements in negative ETA outcomes in some cities.
- Relevance: strong evidence that GNNs can capture transportation network structure in production settings, though it is prediction rather than decision optimization.

**Kool et al. and related graph/attention routing work.**

- Attention and graph-based architectures are effective for learning heuristics over routing instances.
- Relevance: supports using message passing or attention over freight regions, but does not by itself prove value for stochastic freight bid evaluation.

Takeaway:

The GNN angle is plausible but should be an ablation or second paper unless it clearly improves spatial generalization. A reviewer will ask whether simpler lane, region, and imbalance features already capture most of the value.

### 5. GPU/vectorized simulation and differentiable computing tools

This supports the "parallel rollouts" strategy.

**JAX documentation and ecosystem.**

- `jax.jit` compiles array programs with XLA for efficient CPU/GPU/TPU execution.
- `jax.vmap` automatically vectorizes functions over batch axes.
- `jit` and `vmap` compose, which is exactly the pattern needed for many parallel Monte Carlo scenarios.
- Relevance: technical foundation for a GPU rollout teacher and for generating labels faster.

Takeaway:

GPU rollouts may be the most practical way to build the teacher and a strong benchmark. As a standalone paper, however, it risks sounding like implementation acceleration unless paired with a careful stochastic-network formulation and reproducible benchmark.

### 6. Truckload spot-market pricing and procurement

This literature gives the market context, but usually studies pricing, sourcing, auctions, or forecasting rather than downstream fleet opportunity cost.

**Budak, Ustundag, and Guloglu, "A Forecasting Approach for Truckload Spot Market Pricing," Transportation Research Part A, 2017.**

- Uses neural networks and quantile regression for truckload spot-price forecasting.
- Relevance: shows ML has been used for truckload price prediction, but price forecasting is not the same as bid acceptance based on future fleet state.

**Lindsey and Mahmassani, "Measuring Carrier Reservation Prices for Truckload Capacity in the Transportation Spot Market," Transportation Research Record, 2015.**

- Studies carrier reservation prices and spot-market capacity behavior.
- Relevance: useful for later pricing extensions, especially minimum acceptable bid estimation.

**Lindsey and Mahmassani, "Sourcing Truckload Capacity in the Transportation Spot Market," Transportation Research Part A, 2017.**

- Proposes a framework for 3PL brokers using carrier behavior, reservation prices, and bundling to source capacity.
- Relevance: broker-side rather than carrier-side, but supports the idea that spot-market decisions are sequential, uncertain, and search/latency constrained.

**Bid-price optimization and truckload procurement auction papers.**

- Several papers optimize carrier bids or shipper winner determination under uncertainty, including stochastic and robust models.
- Relevance: useful background if the paper moves from accept/reject into bid pricing, but many procurement-auction settings differ from real-time spot tender acceptance.

Takeaway:

Truckload spot-market research exists, including ML price forecasting and auction/procurement optimization. The gap is a **carrier-side real-time stochastic bid evaluator that internalizes future fleet value**.

## Gap Statement From The Literature

The strongest literature-backed gap is:

> Prior truckload and dynamic vehicle-routing work models downstream opportunity cost with ADP, rollout, and VFA methods, while spot-market freight work studies price forecasting, reservation prices, and procurement behavior. Separately, neural stochastic-programming surrogates and learned routing heuristics show that expensive optimization/value calculations can be approximated after offline training. What is missing is a closed-loop study of real-time truckload bid/load acceptance that directly measures the latency-profit frontier between high-fidelity stochastic evaluation and millisecond learned surrogates.

That gap leads to a cleaner contribution:

1. Formulate real-time truckload bid acceptance as a stochastic dynamic decision problem with an explicit latency budget.
2. Build a high-fidelity rollout/ADP teacher and fast neural/GNN/GPU alternatives.
3. Evaluate policies in closed-loop simulation, not just prediction error.
4. Report profit retention, regret, and decision latency on the same frontier.

## Must-Cite Starting Bibliography

- Simão, H. P., Day, J., George, A. P., Gifford, T., Nienow, J., and Powell, W. B. 2009. "An Approximate Dynamic Programming Algorithm for Large-Scale Fleet Management: A Case Application." Transportation Science.
- Kim, Y., Mahmassani, H. S., and Jaillet, P. 2004. "Dynamic Truckload Routing, Scheduling, and Load Acceptance for Large Fleet Operation with Priority Demands." Transportation Research Record.
- Kim, Y., Mahmassani, H. S., and Jaillet, P. 2002. "Dynamic Truckload Truck Routing and Scheduling in Oversaturated Demand Situations." Transportation Research Record.
- Ulmer, M. W., Goodson, J. C., Mattfeld, D. C., and Hennig, M. 2019. "Offline-Online Approximate Dynamic Programming for Dynamic Vehicle Routing with Stochastic Requests." Transportation Science.
- Ulmer, M. W., and Thomas, B. W. 2020. "Meso-parametric Value Function Approximation for Dynamic Customer Acceptances in Delivery Routing." European Journal of Operational Research.
- van Heeswijk, W., and La Poutré, H. 2019. "Approximate Dynamic Programming with Neural Networks in Linear Discrete Action Spaces."
- Dumouchelle, J., Patel, R. M., Khalil, E. B., and Bodur, M. 2022. "Neur2SP: Neural Two-Stage Stochastic Programming." NeurIPS.
- Nazari, M., Oroojlooy, A., Snyder, L. V., and Takáč, M. 2018. "Deep Reinforcement Learning for Solving the Vehicle Routing Problem." NeurIPS.
- Kool, W., van Hoof, H., and Welling, M. 2019. "Attention, Learn to Solve Routing Problems!" ICLR.
- Derrow-Pinion, A., She, J., Wong, D., Lange, O., Hester, T., Perez, L., Nunkesser, M., Lee, S., Guo, X., Wiltshire, B., et al. 2021. "ETA Prediction with Graph Neural Networks in Google Maps." CIKM.
- Budak, A., Ustundag, A., and Guloglu, B. 2017. "A Forecasting Approach for Truckload Spot Market Pricing." Transportation Research Part A.
- Lindsey, C., and Mahmassani, H. S. 2015. "Measuring Carrier Reservation Prices for Truckload Capacity in the Transportation Spot Market." Transportation Research Record.
- Lindsey, C., and Mahmassani, H. S. 2017. "Sourcing Truckload Capacity in the Transportation Spot Market: A Framework for Third Party Providers." Transportation Research Part A.

## Public Data Sources To Cite

- Bureau of Transportation Statistics. "Freight Analysis Framework." Use for OD freight flows, commodity type, mode, tonnage, value, and ton-mile calibration.
- Bureau of Transportation Statistics. "Freight Analysis Framework Version 5 Experimental County-Level Estimates." Use only if county-level detail becomes necessary; clearly label it experimental.
- USDA Agricultural Marketing Service. "Specialty Crops Market News." Use for public access to specialty-crop market data and report datasets.
- USDA My Market News. "SC National Truck Rate Report (PDF) (FVWTRK), report id 2375." Use for refrigerated truckload spot rates and truck availability categories.

## Research Position Analysis

### Bottom-line assessment

The idea is viable, but only if the paper is framed narrowly and defensibly.

A weak version of the paper would say:

> We use neural networks to speed up ADP for freight.

That will be attacked immediately because neural VFAs, RL for vehicle routing, offline-online ADP, and stochastic-programming surrogates already exist.

A strong version says:

> We study real-time truckload bid acceptance as a latency-constrained stochastic decision problem and measure the profit retained by several fast approximations relative to a high-fidelity rollout or ADP teacher.

That positioning has room because it connects four literatures that are usually separate:

- Truckload load acceptance and spot-market freight decisions.
- ADP/VFA for dynamic fleet and vehicle routing.
- Neural surrogates for expensive stochastic value functions.
- Hardware/vectorization for fast Monte Carlo evaluation.

The paper should be sold as a **benchmark and methodology for real-time stochastic bid evaluation**, not as a generic new neural optimizer.

### What is already well covered

These areas are not enough for novelty by themselves:

- ADP/VFA for large-scale fleet management.
- Dynamic customer or load acceptance with stochastic future requests.
- Offline-online ADP for dynamic vehicle routing.
- Neural value function approximation.
- Learned heuristics for VRP.
- GNNs for transportation prediction and some stochastic routing/planning problems.
- Neural surrogates for stochastic-programming recourse functions.

The paper must acknowledge this up front. The novelty is in the combination, decision setting, and evaluation metric.

### What still looks underexplored

The most promising gap is **carrier-side real-time truckload bid/load acceptance with downstream fleet opportunity cost**.

The closest literatures either miss the carrier-side spot-market setting or miss the real-time surrogate comparison:

- Truckload ADP papers model fleet operations, but do not center online bid-evaluation latency.
- Dynamic vehicle routing papers study acceptance and stochastic requests, but usually in parcel, technician, same-day delivery, or generic DVRP settings rather than truckload spot tenders.
- Spot-market freight papers study price forecasting, reservation prices, auctions, or sourcing, but often do not model future fleet-state opportunity cost.
- Neural stochastic-programming papers approximate expensive value functions, but usually in static/two-stage benchmark settings rather than closed-loop freight simulation.
- GNN transportation papers are strong on prediction and representation, but not necessarily on freight bid decision quality.

That means the best contribution is not "new algorithm in isolation." It is a **decision benchmark plus empirical frontier**.

### Recommended paper claim

Use this as the north-star claim:

> In stochastic truckload bid acceptance, neural value surrogates trained from offline rollout labels can retain most of the closed-loop profit of high-fidelity stochastic evaluation while reducing online decision latency by orders of magnitude.

This is specific enough to test.

The supporting claims:

- Myopic margin rules are fast but miss downstream opportunity cost.
- Rollout/ADP teachers capture downstream opportunity cost but are too slow online.
- A learned value surrogate can approximate the marginal downstream value of accepting a load.
- Closed-loop profit retention is a better success metric than static prediction accuracy.
- The useful output is a latency-profit frontier, not a single "best" model.

### Method ranking

1. **Neural surrogate VFA: best primary method**
   - Highest fit to the paper thesis.
   - Clean offline-training versus online-inference story.
   - Easy to compare against linear/tree surrogates.
   - Natural output is incremental value or minimum acceptable price.

2. **GPU-parallel rollout: best teacher accelerator and benchmark**
   - Useful even if the paper is about surrogates.
   - Makes label generation tractable.
   - Provides a strong "what if we just parallelize?" comparator.
   - Helps avoid straw-manning slow CPU rollout.

3. **GNN: optional model, not the first dependency**
   - Worth testing if spatial generalization matters.
   - Stronger if the experiment includes held-out regions, sparse lanes, or shifted regional demand.
   - Risky as the main method because reviewers may ask why simpler region/lane features are insufficient.

The first paper should implement all three only if scope allows. Otherwise: MLP surrogate plus linear/tree baselines plus CPU/GPU rollout teacher is enough.

### Reviewer attack points

Expect these objections:

1. **"This is just imitation learning."**
   - Response: the paper evaluates closed-loop profit, regret, and latency, not only teacher agreement.

2. **"The teacher is not optimal."**
   - Response: call it a high-fidelity stochastic evaluator; include exact small-instance dynamic programming or exhaustive rollout checks where possible.

3. **"Synthetic data is not realistic."**
   - Response: make the simulator transparent, include sensitivity sweeps, and reproduce known freight phenomena such as headhaul/backhaul imbalance, trap destinations, repositioning value, and demand shocks.

4. **"Neural VFAs already exist."**
   - Response: agree, then emphasize the freight bid setting, latency budget, and latency-profit frontier.

5. **"GNNs are unnecessary."**
   - Response: include GNN only as an ablation; the main thesis does not depend on GNN superiority.

6. **"GPU rollout solves the latency problem without learning."**
   - Response: include GPU rollout in the frontier. If GPU rollout is fast and accurate enough, that is a valid outcome and may become the stronger practical contribution.

### What experiment would make the paper convincing

The first convincing experiment should be small but surgical:

- 50 freight regions.
- 200-1,000 trucks.
- 3-7 day rolling horizon.
- Stochastic lane demand with region imbalance.
- Load prices depend on distance, lane imbalance, and random market noise.
- Some markets are intentionally high-revenue traps with poor outbound demand.
- Some low-margin loads are valuable repositioning moves.

Run policies in closed-loop simulation:

- Myopic margin rule.
- Lane-score heuristic.
- Bid-price opportunity-cost heuristic.
- Linear or gradient-boosted value surrogate.
- MLP value surrogate.
- Optional GNN value surrogate.
- CPU rollout teacher.
- GPU-vectorized rollout benchmark.
- Cascaded selective evaluator.

Report:

- Profit retention against teacher.
- Mean and p95 decision latency.
- Regret per accepted load.
- Empty miles and utilization.
- Robustness under demand shocks.
- OOD transfer to shifted market imbalance.

The key figure should show that the MLP sits near the teacher in profit but near heuristics in latency.

The stronger v1 figure should show the cascade tracing the best frontier: lower latency than always-rollout and higher profit than always-surrogate or myopic rules.

### Minimum publishable contribution

The minimum strong paper needs:

- A formal MDP-style formulation of truckload bid/load acceptance.
- A reproducible public-calibrated synthetic freight simulator with opportunity-cost structure.
- A high-fidelity stochastic teacher.
- At least two fast surrogate baselines, one simple and one neural.
- A cascaded selective evaluator.
- Closed-loop evaluation.
- Latency measurement.
- A clear gap discussion versus ADP/VFA, DVRP, neural routing, and stochastic-programming surrogate papers.

Do not overbuild a full dispatch system for v1. The paper lives or dies on the bid-evaluation experiment.

### Recommended target venue angle

Transportation/OR venue angle:

- Emphasize stochastic dynamic decision making, VFA, closed-loop simulation, and managerial insight.
- Stronger venues will expect careful baselines and sensitivity analysis.

Applied ML/workshop angle:

- Emphasize value distillation, fast inference, and decision-focused evaluation.
- Needs a clean benchmark and possibly open-source simulator.

Industry/practitioner angle:

- Emphasize response-time budgets, bid acceptance, profit retention, and deployment architecture.
- Needs credible latency numbers and freight-realistic examples.

Best initial target:

- Write it like a Transportation Science / Transportation Research Part E style paper.
- Keep an applied ML workshop version as a shorter derivative if the simulator and benchmark become clean.

### Go/no-go criteria

Proceed if early experiments show at least one of these:

- Neural surrogate keeps at least 95% of teacher profit at less than 1% of teacher latency.
- GPU rollout gives near-teacher quality within operational latency, creating a strong acceleration paper.
- Cascaded evaluation dominates the single-method frontier by using rollout on only a small fraction of decisions.
- GNN materially improves transfer to new market conditions over MLP/tree models.

Stop or pivot if:

- Myopic and lane-score heuristics already achieve nearly the same profit as rollout.
- Teacher labels are too noisy for any surrogate to learn useful values.
- The simulator cannot generate opportunity-cost cases that are both realistic and explainable.
- Latency improvements disappear once closed-loop policy evaluation is measured honestly.
- Public calibration is too weak to support even a benchmark claim; in that case, pivot to a pure algorithmic/synthetic paper with no realism claim.

### Immediate analysis tasks

1. Build a source spreadsheet with columns: paper, domain, method, decision type, stochasticity, online latency treatment, evaluation metric, relevance, gap.
2. Build a public-data spreadsheet with columns: source, geography, commodity/equipment coverage, rate availability, flow availability, time granularity, use in simulator.
3. Separate must-cite papers from optional background papers.
4. Draft a one-page "Related Work and Gap" section from the research position above.
5. Define the simulator phenomena required to make myopic policies fail.
6. Decide the first empirical claim before implementing models:

```text
Can a fast surrogate preserve downstream opportunity-cost decisions?
```

If the answer is yes, the paper has a clear lane.

## Novelty Angle

The paper should not claim that neural value function approximation is new.

The stronger novelty claim:

- Real-time freight bid evaluation is constrained by online latency, not just optimality.
- The paper measures a latency-profit frontier for stochastic fleet decisions.
- It distills a slow stochastic evaluator into a fast online policy.
- It evaluates the model in closed-loop freight simulation rather than only static prediction.
- It compares neural surrogates, graph spatial models, and GPU rollouts under the same operational budget.

Possible phrasing:

> We study stochastic truckload bid evaluation as a real-time approximation problem. Rather than optimizing only for expected profit, we quantify the trade-off between decision quality and online latency, and show that offline value distillation can retain most of the value of rollout-based evaluation at operationally viable response times.

## Risks And How To Handle Them

### Risk: Synthetic simulator is not credible

Mitigation:

- Keep the simulator transparent.
- Include sensitivity analysis across demand volatility, network imbalance, and fleet size.
- If real data becomes available, use it only after the synthetic benchmark works.

### Risk: Neural surrogate is just imitation learning

Mitigation:

- Emphasize the OR setting, value labels, and operational latency constraint.
- Compare against non-neural surrogates.
- Show closed-loop profit, not only imitation accuracy.

### Risk: GNN adds complexity without payoff

Mitigation:

- Treat GNN as optional.
- Include it only if it improves out-of-distribution transfer to new regions, sparse lanes, or shifted demand.

### Risk: GPU rollout is enough by itself

Mitigation:

- Use GPU rollout as a strong benchmark.
- If GPU rollout is fast enough and high quality, pivot the paper toward accelerated stochastic simulation rather than neural surrogates.

### Risk: Teacher is not truly optimal

Mitigation:

- Call it a high-fidelity teacher, not an oracle, unless an exact small-instance optimum is available.
- Include small instances where exact dynamic programming or exhaustive evaluation is possible.

## Paper Outline

1. Introduction
   - Real-time freight decisions require stochastic lookahead under strict latency.
   - Existing ADP and rollout methods are high quality but expensive online.
   - Contribution: latency-profit frontier and offline value distillation.

2. Related Work
   - ADP for fleet management.
   - Dynamic load acceptance and customer acceptance.
   - Neural value function approximation.
   - GNNs for transportation networks.
   - GPU/vectorized simulation.

3. Problem Formulation
   - Dynamic truckload bid acceptance.
   - State, action, stochastic arrivals, transition, reward.
   - Online latency budget.

4. Methods
   - Slow stochastic teacher.
   - Surrogate student models.
   - Optional GNN spatial model.
   - Optional GPU rollout benchmark.

5. Experiments
   - Synthetic freight network.
   - Baselines.
   - Closed-loop evaluation.
   - Latency measurement.

6. Results
   - Profit versus latency frontier.
   - Policy regret.
   - Robustness to demand and capacity shocks.
   - Ablations.

7. Discussion
   - When fast surrogates work.
   - When lookahead remains necessary.
   - Practical deployment implications.

## Immediate Next Steps

1. Download and inspect FAF regional/state truck-flow data.
2. Download and inspect USDA AMS Specialty Crops National Truck Rate Report data.
3. Define the smallest public-calibrated reefer truckload scenario that creates real opportunity-cost decisions.
4. Implement myopic, lane-score, bid-price, and rollout teacher policies.
5. Generate teacher labels for a large offline state set.
6. Train a first MLP surrogate.
7. Implement the cascaded evaluator with tunable escalation thresholds.
8. Run closed-loop evaluation across 100-1,000 random demand seeds.
9. Produce the first latency-profit frontier plot.
10. Decide whether the first paper is strongest as FreightBidBench, selective stochastic evaluation, or neural value distillation.

## Open Questions

- Is the target venue operations research, transportation science, applied ML, or a systems-oriented workshop?
- Should the decision be framed as accept/reject first, or as minimum profitable bid price?
- What latency budget is most realistic for the intended industry setting: 10 ms, 100 ms, 1 second, or 5 seconds?
- Should the paper optimize for academic novelty, startup defensibility, or practitioner credibility?
- Should the benchmark focus only on reefer specialty-crop lanes first, or use reefer lanes as a calibrated subset inside a broader FAF truckload network?
- Should FreightBidBench be released as an open-source simulator alongside the paper?

## Current Best Bet

Start with the public-calibrated benchmark + cascaded evaluator paper.

Use FAF for OD freight-flow structure and USDA AMS for the refrigerated spot-rate/availability case. Use GPU-parallel rollouts to make the teacher faster and to create a strong benchmark, but keep the primary story focused on selective stochastic evaluation under an explicit latency budget.

The paper succeeds if it can honestly show something like:

```text
Policy                     Latency       Profit retention
Slow rollout teacher        30-600 s      100%
GPU rollout                 1-5 s         99-100%
Neural surrogate            5-50 ms       95-99%
Cascaded evaluator          50 ms-3 s     97-100%
Myopic margin rule          <1 ms         70-90%
Lane-score heuristic        <1 ms         80-93%
```

The exact numbers do not matter yet. The structure of the result matters: a rigorous trade-off curve where the cascade occupies the best practical middle ground, and the public-calibrated benchmark makes the comparison reproducible.
