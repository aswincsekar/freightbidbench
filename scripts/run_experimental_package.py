#!/usr/bin/env python3
"""Run a repeatable experimental package for FreightBidBench.

This runner wraps the first surrogate/cascade prototype in a multi-seed
experiment. It writes paper-oriented artifacts:

- seed-level policy results,
- seed-level offline label-fit metrics,
- aggregate policy summaries, and
- an aggregate cascade latency-profit frontier.
"""

from __future__ import annotations

import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import run_closed_loop_baselines as base  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


POLICY_RUNS_OUT = ROOT / "data" / "processed" / "experimental_policy_runs.csv"
STATIC_FIT_OUT = ROOT / "data" / "processed" / "experimental_static_label_fit.csv"
POLICY_SUMMARY_OUT = ROOT / "data" / "processed" / "experimental_policy_summary.csv"
FRONTIER_SUMMARY_OUT = ROOT / "data" / "processed" / "experimental_frontier_summary.csv"
REPORT_OUT = ROOT / "reports" / "experimental_package_report.md"

SEED_PAIRS = [
    (20260506, 20260507),
    (20260508, 20260509),
    (20260510, 20260511),
]

EXPERIMENT_SCENARIOS = [
    base.Scenario(
        "surrogate_probe_mild_capacity",
        horizon_hours=72,
        loads_per_hour=12,
        fleet_size=90,
        base_cost_per_mile=2.95,
        fixed_load_cost=250.0,
        value_scale_dollars=2400.0,
    ),
    sc.SCENARIO,
    base.Scenario(
        "surrogate_probe_scarce_capacity",
        horizon_hours=72,
        loads_per_hour=16,
        fleet_size=55,
        base_cost_per_mile=3.20,
        fixed_load_cost=250.0,
        value_scale_dollars=3400.0,
    ),
]

BASELINE_POLICIES = [
    "reject_all",
    "accept_all_feasible",
    "myopic_margin",
    "bid_price",
    "surrogate_linear",
    "rollout_teacher",
]

REPRESENTATIVE_CASCADE_BAND = sc.CASCADE_BAND_DOLLARS


def as_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def student_t_975(df: int) -> float:
    """Small lookup table for two-sided 95% intervals."""
    if df <= 0:
        return 0.0
    table = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
    }
    return table.get(df, 1.960)


