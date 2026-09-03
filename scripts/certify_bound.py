"""Certify a finished dual solve with the sound per-truck evaluator.

The subgradient search may use any solver to choose duals (Theorem 1
holds for every lambda); the certificate is L(lambda) evaluated by the
sound bucketed solver at the search's incumbent duals. This script
reconstructs the instance recorded in a solve directory, reads its
incumbent duals (lagrangian_best_duals_checkpoint.csv), evaluates the
sound bound once, and writes sound_bound_summary.csv beside the
original summary. It never modifies the original artifacts.

Usage:
    python3 scripts/certify_bound.py --solve-dir benchmark_runs/v041_fix/lagrangian_tight --workers 4
"""

from __future__ import annotations

import argparse
import csv
import multiprocessing
import platform
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

SUMMARY = "lagrangian_bound_summary.csv"
REPORT = "lagrangian_bound_report.md"
INCUMBENT = "lagrangian_best_duals_checkpoint.csv"
OUTPUT = "sound_bound_summary.csv"


def config_path_from_report(report: Path) -> Path:
    text = report.read_text(encoding="utf-8")
    match = re.search(r"Scenario config: `([^`]+)`", text)
    if not match:
        raise SystemExit(f"no scenario config recorded in {report}")
    return ROOT / match.group(1)


def certify(solve_dir: Path, workers: int, mode: str) -> dict[str, object]:
    summary = next(csv.DictReader((solve_dir / SUMMARY).open(encoding="utf-8")))
    config_path = config_path_from_report(solve_dir / REPORT)
    _, config, scenarios = lag.load_config(config_path)
    scenario_key = summary["scenario"]
    scenario = scenarios[scenario_key]
    eval_seed = int(summary["eval_seed"])

    lanes = base.load_csv(base.LANES)
    loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    if len(loads) != int(summary["loads_seen"]):
        raise SystemExit(
            f"regenerated {len(loads)} loads but the solve saw "
            f"{summary['loads_seen']}; instance mismatch"
        )
    initial_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)
    state_values = base.build_state_values(lanes, scenario)
    terminal_weight = base.terminal_value_weight(scenario)
    duals = lag.load_initial_duals_from_csv(solve_dir / INCUMBENT, loads)

    start = time.perf_counter()
    sorted_loads = sorted(loads, key=lambda load: float(load["hour"]))
    if workers > 1:
        with multiprocessing.Pool(
            workers,
            initializer=lag._pool_init,
            initargs=(sorted_loads, terminal_weight, state_values, mode),
        ) as pool:
            evaluation = lag.evaluate_lagrangian(
                initial_fleet, loads, duals, terminal_weight, state_values,
                pool=pool, mode=mode,
            )
    else:
        evaluation = lag.evaluate_lagrangian(
            initial_fleet, loads, duals, terminal_weight, state_values, mode=mode
        )
    elapsed = time.perf_counter() - start
    fleet_evaluated = sum(len(trucks) for trucks in initial_fleet.values())
    return {
        "scenario": scenario_key,
        "eval_seed": eval_seed,
        "loads_seen": len(loads),
        "fleet_size_evaluated": fleet_evaluated,
        "solver_mode": mode,
        "duals_source": INCUMBENT,
        "search_best_bound": float(summary["best_bound"]),
        "sound_bound": round(evaluation.bound, 2),
        "sound_minus_search_pct": round(
            100 * (evaluation.bound - float(summary["best_bound"]))
            / float(summary["best_bound"]),
            4,
        ),
        "elapsed_seconds": round(elapsed, 2),
        "workers": workers,
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solve-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--mode", choices=lag.SOLVER_MODES, default="sound",
        help="solver mode for the evaluation (default sound)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-evaluate even if sound_bound_summary.csv exists",
    )
    args = parser.parse_args()
    solve_dir = args.solve_dir if args.solve_dir.is_absolute() else ROOT / args.solve_dir
    out = solve_dir / OUTPUT
    if out.exists() and not args.force:
        print(f"skip (exists): {out}")
        return
    row = certify(solve_dir, args.workers, args.mode)
    lag.write_csv(out, [row])
    print(
        f"{row['scenario']} {row['eval_seed']}: search {row['search_best_bound']:.2f}"
        f" -> sound {row['sound_bound']:.2f} ({row['sound_minus_search_pct']:+.4f}%)"
        f" in {row['elapsed_seconds']:.0f}s"
    )


if __name__ == "__main__":
    main()
