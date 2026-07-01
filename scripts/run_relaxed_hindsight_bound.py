#!/usr/bin/env python3
"""Compute relaxed full-horizon upper bounds for FreightBidBench v0.3.

This script is intentionally separate from the exact DP in
`run_hindsight_bound.py`. It reports cheap relaxations for paper-scale streams:

- positive-profit bound: accept every profitable realized load;
- fractional truck-hour bound: ignore location and sequencing, but charge each
  load a lower-bound busy time and solve the fractional knapsack relaxation.

Both bounds are ceilings, not achievable policies.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


DEFAULT_CONFIG_PATH = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "relaxed_bound_smoke"
DEFAULT_SCENARIO = "tight"
SIMPLE_POLICIES = ["reject_all", "accept_all_feasible", "myopic_margin", "bid_price"]


@dataclass(frozen=True)
class LoadTerm:
    load_id: int
    hour: float
    origin_state: str
    destination_state: str
    profit: float
    lower_bound_busy_hours: float
    fresh_truck_busy_hours: float


def scenario_from_config(config: dict[str, object]) -> base.Scenario:
    return base.Scenario(
        str(config["name"]),
        horizon_hours=int(config["horizon_hours"]),
        loads_per_hour=int(config["loads_per_hour"]),
        fleet_size=int(config["fleet_size"]),
        base_cost_per_mile=float(config["base_cost_per_mile"]),
        fixed_load_cost=float(config["fixed_load_cost"]),
        value_scale_dollars=float(config["value_scale_dollars"]),
        service_failure_penalty_dollars=config.get("service_failure_penalty_dollars"),
        terminal_value_weight=config.get("terminal_value_weight"),
        demand_wave_schedule=config.get("demand_wave_schedule"),
    )


def load_config(config_path: Path) -> tuple[Path, dict[str, object], dict[str, base.Scenario]]:
    path = config_path if config_path.is_absolute() else ROOT / config_path
    config = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {
        name: scenario_from_config(scenario_config)
        for name, scenario_config in dict(config["scenarios"]).items()
    }
    return path, config, scenarios


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def money(value: float) -> str:
    return f"${value:,.0f}"


def lower_bound_busy_hours(load: dict[str, object]) -> float:
    pickup_service = feas.PICKUP_BASE_SERVICE_HOURS + float(
        load.get("pickup_yard_delay_hours", 0.0)
    )
    dropoff_service = feas.DROPOFF_BASE_SERVICE_HOURS + float(
        load.get("dropoff_yard_delay_hours", 0.0)
    )
    linehaul = float(load.get("linehaul_drive_hours", load.get("travel_hours", 0.0)))
    return max(1e-9, pickup_service + linehaul + dropoff_service)


def fresh_truck_term(load: dict[str, object]) -> LoadTerm | None:
    origin = str(load["origin_state"])
    fleet = {origin: [feas.TruckState("relaxed-fresh", origin, float(load["hour"]))]}
    assignment = feas.apply_accept(fleet, load, float(load["hour"]))
    if not assignment.accepted:
        return None
    return LoadTerm(
        load_id=int(load["load_id"]),
        hour=float(load["hour"]),
        origin_state=origin,
        destination_state=str(load["destination_state"]),
        profit=assignment.profit,
        lower_bound_busy_hours=lower_bound_busy_hours(load),
        fresh_truck_busy_hours=assignment.busy_hours,
    )


def positive_terms(loads: list[dict[str, object]]) -> list[LoadTerm]:
    terms: list[LoadTerm] = []
    for load in loads:
        term = fresh_truck_term(load)
        if term is not None and term.profit > 0.0:
            terms.append(term)
    return terms


def fractional_knapsack_profit(terms: list[LoadTerm], capacity_hours: float) -> float:
    remaining = max(0.0, capacity_hours)
    total = 0.0
    ranked = sorted(
        terms,
        key=lambda term: term.profit / max(term.lower_bound_busy_hours, 1e-9),
        reverse=True,
    )
    for term in ranked:
        if remaining <= 1e-9:
            break
        busy = max(term.lower_bound_busy_hours, 1e-9)
        if busy <= remaining:
            total += term.profit
            remaining -= busy
        else:
            total += term.profit * (remaining / busy)
            remaining = 0.0
    return total


def terminal_value_upper_bound(
    scenario: base.Scenario,
    state_values: dict[str, float],
) -> float:
    if not state_values:
        return 0.0
    best_state_value = max(state_values.values())
    return max(
        0.0,
        scenario.fleet_size
        * base.terminal_value_weight(scenario)
        * best_state_value,
    )


def policy_rows(
    policies: list[str],
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    upper_bound: float,
    eval_seed: int,
) -> list[dict[str, object]]:
    dummy_model = sc.LinearModel([], [], [], [0.0])
    rows: list[dict[str, object]] = []
    for policy in policies:
        summary, _ = sc.simulate_policy(
            policy,
            loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            dummy_model,
            rollout_seed_offset=eval_seed,
        )
        profit = float(summary["profit"])
        rows.append(
            {
                "policy": policy,
                "profit": f"{profit:.2f}",
                "retention_vs_relaxed_bound": f"{profit / upper_bound:.6f}"
                if upper_bound
                else "0.000000",
                "gap_to_relaxed_bound": f"{upper_bound - profit:.2f}",
                "accepted": summary["accepted"],
                "no_truck": summary["no_truck"],
                "infeasible": summary["infeasible"],
                "mean_latency_ms": summary["mean_latency_ms"],
            }
        )
    return rows


def load_term_rows(terms: list[LoadTerm], limit: int) -> list[dict[str, object]]:
    ranked = sorted(terms, key=lambda term: term.profit, reverse=True)
    rows: list[dict[str, object]] = []
    for term in ranked[:limit]:
        rows.append(
            {
                "load_id": term.load_id,
                "hour": f"{term.hour:.2f}",
                "origin_state": term.origin_state,
                "destination_state": term.destination_state,
                "profit": f"{term.profit:.2f}",
                "lower_bound_busy_hours": f"{term.lower_bound_busy_hours:.4f}",
                "fresh_truck_busy_hours": f"{term.fresh_truck_busy_hours:.4f}",
                "profit_per_lower_bound_busy_hour": (
                    f"{term.profit / max(term.lower_bound_busy_hours, 1e-9):.4f}"
                ),
            }
        )
    return rows


def write_report(
    path: Path,
    config_path: Path,
    scenario_key: str,
    scenario: base.Scenario,
    eval_seed: int,
    loads_seen: int,
    positive_profit_bound: float,
    fractional_truck_hour_bound: float,
    terminal_upper_bound: float,
    selected_bound: float,
    capacity_hours: float,
    elapsed_seconds: float,
    comparison_rows: list[dict[str, object]],
) -> None:
    comparison_table = [
        "| Policy | Profit | Retention vs Bound | Gap | Accepted | Infeasible | Mean Latency ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in comparison_rows:
        comparison_table.append(
            f"| `{row['policy']}` | {money(float(row['profit']))} | "
            f"{float(row['retention_vs_relaxed_bound']):.1%} | "
            f"{money(float(row['gap_to_relaxed_bound']))} | {row['accepted']} | "
            f"{row['infeasible']} | {float(row['mean_latency_ms']):.3f} |"
        )
    if not comparison_rows:
        comparison_table.append("| _Skipped_ | | | | | | |")

    content = f"""# FreightBidBench v0.3 Relaxed Hindsight Bound

