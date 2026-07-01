#!/usr/bin/env python3
"""Compute a limited realized-seed hindsight bound for FreightBidBench.

This is a v0.3 prototype diagnostic. It solves the exact accept/reject problem
for a truncated realized load stream, assuming the benchmark's current
deterministic truck-assignment rule after an accept decision. The result is a
small-instance ceiling for rollout and heuristic policies, not yet a full
paper-scale optimizer.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


DEFAULT_CONFIG_PATH = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
CONFIG_PATH = DEFAULT_CONFIG_PATH
BENCHMARK_CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "hindsight_bound_smoke"
DEFAULT_SCENARIO = "tight"
DEFAULT_MAX_LOADS = 16
DEFAULT_STATE_LIMIT = 200_000

TruckKey = tuple[str, float, float, float]
FleetKey = tuple[tuple[str, tuple[TruckKey, ...]], ...]


@dataclass(frozen=True)
class HindsightSolution:
    profit: float
    accepted_load_ids: tuple[int, ...]
    states_evaluated: int


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


SCENARIOS = {
    name: scenario_from_config(config)
    for name, config in BENCHMARK_CONFIG["scenarios"].items()
}


def load_config(config_path: Path) -> tuple[Path, dict[str, object], dict[str, base.Scenario]]:
    path = config_path if config_path.is_absolute() else ROOT / config_path
    config = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {
        name: scenario_from_config(scenario_config)
        for name, scenario_config in dict(config["scenarios"]).items()
    }
    return path, config, scenarios


def with_fleet_size(scenario: base.Scenario, fleet_size: int | None) -> base.Scenario:
    if fleet_size is None:
        return scenario
    return base.Scenario(
        scenario.name,
        horizon_hours=scenario.horizon_hours,
        loads_per_hour=scenario.loads_per_hour,
        fleet_size=fleet_size,
        base_cost_per_mile=scenario.base_cost_per_mile,
        fixed_load_cost=scenario.fixed_load_cost,
        value_scale_dollars=scenario.value_scale_dollars,
        service_failure_penalty_dollars=scenario.service_failure_penalty_dollars,
        terminal_value_weight=scenario.terminal_value_weight,
        demand_wave_schedule=scenario.demand_wave_schedule,
    )


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


def freeze_fleet(fleet: dict[str, list[object]]) -> FleetKey:
    frozen: list[tuple[str, tuple[TruckKey, ...]]] = []
    for state, trucks in fleet.items():
        truck_keys: list[TruckKey] = []
        for idx, raw_truck in enumerate(trucks):
            if hasattr(raw_truck, "available_time"):
                truck_id = str(getattr(raw_truck, "truck_id", f"{state}-{idx}"))
                available_time = float(getattr(raw_truck, "available_time"))
                drive_used_hours = float(getattr(raw_truck, "drive_used_hours", 0.0))
                duty_used_hours = float(getattr(raw_truck, "duty_used_hours", 0.0))
            else:
                truck = feas.coerce_truck(raw_truck, state, idx)
                truck_id = truck.truck_id
                available_time = truck.available_time
                drive_used_hours = truck.drive_used_hours
                duty_used_hours = truck.duty_used_hours
            truck_keys.append(
                (
                    truck_id,
                    round(available_time, 6),
                    round(drive_used_hours, 6),
                    round(duty_used_hours, 6),
                )
            )
        if truck_keys:
            frozen.append((state, tuple(sorted(truck_keys))))
    return tuple(sorted(frozen))


def thaw_fleet(fleet_key: FleetKey) -> dict[str, list[object]]:
    return {
        state: [
            feas.TruckState(
                truck_id,
                state,
                available_time,
                drive_used_hours,
                duty_used_hours,
            )
            for truck_id, available_time, drive_used_hours, duty_used_hours in trucks
        ]
        for state, trucks in fleet_key
    }


def exact_hindsight_bound(
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[object]],
    scenario: base.Scenario | None = None,
    state_values: dict[str, float] | None = None,
    state_limit: int = DEFAULT_STATE_LIMIT,
) -> HindsightSolution:
    """Return the exact truncated-stream accept/reject optimum.

    The search branches only on accept versus reject. If accept is chosen, the
    same feasibility and assignment routine used by the benchmark mutates the
    fleet. Infeasible accepts are dominated by reject because v0.2 applies no
    explicit service-failure penalty.
    """

    states_evaluated = 0

    @lru_cache(maxsize=None)
    def solve(index: int, fleet_key: FleetKey) -> tuple[float, tuple[int, ...]]:
        nonlocal states_evaluated
        states_evaluated += 1
        if states_evaluated > state_limit:
            raise RuntimeError(
                f"hindsight search exceeded --state-limit={state_limit:,}; "
                "reduce --max-loads or increase the limit"
            )
        if index >= len(loads):
            if scenario is not None and state_values is not None:
                terminal_value = base.terminal_fleet_value(
                    thaw_fleet(fleet_key), scenario, state_values
                )
                return terminal_value, ()
            return 0.0, ()

        reject_profit, reject_ids = solve(index + 1, fleet_key)
        best_profit = reject_profit
        best_ids = reject_ids

        load = loads[index]
        accept_fleet = thaw_fleet(fleet_key)
        assignment = feas.apply_accept(accept_fleet, load, float(load["hour"]))
        if assignment.accepted:
            future_profit, future_ids = solve(index + 1, freeze_fleet(accept_fleet))
            accept_profit = assignment.profit + future_profit
            if accept_profit > best_profit + 1e-9:
                best_profit = accept_profit
                best_ids = (int(load["load_id"]),) + future_ids

        return best_profit, best_ids

    profit, accepted_load_ids = solve(0, freeze_fleet(starting_fleet))
    return HindsightSolution(profit, accepted_load_ids, states_evaluated)


def decision_rows(
    loads: list[dict[str, object]],
    solution: HindsightSolution,
) -> list[dict[str, object]]:
    accepted = set(solution.accepted_load_ids)
    rows: list[dict[str, object]] = []
    for idx, load in enumerate(loads):
        margin = float(load["price"]) - float(load["direct_cost"])
        rows.append(
            {
                "decision_index": idx,
                "load_id": load["load_id"],
                "hour": load["hour"],
                "origin_state": load["origin_state"],
                "destination_state": load["destination_state"],
                "price": f"{float(load['price']):.2f}",
                "direct_cost": f"{float(load['direct_cost']):.2f}",
                "margin": f"{margin:.2f}",
                "hindsight_action": "accept"
                if int(load["load_id"]) in accepted
                else "reject",
            }
        )
    return rows


def policy_comparison_rows(
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    solution: HindsightSolution,
    eval_seed: int,
) -> list[dict[str, object]]:
    dummy_model = sc.LinearModel([], [], [], [0.0])
    rows: list[dict[str, object]] = []
    for policy in [
        "reject_all",
        "accept_all_feasible",
        "myopic_margin",
        "bid_price",
        "rollout_teacher",
    ]:
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
                "retention_vs_hindsight": f"{profit / solution.profit:.6f}"
                if solution.profit
                else "0.000000",
                "gap_to_hindsight": f"{solution.profit - profit:.2f}",
                "accepted": summary["accepted"],
                "rejected": summary["rejected"],
                "no_truck": summary["no_truck"],
                "infeasible": summary["infeasible"],
                "mean_latency_ms": summary["mean_latency_ms"],
            }
        )
    return rows


def write_report(
    path: Path,
    config_path: Path,
    scenario_key: str,
    scenario: base.Scenario,
    eval_seed: int,
    max_loads: int,
    solution: HindsightSolution,
    elapsed_seconds: float,
    comparison_rows: list[dict[str, object]],
) -> None:
    comparison_table = [
        "| Policy | Profit | Retention vs Hindsight | Gap | Accepted | Infeasible | Mean Latency ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in comparison_rows:
        comparison_table.append(
            f"| `{row['policy']}` | {money(float(row['profit']))} | "
            f"{float(row['retention_vs_hindsight']):.1%} | "
            f"{money(float(row['gap_to_hindsight']))} | {row['accepted']} | "
            f"{row['infeasible']} | {float(row['mean_latency_ms']):.3f} |"
        )
    if not comparison_rows:
        comparison_table.append("| _Skipped_ | | | | | | |")

    content = f"""# FreightBidBench v0.3 Hindsight-Bound Prototype

