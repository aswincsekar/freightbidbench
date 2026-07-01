#!/usr/bin/env python3
"""Sweep v0.3 service-failure penalties.

This script generates one config per penalty value, runs the benchmark, and
writes a compact comparison table for the A1 calibration gate.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "v03_sweeps" / "service_failure_penalty"
POLICIES_TO_COMPARE = ["accept_all_feasible", "myopic_margin", "bid_price", "rollout_teacher"]


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_penalties(value: str) -> list[float]:
    penalties: list[float] = []
    for item in parse_csv(value):
        try:
            penalty = float(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "penalties must be comma-separated numbers"
            ) from exc
        if penalty < 0:
            raise argparse.ArgumentTypeError("penalties must be non-negative")
        penalties.append(penalty)
    if not penalties:
        raise argparse.ArgumentTypeError("at least one penalty is required")
    return penalties


def money_label(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "p")


def as_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def configured_scenarios(config: dict[str, object], scenario_keys: list[str], penalty: float) -> dict[str, object]:
    updated = copy.deepcopy(config)
    scenarios = dict(updated["scenarios"])
    missing = sorted(set(scenario_keys) - set(scenarios))
    if missing:
        raise SystemExit(f"unknown scenario(s): {', '.join(missing)}")
    for scenario_key in scenario_keys:
        scenario = dict(scenarios[scenario_key])
        scenario["service_failure_penalty_dollars"] = penalty
        scenarios[scenario_key] = scenario
    updated["scenarios"] = scenarios
    return updated


def read_summary(run_dir: Path) -> list[dict[str, str]]:
    path = run_dir / "freightbidbench_policy_summary.csv"
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def comparison_rows(
    penalty: float,
    scenario_keys: list[str],
    summary_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows_by_key = {
        (row["scenario"], row["policy"], row.get("cascade_band_dollars", "")): row
        for row in summary_rows
    }
    rows: list[dict[str, object]] = []
    for scenario in scenario_keys:
        policy_rows = {
            policy: rows_by_key.get((f"freightbidbench_{scenario}_capacity", policy, ""))
            for policy in POLICIES_TO_COMPARE
        }
        accept_row = policy_rows["accept_all_feasible"]
        myopic_row = policy_rows["myopic_margin"]
        bid_price_row = policy_rows["bid_price"]
        rollout_row = policy_rows["rollout_teacher"]
        if not accept_row or not myopic_row or not bid_price_row:
            available = sorted({row["scenario"] for row in summary_rows})
            raise SystemExit(
                f"missing policy rows for scenario {scenario}; available scenarios: {available}"
            )

        accept_profit = as_float(accept_row["mean_profit"])
        myopic_profit = as_float(myopic_row["mean_profit"])
        bid_price_profit = as_float(bid_price_row["mean_profit"])
        rollout_profit = as_float(rollout_row["mean_profit"]) if rollout_row else 0.0
        myopic_penalty = as_float(myopic_row.get("mean_service_failure_penalty_cost", 0))
        bid_price_penalty = as_float(bid_price_row.get("mean_service_failure_penalty_cost", 0))
        rows.append(
            {
                "penalty_dollars": f"{penalty:.2f}",
                "scenario": scenario,
                "accept_all_feasible_profit": f"{accept_profit:.2f}",
                "myopic_margin_profit": f"{myopic_profit:.2f}",
                "bid_price_profit": f"{bid_price_profit:.2f}",
                "rollout_teacher_profit": f"{rollout_profit:.2f}",
                "myopic_gap_vs_accept_all_feasible": f"{myopic_profit - accept_profit:.2f}",
                "bid_price_gap_vs_accept_all_feasible": f"{bid_price_profit - accept_profit:.2f}",
                "myopic_service_failure_penalty_cost": f"{myopic_penalty:.2f}",
                "bid_price_service_failure_penalty_cost": f"{bid_price_penalty:.2f}",
                "ordering_met": myopic_profit < accept_profit and bid_price_profit < accept_profit,
            }
        )
    return rows


def run_penalty(
    config: dict[str, object],
    penalty: float,
    args: argparse.Namespace,
    scenario_keys: list[str],
) -> list[dict[str, object]]:
    label = money_label(penalty)
    run_dir = args.output_dir / f"penalty_{label}"
    config_dir = args.output_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"freightbidbench_v03_penalty_{label}.json"
    sweep_config = configured_scenarios(config, scenario_keys, penalty)
    config_path.write_text(json.dumps(sweep_config, indent=2), encoding="utf-8")

    command = [
        sys.executable,
        "scripts/run_freightbidbench.py",
        "--config",
        str(config_path.relative_to(ROOT)),
        "--preset",
        args.preset,
        "--scenarios",
        ",".join(scenario_keys),
        "--cascade-bands",
        args.cascade_bands,
        "--output-dir",
        str(run_dir),
    ]
    if args.seed_count is not None:
        command.extend(["--seed-count", str(args.seed_count)])
    if args.label_limit is not None:
        command.extend(["--label-limit", str(args.label_limit)])
    if args.eval_load_limit is not None:
        command.extend(["--eval-load-limit", str(args.eval_load_limit)])

    subprocess.run(command, cwd=ROOT, check=True)
    return comparison_rows(penalty, scenario_keys, read_summary(run_dir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep v0.3 service-failure penalty values and summarize A1 ordering."
    )
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--preset", default="smoke")
    parser.add_argument("--scenarios", default="tight,scarce")
    parser.add_argument("--penalties", type=parse_penalties, default=parse_penalties("0,25,50,100,250,500"))
    parser.add_argument("--seed-count", type=int)
    parser.add_argument("--label-limit", type=int)
    parser.add_argument("--eval-load-limit", type=int)
    parser.add_argument("--cascade-bands", default="0")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    base_config_path = args.base_config if args.base_config.is_absolute() else ROOT / args.base_config
    args.output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    config = json.loads(base_config_path.read_text(encoding="utf-8"))
    scenario_keys = parse_csv(args.scenarios)
    if not scenario_keys:
        raise SystemExit("--scenarios must include at least one scenario")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, object]] = []
    summary_path = args.output_dir / "service_failure_penalty_sweep.csv"
    for penalty in args.penalties:
        print(f"Running service-failure penalty ${penalty:,.2f}", flush=True)
        all_rows.extend(run_penalty(config, penalty, args, scenario_keys))
        write_csv(summary_path, all_rows)

    print(f"Wrote {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
