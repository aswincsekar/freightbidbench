"""Cross-fitted subcritical evaluation with subcriticality diagnostics.

Fixes two review findings against the original subcritical sweep:

1. Independence. Theorem 2 requires tables fitted on a training path
   independent of the evaluation path. The original sweep fit and
   evaluated on the same realization. Here every evaluation stream is
   scored under tables fitted from a *different* seed's dual solve
   (all ordered train/eval pairs), so the reported values are
   out-of-sample in the theorem's sense. Certificates still divide by
   the evaluation stream's own bound, as they must.

2. Non-tautological subcriticality evidence. The policy's feasibility
   guard pre-screens every load, so the runner's infeasible-accept
   counter is zero by construction. This driver reports the
   non-trivial quantities instead: how often the guard blocked a load
   at all, how often it blocked a load whose price-and-gradient score
   was otherwise accepting (the A1-relevant event), the minimum idle
   count at the arrival's origin market over the run, and the global
   minimum idle count across all markets.

Writes one CSV plus a JSON manifest (training identity, margin,
granularity, feasibility config) per cell.

Usage:
    FREIGHTBID_ACCEPT_MARGIN=50 python3 scripts/run_subcritical_crossfit.py \
        --output-dir benchmark_runs/trackb/subcritical_crossfit
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import certified_bound  # noqa: E402
import fit_dual_prices  # noqa: E402
import fit_value_togo  # noqa: E402
import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

CELLS = ("sub_x05", "sub_x1", "sub_x2")
SEEDS = (20260509, 20260511, 20260513)
# Corrected-solver directories (the invalid-solver originals are
# retained under benchmark_runs/trackb/subcritical for the audit).
SUB_DIR = ROOT / "benchmark_runs" / "v041_fix" / "subcritical"
CONFIG = ROOT / "configs" / "freightbidbench_v041_subcritical.json"


def best_bound(cell: str, seed: int) -> float:
    """Tightest sound-certified bound over the seed's base solve and
    warm extensions (each certified at its own incumbent duals)."""
    return certified_bound.best_certified_bound(
        [SUB_DIR / f"{cell}_{seed}{suffix}" for suffix in ("", "_ext", "_ext2")]
    )


def inject_tables(
    scenario: base.Scenario,
    lanes: list[dict[str, str]],
    train_seed: int,
    cell: str,
    state_values: dict[str, float],
) -> tuple[int, int]:
    """Fit lane-hour price and value tables from the training seed's
    duals and inject them into the policy module's caches."""
    duals_csv = SUB_DIR / f"{cell}_{train_seed}" / "lagrangian_dual_prices.csv"
    duals = fit_dual_prices.load_duals(duals_csv)
    train_loads = sc.generate_loads_with_seed(lanes, scenario, train_seed)

    price_rows = fit_dual_prices.fit_table(
        scenario, train_loads, duals, granularity="lane"
    )
    price_table = {
        (
            str(r["scenario"]),
            str(r["origin_state"]),
            str(r["dest_state"]),
            int(r["hour_bucket"]),
        ): float(r["lambda_mean"])
        for r in price_rows
    }
    w = fit_value_togo.fit_value_togo(scenario, train_loads, duals, state_values)
    value_table = {
        (scenario.name, market, hour): value
        for (market, hour), value in w.items()
    }
    sc._DUAL_PRICE_TABLE = price_table
    sc._VALUE_TOGO_TABLE = value_table
    return len(price_table), len(value_table)