## Configuration

- Scenario: `{scenario_key}` (`{scenario.name}`)
- Scenario config: `{config_path.relative_to(ROOT)}`
- Eval seed: `{eval_seed}`
- Realized loads: `{loads_seen}`
- Fleet size: `{scenario.fleet_size}`
- Relaxed truck-hour capacity: `{capacity_hours:.2f}`
- Runtime: `{elapsed_seconds:.2f}` seconds

## Relaxed Bounds

| Bound | Profit Ceiling |
| --- | ---: |
| Positive-profit relaxation | {money(positive_profit_bound + terminal_upper_bound)} |
| Fractional truck-hour relaxation | {money(fractional_truck_hour_bound + terminal_upper_bound)} |
| Terminal fleet-value add-on | {money(terminal_upper_bound)} |
| Selected reported bound | {money(selected_bound)} |

The selected bound is the minimum of the listed relaxations. It is an upper
bound because it ignores location, exact sequencing, and integrality while
preserving only relaxed profit and truck-hour capacity constraints.

## Policy Comparison

{chr(10).join(comparison_table)}

## Interpretation Rules

- Report this as a relaxed full-horizon ceiling, not as an achievable plan.
- Pair it with exact DP on small prefixes when presenting v0.3 results.
- If the gap is loose, report the looseness directly instead of tuning the
  relaxation until it resembles a policy.