def ci95_halfwidth(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return student_t_975(len(values) - 1) * std(values) / math.sqrt(len(values))


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return statistics.mean(values)


def scenario_config_row(scenario: base.Scenario) -> dict[str, object]:
    return {
        "scenario": scenario.name,
        "horizon_hours": scenario.horizon_hours,
        "loads_per_hour": scenario.loads_per_hour,
        "fleet_size": scenario.fleet_size,
        "base_cost_per_mile": f"{scenario.base_cost_per_mile:.2f}",
        "fixed_load_cost": f"{scenario.fixed_load_cost:.2f}",
        "value_scale_dollars": f"{scenario.value_scale_dollars:.2f}",
    }


def decorate_policy_row(
    summary: dict[str, object],
    scenario: base.Scenario,
    train_seed: int,
    eval_seed: int,
    rollout_profit: float,
    static_metrics: dict[str, float],
    train_label_count: int,
    eval_label_count: int,
    elapsed_seconds: float,
) -> dict[str, object]:
    profit = as_float(summary["profit"])
    row = {
        **scenario_config_row(scenario),
        "train_seed": train_seed,
        "eval_seed": eval_seed,
        "train_label_count": train_label_count,
        "eval_label_count": eval_label_count,
        "static_agreement": f"{static_metrics['agreement']:.6f}",
        "static_mae": f"{static_metrics['mae']:.2f}",
        "static_p90_abs_error": f"{static_metrics['p90_abs_error']:.2f}",
        "policy": summary["policy"],
        "cascade_band_dollars": summary.get("cascade_band_dollars", ""),
        "loads_seen": summary["loads_seen"],
        "accepted": summary["accepted"],
        "rejected": summary["rejected"],
        "no_truck": summary["no_truck"],
        "infeasible": summary.get("infeasible", 0),
        "pickup_window_miss": summary.get("pickup_window_miss", 0),
        "delivery_window_miss": summary.get("delivery_window_miss", 0),
        "accept_rate": summary["accept_rate"],
        "profit": summary["profit"],
        "profit_retention_vs_rollout": f"{profit / rollout_profit:.6f}"
        if rollout_profit
        else "0.000000",
        "revenue": summary["revenue"],
        "direct_cost": summary["direct_cost"],
        "loaded_miles": summary["loaded_miles"],
        "deadhead_miles": summary.get("deadhead_miles", "0.00"),
        "yard_delay_hours": summary.get("yard_delay_hours", "0.00"),
        "hos_rest_hours": summary.get("hos_rest_hours", "0.00"),
        "profit_per_loaded_mile": summary["profit_per_loaded_mile"],
        "utilization": summary["utilization"],
        "mean_latency_ms": summary["mean_latency_ms"],
        "p50_latency_ms": summary["p50_latency_ms"],
        "p95_latency_ms": summary["p95_latency_ms"],
        "surrogate_stage_share": summary["surrogate_stage_share"],
        "rollout_stage_share": summary["rollout_stage_share"],
        "final_top_states": summary["final_top_states"],
        "cell_elapsed_seconds": f"{elapsed_seconds:.2f}",
    }
    if "service_failure_penalty_cost" in summary:
        row["service_failure_penalty_cost"] = summary["service_failure_penalty_cost"]
    if "terminal_fleet_value" in summary:
        row["terminal_fleet_value"] = summary["terminal_fleet_value"]
    return row


def static_fit_row(
    scenario: base.Scenario,
    train_seed: int,
    eval_seed: int,
    static_metrics: dict[str, float],
    train_label_count: int,
    eval_label_count: int,
    elapsed_seconds: float,
) -> dict[str, object]:
    return {
        **scenario_config_row(scenario),
        "train_seed": train_seed,
        "eval_seed": eval_seed,
        "train_label_count": train_label_count,
        "eval_label_count": eval_label_count,
        "agreement": f"{static_metrics['agreement']:.6f}",
        "mae": f"{static_metrics['mae']:.2f}",
        "p90_abs_error": f"{static_metrics['p90_abs_error']:.2f}",
        "cell_elapsed_seconds": f"{elapsed_seconds:.2f}",
    }


def run_cell(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    train_seed: int,
    eval_seed: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    start = time.perf_counter()
    state_values = base.build_state_values(lanes, scenario)

    train_labels, _, _ = sc.generate_rollout_labels(
        lanes, scenario, train_seed, state_values
    )
    eval_labels, _, _ = sc.generate_rollout_labels(
        lanes, scenario, eval_seed, state_values
    )
    model = sc.train_linear_model(train_labels)
    static_metrics = sc.evaluate_static_labels(model, eval_labels)

    eval_loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    starting_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)

    policy_summaries: dict[str, dict[str, object]] = {}
    for policy_name in BASELINE_POLICIES:
        summary, _ = sc.simulate_policy(
            policy_name,
            eval_loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            model,
            rollout_seed_offset=eval_seed,
        )
        policy_summaries[policy_name] = summary

    rollout_profit = as_float(policy_summaries["rollout_teacher"]["profit"])
    policy_rows = [
        decorate_policy_row(
            summary,
            scenario,
            train_seed,
            eval_seed,
            rollout_profit,
            static_metrics,
            len(train_labels),
            len(eval_labels),
            time.perf_counter() - start,
        )
        for summary in policy_summaries.values()
    ]

    for band in sc.CASCADE_FRONTIER_BANDS:
        summary, _ = sc.simulate_policy(
            "cascade_surrogate_rollout",
            eval_loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            model,
            cascade_band_dollars=band,
            rollout_seed_offset=eval_seed,
        )
        policy_rows.append(
            decorate_policy_row(
                summary,
                scenario,
                train_seed,
                eval_seed,
                rollout_profit,
                static_metrics,
                len(train_labels),
                len(eval_labels),
                time.perf_counter() - start,
            )
        )

    elapsed_seconds = time.perf_counter() - start
    fit_row = static_fit_row(
        scenario,
        train_seed,
        eval_seed,
        static_metrics,
        len(train_labels),
        len(eval_labels),
        elapsed_seconds,
    )
    return policy_rows, fit_row


def group_key(row: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(row["scenario"]),
        str(row["policy"]),
        str(row.get("cascade_band_dollars", "")),
    )


def aggregate_policy_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: defaultdict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)

    aggregate_rows: list[dict[str, object]] = []
    for (scenario, policy, band), group in grouped.items():
        profits = [as_float(row["profit"]) for row in group]
        retentions = [as_float(row["profit_retention_vs_rollout"]) for row in group]
        latencies = [as_float(row["mean_latency_ms"]) for row in group]
        p95_latencies = [as_float(row["p95_latency_ms"]) for row in group]
        rollout_shares = [as_float(row["rollout_stage_share"]) for row in group]
        surrogate_shares = [as_float(row["surrogate_stage_share"]) for row in group]
        aggregate_row = {
            "scenario": scenario,
            "policy": policy,
            "cascade_band_dollars": band,
            "n_runs": len(group),
            "mean_profit": f"{mean(profits):.2f}",
            "std_profit": f"{std(profits):.2f}",
            "ci95_profit_halfwidth": f"{ci95_halfwidth(profits):.2f}",
            "mean_profit_retention_vs_rollout": f"{mean(retentions):.6f}",
            "min_profit_retention_vs_rollout": f"{min(retentions):.6f}",
            "max_profit_retention_vs_rollout": f"{max(retentions):.6f}",
            "mean_latency_ms": f"{mean(latencies):.6f}",
            "mean_p95_latency_ms": f"{mean(p95_latencies):.6f}",
            "mean_rollout_stage_share": f"{mean(rollout_shares):.6f}",
            "mean_surrogate_stage_share": f"{mean(surrogate_shares):.6f}",
            "mean_accepted": f"{mean([as_float(row['accepted']) for row in group]):.2f}",
            "mean_no_truck": f"{mean([as_float(row['no_truck']) for row in group]):.2f}",
            "mean_infeasible": f"{mean([as_float(row.get('infeasible', 0)) for row in group]):.2f}",
            "mean_pickup_window_miss": f"{mean([as_float(row.get('pickup_window_miss', 0)) for row in group]):.2f}",
            "mean_delivery_window_miss": f"{mean([as_float(row.get('delivery_window_miss', 0)) for row in group]):.2f}",
            "mean_accept_rate": f"{mean([as_float(row['accept_rate']) for row in group]):.6f}",
            "mean_deadhead_miles": f"{mean([as_float(row.get('deadhead_miles', 0)) for row in group]):.2f}",
            "mean_yard_delay_hours": f"{mean([as_float(row.get('yard_delay_hours', 0)) for row in group]):.2f}",
            "mean_hos_rest_hours": f"{mean([as_float(row.get('hos_rest_hours', 0)) for row in group]):.2f}",
            "mean_static_agreement": f"{mean([as_float(row['static_agreement']) for row in group]):.6f}",
            "mean_static_mae": f"{mean([as_float(row['static_mae']) for row in group]):.2f}",
            "mean_static_p90_abs_error": f"{mean([as_float(row['static_p90_abs_error']) for row in group]):.2f}",
        }
        if any("service_failure_penalty_cost" in row for row in group):
            aggregate_row["mean_service_failure_penalty_cost"] = (
                f"{mean([as_float(row.get('service_failure_penalty_cost', 0)) for row in group]):.2f}"
            )
        if any("terminal_fleet_value" in row for row in group):
            aggregate_row["mean_terminal_fleet_value"] = (
                f"{mean([as_float(row.get('terminal_fleet_value', 0)) for row in group]):.2f}"
            )
        aggregate_rows.append(aggregate_row)

    return sorted(aggregate_rows, key=aggregate_sort_key)


