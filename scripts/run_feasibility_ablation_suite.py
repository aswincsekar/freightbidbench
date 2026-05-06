#!/usr/bin/env python3
"""Run local FreightBidBench feasibility ablations.

This helper is intentionally a thin wrapper around the public benchmark CLI.
Each variant writes a normal FreightBidBench run directory plus a manifest.
The wrapper then combines policy summaries so the ablation effect is easy to
inspect without manually opening every subdirectory.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "feasibility_ablations"

VARIANTS = [
    ("full", []),
    ("no_pickup_reach", ["--disable-pickup-reach"]),
    ("no_time_windows", ["--disable-time-windows"]),
    ("no_hos", ["--disable-hos"]),
    ("no_yard_delays", ["--disable-yard-delays"]),
    (
        "minimal_feasibility",
        [
            "--disable-pickup-reach",
            "--disable-time-windows",
            "--disable-hos",
            "--disable-yard-delays",
        ],
    ),
]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def optional_arg(command: list[str], name: str, value: object | None) -> None:
    if value is not None:
        command.extend([name, str(value)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run FreightBidBench feasibility ablations locally."
    )
    parser.add_argument(
        "--preset",
        default="smoke",
        choices=["smoke", "standard", "paper"],
        help="Benchmark preset to use for each ablation variant.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Root directory for ablation variant outputs.",
    )
    parser.add_argument("--scenarios", help="Optional comma-separated scenario subset.")
    parser.add_argument("--seed-count", type=int, help="Optional seed-count override.")
    parser.add_argument("--label-limit", type=int, help="Optional rollout-label limit.")
    parser.add_argument("--eval-load-limit", type=int, help="Optional eval-load limit.")
    parser.add_argument("--cascade-bands", help="Optional comma-separated cascade bands.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    index_rows: list[dict[str, object]] = []
    combined_summary_rows: list[dict[str, object]] = []
    suite_start = time.perf_counter()

    for variant_name, flags in VARIANTS:
        variant_dir = output_dir / variant_name
        command = [
            sys.executable,
            "scripts/run_freightbidbench.py",
            "--preset",
            args.preset,
            "--output-dir",
            str(variant_dir),
            *flags,
        ]
        optional_arg(command, "--scenarios", args.scenarios)
        optional_arg(command, "--seed-count", args.seed_count)
        optional_arg(command, "--label-limit", args.label_limit)
        optional_arg(command, "--eval-load-limit", args.eval_load_limit)
        optional_arg(command, "--cascade-bands", args.cascade_bands)

        print(f"Running ablation {variant_name}: {' '.join(command)}", flush=True)
        start = time.perf_counter()
        subprocess.run(command, cwd=ROOT, check=True)
        elapsed = time.perf_counter() - start

        manifest_path = variant_dir / "freightbidbench_manifest.json"
        summary_path = variant_dir / "freightbidbench_policy_summary.csv"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        disabled = ",".join(
            manifest["feasibility_layer"].get("disabled_features", [])
        )

        index_rows.append(
            {
                "ablation": variant_name,
                "disabled_features": disabled,
                "elapsed_seconds": f"{elapsed:.2f}",
                "manifest": str(manifest_path.relative_to(ROOT)),
                "policy_summary": str(summary_path.relative_to(ROOT)),
                "report": str((variant_dir / "freightbidbench_report.md").relative_to(ROOT)),
            }
        )

        for row in read_csv(summary_path):
            combined_summary_rows.append(
                {
                    "ablation": variant_name,
                    "disabled_features": disabled,
                    **row,
                }
            )

    index_path = output_dir / "feasibility_ablation_index.csv"
    summary_path = output_dir / "feasibility_ablation_policy_summary.csv"
    write_csv(index_path, index_rows)
    write_csv(summary_path, combined_summary_rows)

    print(f"Wrote {index_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Total ablation runtime: {time.perf_counter() - suite_start:.2f} seconds")


if __name__ == "__main__":
    main()
