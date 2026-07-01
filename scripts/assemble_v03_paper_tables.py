#!/usr/bin/env python3
"""Assemble FreightBidBench v0.3 paper table drafts from run artifacts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "paper_v03"
SCENARIO_LABELS = {
    "freightbidbench_mild_capacity": "mild",
    "freightbidbench_tight_capacity": "tight",
    "freightbidbench_scarce_capacity": "scarce",
    "mild": "mild",
    "tight": "tight",
    "scarce": "scarce",
}
SIMPLE_POLICIES = {"accept_all_feasible", "myopic_margin", "bid_price"}
SCENARIO_ORDER = [
    "freightbidbench_mild_capacity",
    "freightbidbench_tight_capacity",
    "freightbidbench_scarce_capacity",
    "mild",
    "tight",
    "scarce",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def money(value: float) -> str:
    return f"${value:,.0f}"


def scenario_label(value: str) -> str:
    return SCENARIO_LABELS.get(value, value.replace("freightbidbench_", "").replace("_capacity", ""))


def scenario_sort_key(value: str) -> tuple[int, str]:
    if value in SCENARIO_ORDER:
        return SCENARIO_ORDER.index(value), value
    return len(SCENARIO_ORDER), value


def methods_rows(methods_dir: Path) -> list[dict[str, object]]:
    rows = load_csv(methods_dir / "freightbidbench_policy_summary.csv")
    by_scenario: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario"], []).append(row)

    output: list[dict[str, object]] = []
    for scenario, scenario_rows in sorted(
        by_scenario.items(), key=lambda item: scenario_sort_key(item[0])
    ):
        simple = [
            row for row in scenario_rows
            if row["policy"] in SIMPLE_POLICIES
        ]
        best_simple = max(
            simple,
            key=lambda row: as_float(row["mean_profit"]),
            default=None,
        )
        rollout = next(
            (row for row in scenario_rows if row["policy"] == "rollout_teacher"),
            None,
        )
        surrogate = next(
            (row for row in scenario_rows if row["policy"] == "surrogate_linear"),
            None,
        )
        cascade_rows = [
            row for row in scenario_rows if row["policy"] == "cascade_surrogate_rollout"
        ]
        best_low_latency = min(
            [
                row for row in cascade_rows
                if as_float(row["mean_profit_retention_vs_rollout"]) >= 0.98
            ],
            key=lambda row: as_float(row["mean_latency_ms"]),
            default=max(
                cascade_rows,
                key=lambda row: as_float(row["mean_profit_retention_vs_rollout"]),
                default=None,
            ),
        )
        if not best_simple or not rollout:
            continue
        output.append(
            {
                "scenario": scenario_label(scenario),
                "best_simple_policy": best_simple["policy"],
                "best_simple_profit": f"{as_float(best_simple['mean_profit']):.2f}",
                "best_simple_retention_vs_rollout": best_simple["mean_profit_retention_vs_rollout"],
                "surrogate_profit": f"{as_float(surrogate['mean_profit']):.2f}" if surrogate else "",
                "surrogate_retention_vs_rollout": surrogate["mean_profit_retention_vs_rollout"] if surrogate else "",
                "cascade_band_dollars": best_low_latency["cascade_band_dollars"] if best_low_latency else "",
                "cascade_profit": f"{as_float(best_low_latency['mean_profit']):.2f}" if best_low_latency else "",
                "cascade_retention_vs_rollout": best_low_latency["mean_profit_retention_vs_rollout"] if best_low_latency else "",
                "cascade_latency_ms": best_low_latency["mean_latency_ms"] if best_low_latency else "",
                "rollout_profit": f"{as_float(rollout['mean_profit']):.2f}",
                "rollout_latency_ms": rollout["mean_latency_ms"],
            }
        )
    return output


def relaxed_rows(relaxed_dirs: list[Path]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for run_dir in relaxed_dirs:
        [summary] = load_csv(run_dir / "relaxed_bound_summary.csv") or [None]
        if not summary:
            continue
        comparisons = load_csv(run_dir / "relaxed_bound_policy_comparison.csv")
        rollout = next((row for row in comparisons if row["policy"] == "rollout_teacher"), None)
        best_simple = max(
            [row for row in comparisons if row["policy"] in SIMPLE_POLICIES],
            key=lambda row: as_float(row["profit"]),
            default=None,
        )
        output.append(
            {
                "scenario": scenario_label(summary["scenario"]),
                "loads_seen": summary["loads_seen"],
                "selected_relaxed_bound": summary["selected_relaxed_bound"],
                "best_simple_policy": best_simple["policy"] if best_simple else "",
                "best_simple_retention_vs_bound": best_simple["retention_vs_relaxed_bound"] if best_simple else "",
                "rollout_retention_vs_bound": rollout["retention_vs_relaxed_bound"] if rollout else "",
            }
        )
    return output


def exact_rows(exact_dirs: list[Path]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for run_dir in exact_dirs:
        [summary] = load_csv(run_dir / "hindsight_bound_summary.csv") or [None]
        if not summary:
            continue
        comparisons = load_csv(run_dir / "hindsight_policy_comparison.csv")
        rollout = next((row for row in comparisons if row["policy"] == "rollout_teacher"), None)
        best_simple = max(
            [row for row in comparisons if row["policy"] in SIMPLE_POLICIES],
            key=lambda row: as_float(row["profit"]),
            default=None,
        )
        output.append(
            {
                "scenario": scenario_label(summary["scenario"]),
                "loads_seen": summary["loads_seen"],
                "hindsight_profit": summary["hindsight_profit"],
                "states_evaluated": summary["states_evaluated"],
                "best_simple_policy": best_simple["policy"] if best_simple else "",
                "best_simple_retention_vs_hindsight": best_simple["retention_vs_hindsight"] if best_simple else "",
                "rollout_retention_vs_hindsight": rollout["retention_vs_hindsight"] if rollout else "",
            }
        )
    return output


def write_markdown(
    path: Path,
    methods: list[dict[str, object]],
    relaxed: list[dict[str, object]],
    exact: list[dict[str, object]],
) -> None:
    lines = [
        "# FreightBidBench v0.3 Paper Tables",
        "",
        "Generated from existing benchmark artifacts. Values are draft table inputs, not prose-ready claims.",
        "",
        "## Methods Frontier",
        "",
        "| Scenario | Best Simple | Simple Retention | Surrogate Retention | Cascade Band | Cascade Retention | Cascade Latency | Rollout Latency |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in methods:
        lines.append(
            f"| `{row['scenario']}` | `{row['best_simple_policy']}` | "
            f"{as_float(row['best_simple_retention_vs_rollout']):.1%} | "
            f"{as_float(row['surrogate_retention_vs_rollout']):.1%} | "
            f"${as_float(row['cascade_band_dollars']):,.0f} | "
            f"{as_float(row['cascade_retention_vs_rollout']):.1%} | "
            f"{as_float(row['cascade_latency_ms']):.2f} ms | "
            f"{as_float(row['rollout_latency_ms']):.2f} ms |"
        )

    lines.extend(
        [
            "",
            "## Relaxed Full-Horizon Bound",
            "",
            "| Scenario | Loads | Relaxed Bound | Best Simple | Simple Retention | Rollout Retention |",
            "| --- | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for row in relaxed:
        lines.append(
            f"| `{row['scenario']}` | {row['loads_seen']} | "
            f"{money(as_float(row['selected_relaxed_bound']))} | "
            f"`{row['best_simple_policy']}` | "
            f"{as_float(row['best_simple_retention_vs_bound']):.1%} | "
            f"{as_float(row['rollout_retention_vs_bound']):.1%} |"
        )

    lines.extend(
        [
            "",
            "## Exact Small-Prefix Hindsight",
            "",
            "| Scenario | Loads | Hindsight | States | Best Simple | Simple Retention | Rollout Retention |",
            "| --- | ---: | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for row in exact:
        lines.append(
            f"| `{row['scenario']}` | {row['loads_seen']} | "
            f"{money(as_float(row['hindsight_profit']))} | "
            f"{int(as_float(row['states_evaluated'])):,} | "
            f"`{row['best_simple_policy']}` | "
            f"{as_float(row['best_simple_retention_vs_hindsight']):.1%} | "
            f"{as_float(row['rollout_retention_vs_hindsight']):.1%} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--methods-dir", type=Path, required=True)
    parser.add_argument("--relaxed-dir", type=Path, action="append", default=[])
    parser.add_argument("--exact-dir", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = build_parser().parse_args()
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    methods = methods_rows(resolve(args.methods_dir))
    relaxed = relaxed_rows([resolve(path) for path in args.relaxed_dir])
    exact = exact_rows([resolve(path) for path in args.exact_dir])

    write_csv(output_dir / "v03_methods_table.csv", methods)
    write_csv(output_dir / "v03_relaxed_bound_table.csv", relaxed)
    write_csv(output_dir / "v03_exact_hindsight_table.csv", exact)
    write_markdown(output_dir / "v03_paper_tables.md", methods, relaxed, exact)
    print(f"Wrote {output_dir / 'v03_paper_tables.md'}")


if __name__ == "__main__":
    main()