def evaluate(
    scenario: base.Scenario,
    lanes: list[dict[str, str]],
    eval_seed: int,
    state_values: dict[str, float],
    margin: float,
) -> dict[str, object]:
    loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    fleet = base.initial_fleet(lanes, scenario)
    fleet = {
        market: [feas.TruckState(f"{market}-{i}", market, avail) for i, avail in enumerate(times)]
        for market, times in fleet.items()
    }

    profit = 0.0
    accepted = 0
    guard_fires = 0
    guard_score_positive = 0
    min_idle_origin = None
    min_idle_global = None
    empty_market_events = 0

    for idx, load in enumerate(loads):
        hour = float(load["hour"])
        origin = str(load["origin_state"])
        idle_origin = sum(
            1 for t in fleet.get(origin, []) if t.available_time <= hour
        )
        idle_global = min(
            (
                sum(1 for t in trucks if t.available_time <= hour)
                for trucks in fleet.values()
                if trucks
            ),
            default=0,
        )
        min_idle_origin = idle_origin if min_idle_origin is None else min(min_idle_origin, idle_origin)
        min_idle_global = idle_global if min_idle_global is None else min(min_idle_global, idle_global)
        if idle_origin == 0:
            empty_market_events += 1

        wants, score, stage = sc.choose_action(
            "dual_price_vf",
            load,
            fleet,
            lanes,
            scenario,
            state_values,
            None,
            idx,
        )
        if stage == "dual_feasibility_guard":
            guard_fires += 1
            fresh_profit = feas.realized_profit(load)[0]
            lam = sc.dual_price_lambda(
                scenario.name,
                origin,
                hour,
                dest=str(load["destination_state"]),
            )
            probe = feas.plan_schedule(
                feas.TruckState("probe", origin, hour), load, hour
            )
            done = (
                probe.final_available_time
                if probe.feasible
                else hour + float(load["travel_hours"])
            )
            g = sc.value_togo(
                scenario, str(load["destination_state"]), done
            ) - sc.value_togo(scenario, origin, done)
            if fresh_profit - lam + g >= -margin:
                guard_score_positive += 1
            continue
        if wants:
            assignment = feas.apply_accept(fleet, load, hour)
            if assignment.accepted:
                profit += assignment.profit
                accepted += 1

    profit += base.terminal_fleet_value(fleet, scenario, state_values)
    return {
        "profit": profit,
        "accepted": accepted,
        "guard_fires": guard_fires,
        "guard_score_positive": guard_score_positive,
        "min_idle_origin": min_idle_origin,
        "min_idle_global": min_idle_global,
        "empty_market_events": empty_market_events,
        "loads": len(loads),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "benchmark_runs" / "trackb" / "subcritical_crossfit",
    )
    parser.add_argument(
        "--pairs",
        choices=("cross", "in", "both"),
        default="cross",
        help="cross: train != eval (default, the theorem's sense); "
        "in: train == eval (regenerates the in-sample ladder numbers "
        "with the same instrumentation); both: all ordered pairs.",
    )
    args = parser.parse_args()
    out_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    margin = sc.ACCEPT_MARGIN
    config = json.loads(CONFIG.read_text())
    lanes = base.load_csv(base.LANES)

    rows: list[dict[str, object]] = []
    for cell in CELLS:
        scenario = lag.scenario_from_config(config["scenarios"][cell])
        state_values = base.build_state_values(lanes, scenario)
        for train_seed in SEEDS:
            n_price, n_value = inject_tables(
                scenario, lanes, train_seed, cell, state_values
            )
            for eval_seed in SEEDS:
                if args.pairs == "cross" and eval_seed == train_seed:
                    continue
                if args.pairs == "in" and eval_seed != train_seed:
                    continue
                result = evaluate(scenario, lanes, eval_seed, state_values, margin)
                bound = best_bound(cell, eval_seed)
                rows.append(
                    {
                        "cell": cell,
                        "train_seed": train_seed,
                        "eval_seed": eval_seed,
                        "certified_pct": f"{100 * float(result['profit']) / bound:.2f}",
                        **{k: (f"{v:.2f}" if isinstance(v, float) else v) for k, v in result.items()},
                        "bound": f"{bound:.2f}",
                    }
                )
                print(
                    f"{cell} train {train_seed} -> eval {eval_seed}: "
                    f"certified {rows[-1]['certified_pct']}%, guard fires "
                    f"{result['guard_fires']} (score-positive "
                    f"{result['guard_score_positive']}), min idle origin/global "
                    f"{result['min_idle_origin']}/{result['min_idle_global']}"
                )
        manifest = {
            "cell": cell,
            "config": str(CONFIG.relative_to(ROOT)),
            "benchmark_version": config.get("benchmark_version"),
            "granularity": "lane",
            "accept_margin": margin,
            "pairs": args.pairs,
            "train_seeds": list(SEEDS),
            "feasibility_config": "DEFAULT_CONFIG (all features enabled)",
            "price_table_rows": n_price,
            "value_table_cells": n_value,
            "table_source": "lagrangian_dual_prices.csv of the train seed's solve dir",
        }
        (out_dir / f"{cell}_manifest.json").write_text(
            json.dumps(manifest, indent=1) + "\n"
        )

    path = out_dir / "subcritical_crossfit.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
