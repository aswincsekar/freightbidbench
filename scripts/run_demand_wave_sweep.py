#!/usr/bin/env python3
"""Sweep v0.3 temporal demand-wave amplitudes."""

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
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "v03_sweeps" / "demand_waves"
SIMPLE_POLICIES = ["accept_all_feasible", "myopic_margin", "bid_price"]


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_amplitudes(value: str) -> list[float]:
    amplitudes: list[float] = []
    for item in parse_csv(value):
        try:
            amplitude = float(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "amplitudes must be comma-separated numbers"
            ) from exc
        if amplitude < 0.0 or amplitude >= 1.0:
            raise argparse.ArgumentTypeError("amplitudes must satisfy 0 <= a < 1")
        amplitudes.append(amplitude)
    if not amplitudes:
        raise argparse.ArgumentTypeError("at least one amplitude is required")
    return amplitudes


def label(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", "p")


def as_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def wave_schedule(amplitude: float, mode: str = "market") -> dict[str, object] | None:
    if amplitude == 0.0:
        return None
    low = max(0.05, 1.0 - amplitude)
    high = 1.0 + amplitude
    if mode == "global":
        return {
            "type": "hour_of_day_piecewise",
            "period_hours": 24,
            "default_multiplier": 1.0,
            "segments": [
                {"start_hour": 0, "end_hour": 6, "multiplier": low},
                {"start_hour": 6, "end_hour": 12, "multiplier": high},
                {"start_hour": 12, "end_hour": 18, "multiplier": low},
                {"start_hour": 18, "end_hour": 24, "multiplier": high},
            ],
        }
    if mode == "market":
        return {
            "type": "market_origin_destination_piecewise",
            "period_hours": 24,
            "default_multiplier": 1.0,
            "market_state": "48",
            "segments": [
                {
                    "start_hour": 0,
                    "end_hour": 12,
                    "multiplier": 1.0,
                    "origin_state_multipliers": {"48": low},
                    "destination_state_multipliers": {"48": high},
                },
                {
                    "start_hour": 12,
                    "end_hour": 24,
                    "multiplier": 1.0,
                    "origin_state_multipliers": {"48": high},
                    "destination_state_multipliers": {"48": low},
                },
            ],
        }
    if mode == "combined":
        return {
            "type": "count_and_market_piecewise",
            "period_hours": 24,
            "default_multiplier": 1.0,
            "market_state": "48",
            "segments": [
                {
                    "start_hour": 0,
                    "end_hour": 6,
                    "multiplier": low,
                    "origin_state_multipliers": {"48": low},
                    "destination_state_multipliers": {"48": high},
                },
                {
                    "start_hour": 6,
                    "end_hour": 12,
                    "multiplier": high,
                    "origin_state_multipliers": {"48": high},
                    "destination_state_multipliers": {"48": low},
                },
                {
                    "start_hour": 12,
                    "end_hour": 18,
                    "multiplier": low,
                    "origin_state_multipliers": {"48": low},
                    "destination_state_multipliers": {"48": high},
                },
                {
                    "start_hour": 18,
                    "end_hour": 24,
                    "multiplier": high,
                    "origin_state_multipliers": {"48": high},
                    "destination_state_multipliers": {"48": low},
                },
            ],
        }
    if mode == "price":
        return {
            "type": "price_premium_piecewise",
            "period_hours": 24,
            "default_multiplier": 1.0,
            "default_price_multiplier": 1.0,
            "segments": [
                {"start_hour": 0, "end_hour": 8, "multiplier": 1.0, "price_multiplier": 1.0},
                {"start_hour": 8, "end_hour": 16, "multiplier": 1.0, "price_multiplier": high},
                {"start_hour": 16, "end_hour": 24, "multiplier": 1.0, "price_multiplier": 1.0},
            ],
        }
    raise ValueError(f"unknown demand wave mode: {mode}")


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
    amplitude: float,
    mode: str = "market",
) -> dict[str, object]:
    updated = copy.deepcopy(config)
    scenarios = dict(updated["scenarios"])
    missing = sorted(set(scenario_keys) - set(scenarios))
    if missing:
        raise SystemExit(f"unknown scenario(s): {', '.join(missing)}")
    schedule = wave_schedule(amplitude, mode=mode)
    for scenario_key in scenario_keys:
        scenario = dict(scenarios[scenario_key])
        scenario["demand_wave_schedule"] = schedule
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
    amplitude: float,
    scenario_keys: list[str],
    summary_rows: list[dict[str, str]],
    mode: str = "market",
) -> list[dict[str, object]]:
    rows_by_key = {
        (row["scenario"], row["policy"], row.get("cascade_band_dollars", "")): row
        for row in summary_rows
    }
    rows: list[dict[str, object]] = []
    for scenario in scenario_keys:
        rollout_row = rows_by_key.get((scenario_name(scenario), "rollout_teacher", ""))
        if not rollout_row:
            raise SystemExit(f"missing rollout row for scenario {scenario}")
        rollout_profit = as_float(rollout_row["mean_profit"])

        simple_rows = []
        for policy in SIMPLE_POLICIES:
            row = rows_by_key.get((scenario_name(scenario), policy, ""))
            if not row:
                raise SystemExit(f"missing {policy} row for scenario {scenario}")
            profit = as_float(row["mean_profit"])
            simple_rows.append((policy, profit, profit / rollout_profit if rollout_profit else 0.0))
        best_policy, best_profit, best_retention = max(
            simple_rows,
            key=lambda item: item[1],
        )
        rows.append(
            {
                "wave_mode": mode,
                "wave_amplitude": f"{amplitude:.6f}",
                "scenario": scenario,
                "rollout_teacher_profit": f"{rollout_profit:.2f}",
                "best_simple_policy": best_policy,
                "best_simple_profit": f"{best_profit:.2f}",
                "best_simple_retention_vs_rollout": f"{best_retention:.6f}",
                "best_simple_gap_pp": f"{(1.0 - best_retention) * 100.0:.2f}",
                "gate_met": best_retention <= 0.90,
            }
        )
    return rows


def run_amplitude(
    config: dict[str, object],
    amplitude: float,
    args: argparse.Namespace,
    scenario_keys: list[str],
) -> list[dict[str, object]]:
    run_dir = args.output_dir / f"{args.mode}_amplitude_{label(amplitude)}"
    config_dir = args.output_dir / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"freightbidbench_v03_wave_{args.mode}_{label(amplitude)}.json"
    config_path.write_text(
        json.dumps(
            configured_scenarios(config, scenario_keys, amplitude, mode=args.mode),
            indent=2,
        ),
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
    return comparison_rows(amplitude, scenario_keys, read_summary(run_dir), mode=args.mode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep v0.3 temporal demand-wave amplitudes and summarize A3 gate."
    )
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--preset", default="smoke")
    parser.add_argument("--scenarios", default="tight,scarce")
    parser.add_argument(
        "--mode",
        choices=["market", "global", "combined", "price"],
        default="market",
    )
    parser.add_argument("--amplitudes", type=parse_amplitudes, default=parse_amplitudes("0,0.25,0.5,0.75"))
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
    summary_path = args.output_dir / "demand_wave_sweep.csv"
    for amplitude in args.amplitudes:
        print(
            f"Running {args.mode} demand wave amplitude {amplitude:.6f}",
            flush=True,
        )
        all_rows.extend(run_amplitude(config, amplitude, args, scenario_keys))
        write_csv(summary_path, all_rows)

    print(f"Wrote {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