"""
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run relaxed full-horizon upper bounds for FreightBidBench v0.3."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--eval-seed", type=int)
    parser.add_argument("--eval-load-limit", type=int)
    parser.add_argument("--top-load-terms", type=int, default=200)
    parser.add_argument("--skip-policy-comparison", action="store_true")
    parser.add_argument(
        "--policies",
        default=",".join(SIMPLE_POLICIES),
        help="Comma-separated policies for comparison. Use rollout_teacher sparingly.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def parse_policies(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.eval_load_limit is not None and args.eval_load_limit <= 0:
        raise SystemExit("--eval-load-limit must be positive")
    if args.top_load_terms < 0:
        raise SystemExit("--top-load-terms must be non-negative")

    start = time.perf_counter()
    config_path, config, scenarios = load_config(args.config)
    if args.scenario not in scenarios:
        raise SystemExit(
            f"--scenario must be one of: {', '.join(sorted(scenarios))}"
        )
    eval_seed = (
        args.eval_seed
        if args.eval_seed is not None
        else int(config["default_first_seed"]) + 1
    )
    scenario = scenarios[args.scenario]
    lanes = base.load_csv(base.LANES)
    loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    if args.eval_load_limit is not None:
        loads = loads[: args.eval_load_limit]
    starting_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)
    state_values = base.build_state_values(lanes, scenario)

    terms = positive_terms(loads)
    positive_profit_bound = sum(term.profit for term in terms)
    max_fresh_busy = max((term.fresh_truck_busy_hours for term in terms), default=0.0)
    capacity_hours = scenario.fleet_size * (scenario.horizon_hours + max_fresh_busy)
    fractional_bound = fractional_knapsack_profit(terms, capacity_hours)
    terminal_upper = terminal_value_upper_bound(scenario, state_values)
    positive_total = positive_profit_bound + terminal_upper
    fractional_total = fractional_bound + terminal_upper
    selected_bound = min(positive_total, fractional_total)
    elapsed_seconds = time.perf_counter() - start

    comparison_rows: list[dict[str, object]] = []
    if not args.skip_policy_comparison:
        comparison_rows = policy_rows(
            parse_policies(args.policies),
            loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            selected_bound,
            eval_seed,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = [
        {
            "scenario": args.scenario,
            "scenario_name": scenario.name,
            "scenario_config_path": str(config_path.relative_to(ROOT)),
            "eval_seed": eval_seed,
            "loads_seen": len(loads),
            "positive_load_terms": len(terms),
            "fleet_size": scenario.fleet_size,
            "capacity_hours": f"{capacity_hours:.4f}",
            "positive_profit_bound_without_terminal": f"{positive_profit_bound:.2f}",
            "fractional_truck_hour_bound_without_terminal": f"{fractional_bound:.2f}",
            "terminal_upper_bound": f"{terminal_upper:.2f}",
            "positive_profit_bound": f"{positive_total:.2f}",
            "fractional_truck_hour_bound": f"{fractional_total:.2f}",
            "selected_relaxed_bound": f"{selected_bound:.2f}",
            "elapsed_seconds": f"{elapsed_seconds:.4f}",
        }
    ]
    write_csv(args.output_dir / "relaxed_bound_summary.csv", summary_rows)
    write_csv(
        args.output_dir / "relaxed_bound_load_terms.csv",
        load_term_rows(terms, args.top_load_terms),
    )
    write_csv(args.output_dir / "relaxed_bound_policy_comparison.csv", comparison_rows)
    write_report(
        args.output_dir / "relaxed_bound_report.md",
        config_path,
        args.scenario,
        scenario,
        eval_seed,
        len(loads),
        positive_profit_bound,
        fractional_bound,
        terminal_upper,
        selected_bound,
        capacity_hours,
        elapsed_seconds,
        comparison_rows,
    )

    print(
        f"Wrote {args.output_dir / 'relaxed_bound_report.md'} "
        f"({money(selected_bound)} relaxed bound)"
    )


if __name__ == "__main__":
    main()
