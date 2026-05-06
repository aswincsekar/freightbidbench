# Faster Planning Research Notes

## Current Direction

The strongest v1 paper is:

> FreightBidBench: a public-calibrated benchmark and method comparison for real-time truckload bid acceptance.

The core method angle is a **cascaded selective evaluator**:

1. Use cheap rules for obvious accept/reject decisions.
2. Use a fast value surrogate for normal decisions.
3. Use stochastic rollout only for ambiguous or high-stakes loads.

The core empirical artifact is the **latency-profit frontier**.

## Files

| File | Purpose |
| --- | --- |
| `freight_stochastic_networks_realtime_bid_eval.md` | Main narrative memo: thesis, lit review, positioning, risks, and current best bet. |
| `FREIGHTBIDBENCH.md` | Public benchmark protocol, run commands, output schema, and reporting rules. |
| `public_data_inventory.md` | Public data source inventory and calibration plan for FAF and USDA AMS truck-rate data. |
| `literature_matrix.md` | Working related-work matrix, positioning statement, and reviewer-risk matrix. |
| `freightbidbench_experiment_blueprint.md` | Buildable benchmark and experiment specification. |
| `scripts/inspect_public_sources.py` | Streams the FAF zip, parses USDA FVWTRK text, and writes calibration summaries. |
| `scripts/run_opportunity_cost_sanity.py` | Runs the first one-shot sanity check for trap and repositioning decisions. |
| `scripts/run_closed_loop_baselines.py` | Runs the first closed-loop simulator and compares baseline accept/reject policies. |
| `scripts/run_rollout_teacher.py` | Runs the first CPU rollout teacher on a short tight-capacity probe scenario. |
| `scripts/run_surrogate_cascade.py` | Generates rollout labels, trains a dependency-free linear surrogate, and evaluates a selective cascade/frontier. |
| `scripts/run_experimental_package.py` | Runs the multi-seed, multi-scenario experimental package and writes aggregate policy/frontier tables. |
| `scripts/freight_feasibility.py` | FreightBidBench v0.2 feasibility layer: individual trucks, pickup reach, appointment windows, HOS clocks, and yard delays. |
| `scripts/run_freightbidbench.py` | Public FreightBidBench v0.2 CLI with smoke, standard, and paper presets. |
| `reports/initial_calibration_report.md` | First report from inspected FAF/USDA data. |
| `reports/opportunity_cost_sanity_report.md` | First sanity report showing where myopic and opportunity-cost-aware decisions differ. |
| `reports/closed_loop_baseline_report.md` | First closed-loop policy comparison across base and tight-capacity scenarios. |
| `reports/rollout_teacher_report.md` | First rollout-teacher comparison against myopic and bid-price policies. |
| `reports/surrogate_cascade_report.md` | First value-distillation result and cascade latency-profit frontier. |
| `reports/experimental_package_report.md` | Multi-seed experimental package report across mild, tight, and scarce capacity regimes. |
| `papers/freightbidbench_v02_benchmark_paper.md` | First benchmark-paper manuscript draft with v0.2 standard results. |
| `papers/references.bib` | BibTeX references for the benchmark-paper draft. |
| `papers/benchmark_release_checklist.md` | Release checklist and claim boundaries for FreightBidBench v0.2. |

## Next Work Package

Completed:

1. Downloaded FAF5.7.1 state data and USDA FVWTRK truck-rate PDF.
2. Parsed FAF state truck-flow summaries and USDA reefer lane-rate quotes.
3. Built `data/processed/v1_usda_faf_mapped_lanes.csv` as the first seed lane table.
4. Ran a first opportunity-cost sanity check.
5. Built a closed-loop simulator where accepted loads move trucks and future loads arrive over a week.
6. Built a CPU rollout teacher that compares accept versus reject with common-random-number future simulations.
7. Generated offline rollout labels, trained a simple linear surrogate, and evaluated a selective surrogate/rollout cascade.
8. Added a multi-seed, multi-scenario experimental package with aggregate policy and cascade-frontier outputs.
9. Added a public FreightBidBench v0.1 runner, manifest, and reporting protocol.
10. Added FreightBidBench v0.2 feasibility: individual truck state, pickup reach time, pickup/delivery windows, simplified HOS, and stochastic pickup/dropoff yard delays.

Current result:

- The sanity check generated both trap decisions and repositioning decisions.
- Myopic accepts but value-aware rejects: 51 of 5,000 simulated loads.
- Myopic rejects but value-aware accepts: 39 of 5,000 simulated loads.
- One-shot opportunity-value objective lift: $85,109.
- In the mild base scenario, myopic margin is still best, which means the benchmark can represent easy markets.
- In the tight-capacity scenario, `bid_price_conservative` beats myopic by $1,121,045 over the simulated week.
- In the scarce-capacity/high-demand scenario, `bid_price_strong_future` beats myopic by $1,182,893 over the simulated week.
- In the rollout probe, `rollout_teacher` earns $1,660,405 versus $1,627,144 for `bid_price` and $1,437,245 for `myopic_margin`.
- The rollout probe's mean decision latency is 2.528 ms versus roughly 0.001 ms for `bid_price`, establishing the first latency-quality gap.
- In the first value-distillation test, the linear surrogate reaches 94.0% of rollout profit at 0.003 ms mean latency.
- The first cascade reaches 97.2% of rollout profit at 0.902 ms mean latency while escalating 40.3% of decisions to rollout.
- The frontier sweep shows 99.1% rollout-profit retention when escalating 60.4% of decisions, and 95.1% retention when escalating only 16.5%.
- The experimental package now runs 3 seed pairs across mild, tight, and scarce 72-hour scenarios.
- In mild capacity, myopic/rollout/surrogate are effectively tied near $1.73M, confirming the benchmark has easy regimes.
- In scarce capacity, rollout earns $1.44M versus $1.34M for bid price and $1.27M for myopic; the cascade reaches 98.7% rollout retention at the widest band while using 68.3% rollout calls.
- In tight capacity, the finite rollout teacher is not an oracle: bid price and wider cascades slightly exceed 100% rollout retention on realized profit, so the paper should frame rollout as a stochastic benchmark.
- The package artifacts are `experimental_policy_runs.csv`, `experimental_static_label_fit.csv`, `experimental_policy_summary.csv`, and `experimental_frontier_summary.csv`.
- The publishable benchmark entry point is now `python3 scripts/run_freightbidbench.py --preset standard --output-dir benchmark_runs/standard` from the `faster_planning/` directory.
- FreightBidBench v0.2 standard output is in `benchmark_runs/standard_v02`; it uses 3 seed pairs, 3 scenarios, 600 rollout labels per train/eval stream, and the full 72-hour evaluation horizon.
- v0.2 policy summaries now include infeasible accept attempts, pickup-window misses, delivery-window misses, deadhead miles, HOS rest hours, and yard-delay hours.
- v0.2 standard results: rollout earns $942k in tight capacity versus $867k for myopic/bid-price, and $758k in scarce capacity versus $718k for myopic/bid-price.
- v0.2 figures are in `benchmark_runs/standard_v02/figures`.
- The first benchmark-paper draft is `papers/freightbidbench_v02_benchmark_paper.md`.
- The benchmark-paper references are in `papers/references.bib`, and the release checklist is in `papers/benchmark_release_checklist.md`.

The next concrete work package is to make the benchmark release external-facing: add license/citation files, decide whether processed data can be redistributed, add a CSV column dictionary appendix, and decide whether to run the heavier `paper` preset.