## Configuration

- Scenario: `{scenario_key}` (`{scenario.name}`)
- Scenario config: `{config_path.relative_to(ROOT)}`
- Eval seed: `{eval_seed}`
- Realized load prefix: `{max_loads}`
- Fleet size: `{scenario.fleet_size}`
- Feasibility layer: {", ".join(feas.enabled_feature_names())}
- Search states evaluated: `{solution.states_evaluated:,}`
- Runtime: `{elapsed_seconds:.2f}` seconds

## Exact Truncated-Stream Bound

The hindsight optimizer earned {money(solution.profit)} by accepting
{len(solution.accepted_load_ids)} of {max_loads} realized loads.

This is an exact accept/reject optimum for the truncated stream under the
current deterministic assignment rule. It is intended as a v0.3 diagnostic
ceiling for small realized streams, not as the final paper-scale bound.

## Policy Comparison

{chr(10).join(comparison_table)}

## Interpretation Rules

- Use this output to debug whether rollout and simple policies sit below a
  realized-seed ceiling on small instances.
- Do not report this as a production dispatch optimum.
- Increase `--max-loads` only after checking `--state-limit`, because the exact
  search can grow exponentially.
"""
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a limited exact hindsight-bound diagnostic for FreightBidBench v0.3."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Benchmark scenario config JSON. Defaults to the v0.3 development contract.",
    )
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO,
        help="Scenario key from the current benchmark config.",
    )
    parser.add_argument(
        "--eval-seed",
        type=int,
        help="Realized evaluation seed used to generate loads and initial fleet.",
    )
    parser.add_argument(
        "--max-loads",
        type=int,
        default=DEFAULT_MAX_LOADS,
        help="Prefix length of the realized stream to solve exactly.",
    )
    parser.add_argument(
        "--fleet-size",
        type=int,
        help="Optional smaller fleet size for exact-search stress tests.",
    )
    parser.add_argument(
        "--state-limit",
        type=int,
        default=DEFAULT_STATE_LIMIT,
        help="Maximum memoized search states before aborting.",
    )
    parser.add_argument(
        "--skip-policy-comparison",
        action="store_true",
        help="Only compute the hindsight bound; skip rollout and heuristic comparisons.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for hindsight CSVs and report.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config_path, config, scenarios = load_config(args.config)
    if args.scenario not in scenarios:
        raise SystemExit(
            f"--scenario must be one of: {', '.join(sorted(scenarios))}"
        )
    if args.max_loads <= 0:
        raise SystemExit("--max-loads must be positive")
    if args.fleet_size is not None and args.fleet_size <= 0:
        raise SystemExit("--fleet-size must be positive")
    if args.state_limit <= 0:
        raise SystemExit("--state-limit must be positive")

    eval_seed = (
        args.eval_seed
        if args.eval_seed is not None
        else int(config["default_first_seed"]) + 1
    )
    scenario = with_fleet_size(scenarios[args.scenario], args.fleet_size)
    lanes = base.load_csv(base.LANES)
    loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)[: args.max_loads]
    starting_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)
    state_values = base.build_state_values(lanes, scenario)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    solution = exact_hindsight_bound(
        loads,
        starting_fleet,
        scenario,
        state_values,
        args.state_limit,
    )
    elapsed_seconds = time.perf_counter() - start

    comparison_rows: list[dict[str, object]] = []
    if not args.skip_policy_comparison:
        comparison_rows = policy_comparison_rows(
            loads,
            starting_fleet,
            lanes,
            scenario,
            state_values,
            solution,
            eval_seed,
        )

    summary_rows = [
        {
            "scenario": args.scenario,
            "scenario_name": scenario.name,
            "scenario_config_path": str(config_path.relative_to(ROOT)),
            "eval_seed": eval_seed,
            "loads_seen": len(loads),
            "fleet_size": scenario.fleet_size,
            "hindsight_profit": f"{solution.profit:.2f}",
            "accepted": len(solution.accepted_load_ids),
            "rejected": len(loads) - len(solution.accepted_load_ids),
            "states_evaluated": solution.states_evaluated,
            "elapsed_seconds": f"{elapsed_seconds:.4f}",
        }
    ]

    write_csv(args.output_dir / "hindsight_bound_summary.csv", summary_rows)
    write_csv(args.output_dir / "hindsight_bound_decisions.csv", decision_rows(loads, solution))
    write_csv(args.output_dir / "hindsight_policy_comparison.csv", comparison_rows)
    write_report(
        args.output_dir / "hindsight_bound_report.md",
        config_path,
        args.scenario,
        scenario,
        eval_seed,
        len(loads),
        solution,
        elapsed_seconds,
        comparison_rows,
    )

    print(
        f"Wrote {args.output_dir / 'hindsight_bound_report.md'} "
        f"({money(solution.profit)}, {solution.states_evaluated:,} states)"
    )


if __name__ == "__main__":
    main()
