#!/usr/bin/env python3
"""Generate dependency-free SVG figures for FreightBidBench outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


POLICY_ORDER = [
    "myopic_margin",
    "bid_price",
    "surrogate_linear",
    "cascade_surrogate_rollout",
    "rollout_teacher",
]

POLICY_LABELS = {
    "myopic_margin": "Myopic",
    "bid_price": "Bid price",
    "surrogate_linear": "Linear surrogate",
    "cascade_surrogate_rollout": "Cascade",
    "rollout_teacher": "Rollout",
}

SCENARIO_LABELS = {
    "freightbidbench_mild_capacity": "Mild",
    "freightbidbench_tight_capacity": "Tight",
    "freightbidbench_scarce_capacity": "Scarce",
}

COLORS = {
    "myopic_margin": "#64748b",
    "bid_price": "#0f766e",
    "surrogate_linear": "#b45309",
    "cascade_surrogate_rollout": "#2563eb",
    "rollout_teacher": "#7c3aed",
    "freightbidbench_mild_capacity": "#0f766e",
    "freightbidbench_tight_capacity": "#2563eb",
    "freightbidbench_scarce_capacity": "#b91c1c",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def as_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def svg_text(x: float, y: float, text: str, size: int = 12, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" fill="#111827">{text}</text>'
    )


def svg_line(x1: float, y1: float, x2: float, y2: float, color: str = "#94a3b8") -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="1"/>'
    )


def svg_rect(x: float, y: float, w: float, h: float, color: str) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="2" fill="{color}"/>'
    )


def write_svg(path: Path, width: int, height: int, parts: list[str]) -> None:
    content = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            *parts,
            "</svg>",
        ]
    )
    path.write_text(content, encoding="utf-8")


def representative_policy_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for row in rows:
        policy = row["policy"]
        band = as_float(row.get("cascade_band_dollars", ""))
        if policy != "cascade_surrogate_rollout" or abs(band - 500.0) < 1e-9:
            selected.append(row)
    return selected


def scenario_order(rows: list[dict[str, str]]) -> list[str]:
    scenarios = sorted({row["scenario"] for row in rows})
    preferred = [
        "freightbidbench_mild_capacity",
        "freightbidbench_tight_capacity",
        "freightbidbench_scarce_capacity",
    ]
    return [item for item in preferred if item in scenarios] + [
        item for item in scenarios if item not in preferred
    ]


def draw_profit_retention_bars(rows: list[dict[str, str]], out: Path) -> None:
    rows = representative_policy_rows(rows)
    scenarios = scenario_order(rows)
    by_key = {(row["scenario"], row["policy"]): row for row in rows}
    width, height = 1120, 620
    left, right, top, bottom = 80, 40, 70, 100
    chart_w = width - left - right
    chart_h = height - top - bottom
    parts = [
        svg_text(width / 2, 34, "Profit Retention by Scenario and Policy", 22, "middle"),
        svg_text(width / 2, 56, "Representative cascade band: +/- $500", 12, "middle"),
    ]
    for pct in [0.75, 0.85, 0.95, 1.05, 1.15]:
        y = top + chart_h * (1.20 - pct) / 0.50
        parts.append(svg_line(left, y, width - right, y, "#e5e7eb"))
        parts.append(svg_text(left - 10, y + 4, f"{pct:.0%}", 11, "end"))
    parts.append(svg_line(left, top, left, top + chart_h, "#475569"))
    parts.append(svg_line(left, top + chart_h, width - right, top + chart_h, "#475569"))

    group_w = chart_w / max(len(scenarios), 1)
    bar_w = min(28, group_w / 7)
    for s_idx, scenario in enumerate(scenarios):
        base_x = left + s_idx * group_w + group_w * 0.14
        for p_idx, policy in enumerate(POLICY_ORDER):
            row = by_key.get((scenario, policy))
            if not row:
                continue
            retention = as_float(row["mean_profit_retention_vs_rollout"])
            y = top + chart_h * (1.20 - retention) / 0.50
            h = top + chart_h - y
            x = base_x + p_idx * (bar_w + 8)
            parts.append(svg_rect(x, y, bar_w, h, COLORS[policy]))
        parts.append(
            svg_text(
                left + s_idx * group_w + group_w / 2,
                top + chart_h + 26,
                SCENARIO_LABELS.get(scenario, scenario),
                13,
                "middle",
            )
        )

    legend_x, legend_y = left, height - 42
    for idx, policy in enumerate(POLICY_ORDER):
        x = legend_x + idx * 190
        parts.append(svg_rect(x, legend_y - 12, 14, 14, COLORS[policy]))
        parts.append(svg_text(x + 20, legend_y, POLICY_LABELS[policy], 12))
    write_svg(out, width, height, parts)


def draw_frontier(
    rows: list[dict[str, str]],
    out: Path,
    x_key: str,
    x_label: str,
    title: str,
) -> None:
    scenarios = scenario_order(rows)
    width, height = 920, 600
    left, right, top, bottom = 82, 180, 72, 70
    chart_w = width - left - right
    chart_h = height - top - bottom
    x_values = [as_float(row[x_key]) for row in rows]
    y_values = [as_float(row["mean_profit_retention_vs_rollout"]) for row in rows]
    x_max = max(x_values) if x_values else 1.0
    x_max = max(x_max * 1.08, 1e-6)
    y_min = min(0.80, min(y_values) - 0.03 if y_values else 0.80)
    y_max = max(1.05, max(y_values) + 0.03 if y_values else 1.05)

    def x_scale(value: float) -> float:
        return left + chart_w * value / x_max

    def y_scale(value: float) -> float:
        return top + chart_h * (y_max - value) / (y_max - y_min)

    parts = [
        svg_text(width / 2, 34, title, 22, "middle"),
        svg_text(width / 2, height - 20, x_label, 13, "middle"),
        svg_text(24, top + chart_h / 2, "Profit retention vs rollout", 13, "middle"),
    ]
    for tick in range(6):
        y_value = y_min + tick * (y_max - y_min) / 5
        y = y_scale(y_value)
        parts.append(svg_line(left, y, left + chart_w, y, "#e5e7eb"))
        parts.append(svg_text(left - 10, y + 4, f"{y_value:.0%}", 11, "end"))
    for tick in range(6):
        x_value = tick * x_max / 5
        x = x_scale(x_value)
        parts.append(svg_line(x, top, x, top + chart_h, "#f1f5f9"))
        parts.append(svg_text(x, top + chart_h + 20, f"{x_value:.1f}", 11, "middle"))
    parts.append(svg_line(left, top, left, top + chart_h, "#475569"))
    parts.append(svg_line(left, top + chart_h, left + chart_w, top + chart_h, "#475569"))

    for s_idx, scenario in enumerate(scenarios):
        scenario_rows = [
            row for row in rows if row["scenario"] == scenario
        ]
        scenario_rows.sort(key=lambda row: as_float(row[x_key]))
        color = COLORS.get(scenario, "#2563eb")
        prev: tuple[float, float] | None = None
        for row in scenario_rows:
            x = x_scale(as_float(row[x_key]))
            y = y_scale(as_float(row["mean_profit_retention_vs_rollout"]))
            if prev is not None:
                parts.append(
                    f'<line x1="{prev[0]:.1f}" y1="{prev[1]:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
                    f'stroke="{color}" stroke-width="2.5"/>'
                )
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
            prev = (x, y)
        lx, ly = width - right + 40, top + 28 + s_idx * 26
        parts.append(svg_rect(lx, ly - 12, 14, 14, color))
        parts.append(svg_text(lx + 20, ly, SCENARIO_LABELS.get(scenario, scenario), 12))

    write_svg(out, width, height, parts)


def draw_feasibility_bars(rows: list[dict[str, str]], out: Path) -> None:
    rows = representative_policy_rows(rows)
    scenarios = scenario_order(rows)
    by_key = {(row["scenario"], row["policy"]): row for row in rows}
    width, height = 1120, 620
    left, right, top, bottom = 80, 40, 70, 100
    chart_w = width - left - right
    chart_h = height - top - bottom
    values = [as_float(row.get("mean_infeasible", 0)) for row in rows]
    y_max = max(values) * 1.15 if values else 1.0
    y_max = max(y_max, 1.0)
    parts = [
        svg_text(width / 2, 34, "Infeasible Accept Attempts", 22, "middle"),
        svg_text(width / 2, 56, "Representative cascade band: +/- $500", 12, "middle"),
    ]
    for tick in range(6):
        value = tick * y_max / 5
        y = top + chart_h * (1 - value / y_max)
        parts.append(svg_line(left, y, width - right, y, "#e5e7eb"))
        parts.append(svg_text(left - 10, y + 4, f"{value:.0f}", 11, "end"))
    parts.append(svg_line(left, top, left, top + chart_h, "#475569"))
    parts.append(svg_line(left, top + chart_h, width - right, top + chart_h, "#475569"))

    group_w = chart_w / max(len(scenarios), 1)
    bar_w = min(28, group_w / 7)
    for s_idx, scenario in enumerate(scenarios):
        base_x = left + s_idx * group_w + group_w * 0.14
        for p_idx, policy in enumerate(POLICY_ORDER):
            row = by_key.get((scenario, policy))
            if not row:
                continue
            value = as_float(row.get("mean_infeasible", 0))
            h = chart_h * value / y_max
            x = base_x + p_idx * (bar_w + 8)
            y = top + chart_h - h
            parts.append(svg_rect(x, y, bar_w, h, COLORS[policy]))
        parts.append(
            svg_text(
                left + s_idx * group_w + group_w / 2,
                top + chart_h + 26,
                SCENARIO_LABELS.get(scenario, scenario),
                13,
                "middle",
            )
        )
    legend_x, legend_y = left, height - 42
    for idx, policy in enumerate(POLICY_ORDER):
        x = legend_x + idx * 190
        parts.append(svg_rect(x, legend_y - 12, 14, 14, COLORS[policy]))
        parts.append(svg_text(x + 20, legend_y, POLICY_LABELS[policy], 12))
    write_svg(out, width, height, parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot FreightBidBench benchmark outputs.")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=True,
        help="Directory containing freightbidbench_policy_summary.csv and freightbidbench_frontier_summary.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Figure output directory. Defaults to <run-dir>/figures.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_dir = args.run_dir
    output_dir = args.output_dir or run_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    policy_rows = load_csv(run_dir / "freightbidbench_policy_summary.csv")
    frontier_rows = load_csv(run_dir / "freightbidbench_frontier_summary.csv")

    draw_profit_retention_bars(
        policy_rows, output_dir / "profit_retention_by_policy.svg"
    )
    draw_frontier(
        frontier_rows,
        output_dir / "latency_profit_frontier.svg",
        "mean_latency_ms",
        "Mean latency (ms)",
        "Latency-Profit Frontier",
    )
    draw_frontier(
        frontier_rows,
        output_dir / "rollout_share_profit_frontier.svg",
        "mean_rollout_stage_share",
        "Rollout-call share",
        "Rollout Share-Profit Frontier",
    )
    draw_feasibility_bars(policy_rows, output_dir / "infeasible_accepts_by_policy.svg")
    print(f"Wrote figures to {output_dir}")


if __name__ == "__main__":
    main()
