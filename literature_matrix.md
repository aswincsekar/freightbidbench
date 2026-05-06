# Literature Matrix

## Purpose

This file turns the literature review into a working matrix for paper positioning. The goal is to show exactly what each area contributes and what gap FreightBidBench can own.

## Core Literature Matrix

| Area | Representative Work | What It Already Solves | What It Does Not Solve For Us | How We Use It |
| --- | --- | --- | --- | --- |
| Large-scale truckload ADP | Simão, Day, George, Gifford, Nienow, Powell, 2009 | Shows ADP can model realistic large-scale truckload fleet value and marginal driver values | Does not center millisecond online bid evaluation or public-calibrated benchmark design | Anchor for the slow high-quality teacher tradition |
| Dynamic truckload load acceptance | Kim, Mahmassani, Jaillet, 2002/2004 | Frames truckload load acceptance as online, time-constrained, and state-dependent | Predates neural surrogates, GPU rollouts, and modern benchmark framing | Anchor for the decision setting |
| Offline-online ADP for dynamic routing | Ulmer, Goodson, Mattfeld, Hennig, 2019 | Combines offline VFA and online rollout for stochastic requests | Not truckload spot tender bidding; not focused on public data or latency-profit frontier | Closest methodological predecessor |
| Dynamic customer acceptance VFAs | Ulmer and Thomas, 2020 | Studies acceptance decisions with value approximations | Delivery-routing context rather than truckload bid evaluation | Supports accept/reject and opportunity-cost formulation |
| Neural VFA in ADP | van Heeswijk and La Poutré, 2019 | Shows neural VFAs can help OR/transportation ADP problems | Neural approximation alone is not novel enough | Supports the surrogate model baseline |
| Neural stochastic-programming surrogates | Dumouchelle, Patel, Khalil, Bodur, 2022 | Replaces expensive stochastic recourse evaluation with neural approximations | Usually static/two-stage, not closed-loop truckload bidding | Supports value-distillation framing |
| Learned VRP heuristics | Nazari et al., 2018; Kool et al., 2019 | Demonstrates fast inference after offline training for routing-like problems | Focuses on route construction rather than stochastic tender acceptance | Architecture background only |
| GNN transportation prediction | Derrow-Pinion et al., 2021 | Shows graph models capture transport network structure at scale | Prediction, not stochastic bid policy evaluation | Justifies optional graph features/GNN ablation |
| Truckload spot-market pricing | Budak et al., 2017; Lindsey and Mahmassani, 2015/2017 | Studies rates, reservation prices, and spot-market sourcing | Often misses carrier-side downstream fleet opportunity cost | Market-context background |
| Public freight-flow data | BTS FAF | Provides public OD, commodity, mode, tonnage/value structure | Not event-level tender data | Calibrates benchmark demand and imbalance |
| Public refrigerated truck rates | USDA AMS FVWTRK | Provides public reefer spot-rate and availability signals | Narrow lane/commodity coverage | Calibrates v1 reefer scenario |

## Positioning Statement

Prior work establishes three pieces separately:

1. Truckload and dynamic-routing decisions need downstream opportunity-cost reasoning.
2. ADP, rollout, and VFA methods can approximate those downstream values.
3. Neural or learned surrogates can replace expensive value calculations in some stochastic optimization settings.

The missing piece:

> A reproducible, public-calibrated benchmark for real-time truckload bid acceptance that compares heuristic, surrogate, rollout, GPU, and cascaded decision architectures on the same latency-profit frontier.

## Reviewer Risk Matrix

| Reviewer Objection | Likely Source | Response |
| --- | --- | --- |
| Neural VFAs already exist | ADP/ML reviewers | Agree; the contribution is benchmarked real-time truckload bid evaluation and closed-loop latency-profit measurement |
| Synthetic data is not real freight | Transportation reviewers | Use public calibration, transparent generator assumptions, sensitivity analysis, and restrained claims |
| Rollout teacher is not optimal | OR reviewers | Call it high-fidelity teacher, include small exact instances, report teacher limits |
| GNN is unnecessary | ML reviewers | Treat GNN as optional ablation, not core claim |
| GPU rollout might solve the problem | Systems/practitioner reviewers | Include GPU rollout as a frontier point and let results decide |
| Cascades are engineering, not research | OR/ML reviewers | Frame cascade as selective stochastic evaluation under latency budget; evaluate threshold frontier and escalation rates |

## Must-Cite Shortlist

1. Simão et al. 2009, Transportation Science.
2. Kim, Mahmassani, and Jaillet 2004, Transportation Research Record.
3. Kim, Mahmassani, and Jaillet 2002, Transportation Research Record.
4. Ulmer et al. 2019, Transportation Science.
5. Ulmer and Thomas 2020, European Journal of Operational Research.
6. van Heeswijk and La Poutré 2019.
7. Dumouchelle et al. 2022, NeurIPS.
8. Nazari et al. 2018, NeurIPS.
9. Kool et al. 2019, ICLR.
10. Derrow-Pinion et al. 2021, CIKM.
11. Budak et al. 2017, Transportation Research Part A.
12. Lindsey and Mahmassani 2015/2017.

## Related Work Section Skeleton

1. **Dynamic freight and vehicle-routing acceptance.**
   Discuss ADP/VFA and load/customer acceptance. End with: these methods model future value but do not primarily study real-time bid-evaluation latency under public-data constraints.

2. **Learning surrogates for stochastic value functions.**
   Discuss neural VFAs and neural stochastic-programming surrogates. End with: these methods motivate value distillation but need closed-loop freight decision evaluation.

3. **Graph and learned routing methods.**
   Discuss learned routing and GNN transportation models. End with: useful representation tools, but not the core novelty.

4. **Truckload spot-market data and pricing.**
   Discuss rate forecasting and reservation price work. End with: market work often lacks downstream fleet-state opportunity cost.

5. **Public-calibrated benchmark gap.**
   Introduce FreightBidBench as the artifact joining these threads.

