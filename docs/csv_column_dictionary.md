# FreightBidBench CSV Column Dictionary

This dictionary describes the CSV artifacts written by
`scripts/run_freightbidbench.py`.

## Shared Scenario Columns

| Column | Description |
| --- | --- |
| `scenario` | Public benchmark scenario key: `mild`, `tight`, or `scarce`. |
| `horizon_hours` | Simulated online decision horizon in hours. |
| `loads_per_hour` | Mean generated load tenders per simulated hour. |
| `fleet_size` | Number of trucks initialized in the scenario. |
| `base_cost_per_mile` | Scenario linehaul cost basis used by the simulator. |
| `fixed_load_cost` | Fixed cost charged per load. |
| `value_scale_dollars` | Scenario scale for state future-value features. |
| `train_seed` | Seed used to generate offline rollout labels for training. |
| `eval_seed` | Seed used for held-out labels and online closed-loop evaluation. |

## `freightbidbench_policy_runs.csv`

One row per scenario, seed pair, and policy.

| Column | Description |
| --- | --- |
| `train_label_count` | Number of rollout labels generated on the train stream. |
| `eval_label_count` | Number of rollout labels generated on the evaluation stream. |
| `static_agreement` | Surrogate accept/reject agreement on held-out rollout labels. |
| `static_mae` | Mean absolute error of surrogate incremental-value labels. |
| `static_p90_abs_error` | 90th percentile absolute surrogate label error. |
| `policy` | Evaluated policy name. |
| `cascade_band_dollars` | Escalation band for cascade policy; blank for non-cascade policies. |
| `loads_seen` | Number of tendered loads observed by the policy. |
| `accepted` | Number of accepted and successfully assigned loads. |
| `rejected` | Number of rejected loads. |
| `no_truck` | Accept attempts with no truck in the origin market. |
| `infeasible` | Accept attempts that failed feasibility checks. |
| `pickup_window_miss` | Accept attempts failing pickup latest-time feasibility. |
| `delivery_window_miss` | Accept attempts failing delivery latest-time feasibility. |
| `accept_rate` | Accepted loads divided by loads seen. |
| `profit` | Closed-loop realized profit after direct, deadhead, and yard-delay costs. |
| `service_failure_penalty_cost` | v0.3 optional: cancellation/service-failure cost charged for failed accept attempts. |
| `terminal_fleet_value` | v0.3 optional: end-of-horizon fleet-position value added to realized profit. |
| `profit_retention_vs_rollout` | Profit divided by same-scenario finite rollout-teacher profit. |
| `revenue` | Revenue from accepted loads. |
| `direct_cost` | Direct linehaul and fixed load costs. |
| `loaded_miles` | Linehaul miles on accepted loads. |
| `deadhead_miles` | Pickup deadhead miles on accepted loads. |
| `yard_delay_hours` | Pickup and dropoff yard-delay hours on accepted loads. |
| `hos_rest_hours` | Required HOS reset hours inserted by the feasibility layer. |
| `profit_per_loaded_mile` | Profit divided by loaded miles. |
| `utilization` | Accepted-load loaded miles relative to fleet and horizon scale. |
| `mean_latency_ms` | Mean policy decision latency in milliseconds. |
| `p50_latency_ms` | Median policy decision latency in milliseconds. |
| `p95_latency_ms` | 95th percentile policy decision latency in milliseconds. |
| `surrogate_stage_share` | Share of decisions handled by the surrogate stage. |
| `rollout_stage_share` | Share of decisions escalated to rollout. |
| `final_top_states` | Compact final fleet-location summary. |
| `cell_elapsed_seconds` | Wall-clock time to generate labels, fit surrogate, and evaluate the cell. |

## `freightbidbench_static_label_fit.csv`

One row per scenario and seed pair.

| Column | Description |
| --- | --- |
| `train_label_count` | Number of training rollout-label decisions. |
| `eval_label_count` | Number of evaluation rollout-label decisions. |
| `agreement` | Held-out accept/reject agreement between surrogate and rollout labels. |
| `mae` | Held-out mean absolute label error. |
| `p90_abs_error` | Held-out 90th percentile absolute label error. |
| `cell_elapsed_seconds` | Label-generation and fitting wall-clock time for the cell. |

## `freightbidbench_policy_summary.csv`

Aggregate rows grouped by scenario, policy, and cascade band.

| Column | Description |
| --- | --- |
| `n_runs` | Number of seed-pair runs in the aggregate. |
| `mean_profit` | Mean closed-loop profit across runs. |
| `mean_service_failure_penalty_cost` | v0.3 optional: mean service-failure penalty cost across runs. |
| `mean_terminal_fleet_value` | v0.3 optional: mean terminal fleet-position value across runs. |
| `std_profit` | Sample standard deviation of profit across runs. |
| `ci95_profit_halfwidth` | Normal-approximation 95% confidence-interval half-width. |
| `mean_profit_retention_vs_rollout` | Mean profit retention relative to rollout teacher. |
| `min_profit_retention_vs_rollout` | Minimum seed-level retention in the group. |
| `max_profit_retention_vs_rollout` | Maximum seed-level retention in the group. |
| `mean_latency_ms` | Mean decision latency across runs. |
| `mean_p95_latency_ms` | Mean of seed-level p95 latency values. |
| `mean_rollout_stage_share` | Mean rollout-call share. |
| `mean_surrogate_stage_share` | Mean surrogate-stage share. |
| `mean_accepted` | Mean accepted loads. |
| `mean_no_truck` | Mean no-truck accept outcomes. |
| `mean_infeasible` | Mean infeasible accept outcomes. |
| `mean_pickup_window_miss` | Mean pickup-window misses. |
| `mean_delivery_window_miss` | Mean delivery-window misses. |
| `mean_accept_rate` | Mean accepted-load share. |
| `mean_deadhead_miles` | Mean pickup deadhead miles. |
| `mean_yard_delay_hours` | Mean yard-delay hours. |
| `mean_hos_rest_hours` | Mean HOS reset hours. |
| `mean_static_agreement` | Mean held-out surrogate agreement for the cell. |
| `mean_static_mae` | Mean held-out surrogate MAE for the cell. |
| `mean_static_p90_abs_error` | Mean held-out surrogate p90 absolute error. |

## `freightbidbench_frontier_summary.csv`

Subset of `freightbidbench_policy_summary.csv` containing cascade rows used to
plot the latency/profit and rollout-share/profit frontiers.

## `freightbidbench_manifest.json`

Run metadata including benchmark version, command, Python version, elapsed
runtime, scenario-config version, policy-set version, scenario-config path,
seed pairs, scenarios, default policy list, cascade policy, evaluated policy
list, cascade bands, feasibility-layer features, output paths, and row counts.
