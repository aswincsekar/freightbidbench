"""Fit an aggregated value-to-go table W(market, hour) for the dual policy.

Runs a backward Bellman recursion on the (market, hour) grid over a realized
load stream, with each load's reward netted by its converged Lagrangian dual
price. The result approximates the per-truck value-to-go of the Lagrangian
sub-MDP on an aggregated state (location, availability time), dropping HOS
clocks. The `dual_price_vf` policy branch scores decisions by
`profit - lambda_hat + W(dest, t_done) - W(origin, now)`.

Recursion, processed from the horizon backward:
    W(m, T) = omega * V(m)                                   (terminal value)
    W(m, t) = max( W(m, t+1),                                (wait)
                   max over loads at hour t from origin m of
                       fresh_profit - lambda_load + W(dest, ceil(t + tt)) )

Dependency-free. Usage mirrors fit_dual_prices.py:
    python3 scripts/fit_value_togo.py \
        --config configs/freightbidbench_v03_scenarios.json \
        --scenario tight --eval-seed 20260507 \
        --duals-csv benchmark_runs/lagrangian_bound_full_v6_warm/lagrangian_dual_prices.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "dual_value_togo.csv"


def load_duals(path: Path) -> dict[int, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            int(row["load_id"]): float(row["lambda"])
            for row in csv.DictReader(handle)
        }


def fit_value_togo(
    scenario: base.Scenario,
    loads: list[dict[str, object]],
    duals: dict[int, float],
    state_values: dict[str, float],
) -> dict[tuple[str, int], float]:
    horizon = int(scenario.horizon_hours)
    markets = sorted(
        {str(load["origin_state"]) for load in loads}
        | {str(load["destination_state"]) for load in loads}
        | set(state_values)
    )
    omega = base.terminal_value_weight(scenario)

    loads_by_hour: defaultdict[int, list[dict[str, object]]] = defaultdict(list)
    for load in loads:
        loads_by_hour[int(float(load["hour"]))].append(load)

    w: dict[tuple[str, int], float] = {
        (market, horizon): omega * state_values.get(market, 0.0)
        for market in markets
    }
    for hour in range(horizon - 1, -1, -1):
        for market in markets:
            best = w[(market, hour + 1)]
            for load in loads_by_hour.get(hour, []):
                if str(load["origin_state"]) != market:
                    continue
                lam = duals.get(int(load["load_id"]), 0.0)
                fresh_profit = float(load["price"]) - float(load["direct_cost"])
                done = min(
                    horizon, int(math.ceil(hour + float(load["travel_hours"])))
                )
                candidate = (
                    fresh_profit
                    - lam
                    + w[(str(load["destination_state"]), done)]
                )
                if candidate > best:
                    best = candidate
            w[(market, hour)] = best
    return w


def write_table(
    path: Path, scenario_name: str, w: dict[tuple[str, int], float]
) -> None:
    kept: list[dict[str, object]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            kept = [
                row for row in csv.DictReader(handle) if row["scenario"] != scenario_name
            ]
    fieldnames = ["scenario", "market", "hour", "value_togo"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
        for (market, hour), value in sorted(w.items()):
            writer.writerow(
                {
                    "scenario": scenario_name,
                    "market": market,
                    "hour": hour,
                    "value_togo": f"{value:.2f}",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--eval-seed", type=int, required=True)
    parser.add_argument("--duals-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with (args.config if args.config.is_absolute() else ROOT / args.config).open(
        encoding="utf-8"
    ) as handle:
        config = json.load(handle)
    scenario = lag.scenario_from_config(config["scenarios"][args.scenario])

    lanes = base.load_csv(base.LANES)
    state_values = base.build_state_values(lanes, scenario)
    loads = sc.generate_loads_with_seed(lanes, scenario, args.eval_seed)
    duals = load_duals(
        args.duals_csv if args.duals_csv.is_absolute() else ROOT / args.duals_csv
    )

    w = fit_value_togo(scenario, loads, duals, state_values)
    write_table(
        args.output if args.output.is_absolute() else ROOT / args.output,
        scenario.name,
        w,
    )
    values = [v for (_, hour), v in w.items() if hour == 0]
    print(
        f"Fitted W(market, hour) for {scenario.name}: {len(w)} cells; "
        f"W(., 0) range ${min(values):,.0f} - ${max(values):,.0f}."
    )


if __name__ == "__main__":
    main()