def aggregate_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    policy_order = {
        "reject_all": 0,
        "accept_all_feasible": 1,
        "myopic_margin": 2,
        "bid_price": 3,
        "surrogate_linear": 4,
        "cascade_surrogate_rollout": 5,
        "rollout_teacher": 6,
    }
    band = as_float(row.get("cascade_band_dollars", ""))
    return (row["scenario"], policy_order.get(str(row["policy"]), 99), band)


def aggregate_static_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario"])].append(row)

    aggregate_rows: list[dict[str, object]] = []
    for scenario, group in grouped.items():
        agreements = [as_float(row["agreement"]) for row in group]
        maes = [as_float(row["mae"]) for row in group]
        p90s = [as_float(row["p90_abs_error"]) for row in group]
        aggregate_rows.append(
            {
                "scenario": scenario,
                "n_runs": len(group),
                "mean_agreement": f"{mean(agreements):.6f}",
                "std_agreement": f"{std(agreements):.6f}",
                "mean_mae": f"{mean(maes):.2f}",
                "std_mae": f"{std(maes):.2f}",
                "mean_p90_abs_error": f"{mean(p90s):.2f}",
                "std_p90_abs_error": f"{std(p90s):.2f}",
            }
        )
    return sorted(aggregate_rows, key=lambda row: str(row["scenario"]))


