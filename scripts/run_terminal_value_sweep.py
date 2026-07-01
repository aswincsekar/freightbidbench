#!/usr/bin/env python3
"""Sweep v0.3 terminal fleet-value weights."""

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
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "v03_sweeps" / "terminal_value"


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_weights(value: str) -> list[float]:
    weights: list[float] = []
    for item in parse_csv(value):
        try:
            weight = float(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "weights must be comma-separated numbers"
            ) from exc
        weights.append(weight)
    if not weights:
        raise argparse.ArgumentTypeError("at least one weight is required")
    return weights


def label(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p")


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


def configured_scenarios(
    config: dict[str, object],
    scenario_keys: list[str],
    weight: float,
) -> dict[str, object]:
    updated = copy.deepcopy(config)
    scenarios = dict(updated["scenarios"])
    missing = sorted(set(scenario_keys) - set(scenarios))
    if missing:
        raise SystemExit(f"unknown scenario(s): {', '.join(missing)}")
    for scenario_key in scenario_keys:
        scenario = dict(scenarios[scenario_key])
        scenario["terminal_value_weight"] = weight
        scenarios[scenario_key] = scenario
    updated["scenarios"] = scenarios
    return updated


def read_summary(run_dir: Path) -> list[dict[str, str]]:
    with (run_dir / "freightbidbench_policy_summary.csv").open(
        newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def scenario_name(scenario_key: str) -> str:
    return f"freightbidbench_{scenario_key}_capacity"


def comparison_rows(
    weight: float,
    scenario_keys: list[str],
    summary_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows_by_key = {
        (row["scenario"], row["policy"], row.get("cascade_band_dollars", "")): row
        for row in summary_rows
    }
    rows: list[dict[str, object]] = []
    for scenario in scenario_keys:
        accept_row = rows_by_key.get((scenario_name(scenario), "accept_all_feasible", ""))
        rollout_row = rows_by_key.get((scenario_name(scenario), "rollout_teacher", ""))
        myopic_row = rows_by_key.get((scenario_name(scenario), "myopic_margin", ""))
        bid_price_row = rows_by_key.get((scenario_name(scenario), "bid_price", ""))
        if not accept_row or not rollout_row or not myopic_row or not bid_price_row:
            raise SystemExit(f"missing policy rows for scenario {scenario}")

        accept_profit = as_float(accept_row["mean_profit"])
        rollout_profit = as_float(rollout_row["mean_profit"])
        accept_retention = accept_profit / rollout_profit if rollout_profit else 0.0
        rows.append(
            {
                "terminal_value_weight": f"{weight:.6f}",
                "scenario": scenario,
                "accept_all_feasible_profit": f"{accept_profit:.2f}",
                "myopic_margin_profit": f"{as_float(myopic_row['mean_profit']):.2f}",
                "bid_price_profit": f"{as_float(bid_price_row['mean_profit']):.2f}",
                "rollout_teacher_profit": f"{rollout_profit:.2f}",
                "accept_all_feasible_retention_vs_rollout": f"{accept_retention:.6f}",
                "accept_all_feasible_retention_gap_pp": f"{(1.0 - accept_retention) * 100.0:.2f}",
                "accept_all_feasible_terminal_value": f"{as_float(accept_row.get('mean_terminal_fleet_value', 0)):.2f}",
                "rollout_terminal_value": f"{as_float(rollout_row.get('mean_terminal_fleet_value', 0)):.2f}",
                "gate_met": accept_retention <= 0.95,
            }
        )
    return rows


def run_weight(
    config: dict[str, object],
    weight: float,
    args: argparse.Namespace,
    scenario_keys: list[str],
) -> list[dict[str, object]]:
    run_dir = args.output_dir / f"weight_{label(weight)}"
    config_dir = args.output_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"freightbidbench_v03_terminal_{label(weight)}.json"
    config_path.write_text(
        json.dumps(configured_scenarios(config, scenario_keys, weight), indent=2),
        encoding="utf-8",
    )

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
    return comparison_rows(weight, scenario_keys, read_summary(run_dir))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep v0.3 terminal fleet-value weights and summarize A2 gate."
    )
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--preset", default="smoke")
    parser.add_argument("--scenarios", default="tight,scarce")
    parser.add_argument("--weights", type=parse_weights, default=parse_weights("0,0.25,0.5,1.0"))
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
    summary_path = args.output_dir / "terminal_value_sweep.csv"
    for weight in args.weights:
        print(f"Running terminal value weight {weight:.6f}", flush=True)
        all_rows.extend(run_weight(config, weight, args, scenario_keys))
        write_csv(summary_path, all_rows)

    print(f"Wrote {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