def build_frontier_rows(policy_summary_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [
        row
        for row in policy_summary_rows
        if row["policy"] == "cascade_surrogate_rollout"
    ]
    return sorted(rows, key=lambda row: (str(row["scenario"]), as_float(row["cascade_band_dollars"])))


def money(value: object) -> str:
    return f"${as_float(value):,.0f}"


def percent(value: object) -> str:
    return f"{as_float(value):.1%}"


def representative_rows(policy_summary_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in policy_summary_rows:
        if row["policy"] != "cascade_surrogate_rollout":
            rows.append(row)
            continue
        if abs(as_float(row["cascade_band_dollars"]) - REPRESENTATIVE_CASCADE_BAND) < 1e-9:
            rows.append(row)
    return sorted(rows, key=aggregate_sort_key)


def write_report(
    policy_summary_rows: list[dict[str, object]],
    frontier_rows: list[dict[str, object]],
    static_summary_rows: list[dict[str, object]],
    elapsed_seconds: float,
) -> None:
    seed_text = ", ".join(f"{train}/{eval_}" for train, eval_ in SEED_PAIRS)
    scenario_lines = [
        "| Scenario | Horizon | Loads/Hour | Fleet | Cost/Mile | Value Scale |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scenario in EXPERIMENT_SCENARIOS:
        scenario_lines.append(
            f"| `{scenario.name}` | {scenario.horizon_hours}h | "
            f"{scenario.loads_per_hour} | {scenario.fleet_size} | "
            f"${scenario.base_cost_per_mile:.2f} | ${scenario.value_scale_dollars:,.0f} |"
        )

    static_lines = [
        "| Scenario | Runs | Agreement | MAE | p90 Abs Error |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in static_summary_rows:
        static_lines.append(
            f"| `{row['scenario']}` | {row['n_runs']} | "
            f"{percent(row['mean_agreement'])} | {money(row['mean_mae'])} | "
            f"{money(row['mean_p90_abs_error'])} |"
        )

    policy_lines = [
        "| Scenario | Policy | Band | Mean Profit | Profit CI95 | Retention | Mean Latency ms | Rollout Share |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in representative_rows(policy_summary_rows):
        band = row["cascade_band_dollars"] or "-"
        policy_lines.append(
            f"| `{row['scenario']}` | `{row['policy']}` | {band} | "
            f"{money(row['mean_profit'])} | +/- {money(row['ci95_profit_halfwidth'])} | "
            f"{percent(row['mean_profit_retention_vs_rollout'])} | "
            f"{as_float(row['mean_latency_ms']):.3f} | "
            f"{percent(row['mean_rollout_stage_share'])} |"
        )

    frontier_lines = [
        "| Scenario | Band +/- $ | Retention | Mean Profit | Mean Latency ms | Rollout Share |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in frontier_rows:
        frontier_lines.append(
            f"| `{row['scenario']}` | {as_float(row['cascade_band_dollars']):,.0f} | "
            f"{percent(row['mean_profit_retention_vs_rollout'])} | "
            f"{money(row['mean_profit'])} | {as_float(row['mean_latency_ms']):.3f} | "
            f"{percent(row['mean_rollout_stage_share'])} |"
        )

    content = f"""# Experimental Package Report

## Configuration

- Seed pairs: {seed_text}
- Baseline policies: {", ".join(f"`{policy}`" for policy in BASELINE_POLICIES)}
- Cascade bands: {", ".join(f"+/- ${band:,.0f}" for band in sc.CASCADE_FRONTIER_BANDS)}
- Rollout labels per train/eval stream: up to {sc.LABEL_DECISION_LIMIT:,}
- Total package runtime: {elapsed_seconds:.2f} seconds

{chr(10).join(scenario_lines)}

## Offline Label Fit

{chr(10).join(static_lines)}

## Representative Policy Results

The table reports seed-averaged closed-loop profit. The cascade row uses the
representative +/- ${REPRESENTATIVE_CASCADE_BAND:,.0f} escalation band; the full
frontier is below.

{chr(10).join(policy_lines)}

## Aggregate Cascade Frontier

{chr(10).join(frontier_lines)}

## Package Artifacts

- `data/processed/{POLICY_RUNS_OUT.name}`: one row per seed, policy, and cascade band.
- `data/processed/{STATIC_FIT_OUT.name}`: one row per seed with held-out rollout-label fit.
- `data/processed/{POLICY_SUMMARY_OUT.name}`: aggregate policy table with variance and confidence intervals.
- `data/processed/{FRONTIER_SUMMARY_OUT.name}`: aggregate cascade frontier table.

## Interpretation

This is now a paper-style experimental package rather than a single illustrative
run. It gives the paper a reproducible protocol, repeated stochastic seeds,
scenario stress tests, held-out rollout-label diagnostics, and a latency-profit
frontier.

The finite rollout teacher should be interpreted as a stochastic benchmark, not
as an oracle. When a cheap policy exceeds 100% retention, it means that policy
earned more realized closed-loop profit than the finite-lookahead teacher on
that seed average.

The package is still a preliminary version. Before making final claims, the
next upgrades are a stronger surrogate, plotting scripts, and a public release
README that pins the data-preparation commands.
"""
    REPORT_OUT.write_text(content, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    lanes = base.load_csv(base.LANES)
    policy_rows: list[dict[str, object]] = []
    static_rows: list[dict[str, object]] = []

    for scenario in EXPERIMENT_SCENARIOS:
        for train_seed, eval_seed in SEED_PAIRS:
            print(
                f"Running {scenario.name} train_seed={train_seed} eval_seed={eval_seed}",
                flush=True,
            )
            cell_policy_rows, cell_static_row = run_cell(
                lanes, scenario, train_seed, eval_seed
            )
            policy_rows.extend(cell_policy_rows)
            static_rows.append(cell_static_row)

    policy_summary_rows = aggregate_policy_rows(policy_rows)
    static_summary_rows = aggregate_static_rows(static_rows)
    frontier_rows = build_frontier_rows(policy_summary_rows)
    elapsed_seconds = time.perf_counter() - start

    sc.write_csv(POLICY_RUNS_OUT, policy_rows)
    sc.write_csv(STATIC_FIT_OUT, static_rows)
    sc.write_csv(POLICY_SUMMARY_OUT, policy_summary_rows)
    sc.write_csv(FRONTIER_SUMMARY_OUT, frontier_rows)
    write_report(
        policy_summary_rows,
        frontier_rows,
        static_summary_rows,
        elapsed_seconds,
    )

    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    for row in representative_rows(policy_summary_rows):
        print(
            f"{row['scenario']} {row['policy']} band={row['cascade_band_dollars'] or '-'}: "
            f"mean profit {money(row['mean_profit'])}, "
            f"retention {percent(row['mean_profit_retention_vs_rollout'])}, "
            f"mean latency {as_float(row['mean_latency_ms']):.3f} ms"
        )


if __name__ == "__main__":
    main()
