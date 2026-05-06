#!/usr/bin/env python3
"""Run a first opportunity-cost sanity check for FreightBidBench.

This is deliberately not the final simulator. It tests whether the public-
calibrated seed lanes can produce decision cases where immediate-margin bidding
disagrees with a simple downstream opportunity-cost rule.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPED_LANES = ROOT / "data" / "processed" / "v1_usda_faf_mapped_lanes.csv"
IMBALANCE = ROOT / "data" / "processed" / "faf_state_imbalance_2024.csv"
SAMPLES_OUT = ROOT / "data" / "processed" / "sanity_load_samples.csv"
REPORT_OUT = ROOT / "reports" / "opportunity_cost_sanity_report.md"

SEED = 20260505
NUM_LOADS = 5000
BASE_COST_PER_MILE = 2.75
FIXED_LOAD_COST = 250.0
VALUE_SCALE_DOLLARS = 2500.0


def as_float(value: str) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_state_values() -> dict[str, float]:
    rows = load_csv(IMBALANCE)
    imbalances = {
        row["state"]: as_float(row["net_outbound_tons_2024"]) for row in rows
    }
    max_abs = max(abs(value) for value in imbalances.values())
    return {
        state: (imbalance / max_abs) * VALUE_SCALE_DOLLARS
        for state, imbalance in imbalances.items()
    }


def lane_distance_miles(row: dict[str, str]) -> float:
    tons = as_float(row["faf_tons_2024"])
    tmiles = as_float(row["faf_tmiles_2024"])
    if tons <= 0 or tmiles <= 0:
        return 1000.0
    return 1000.0 * tmiles / tons


def weighted_choice(rng: random.Random, rows: list[dict[str, str]]) -> dict[str, str]:
    total = sum(as_float(row["faf_tons_2024"]) for row in rows)
    target = rng.random() * total
    running = 0.0
    for row in rows:
        running += as_float(row["faf_tons_2024"])
        if running >= target:
            return row
    return rows[-1]


def simulate() -> list[dict[str, str]]:
    rng = random.Random(SEED)
    lanes = load_csv(MAPPED_LANES)
    state_values = build_state_values()
    rows: list[dict[str, str]] = []

    for load_id in range(NUM_LOADS):
        lane = weighted_choice(rng, lanes)
        distance = lane_distance_miles(lane)
        rate_midpoint = as_float(lane["rate_midpoint"])
        scarcity = as_float(lane["scarcity_multiplier"])
        price_noise = min(1.30, max(0.70, rng.gauss(1.0, 0.08)))
        price = rate_midpoint * price_noise * (0.9 + 0.1 * scarcity)
        cost = distance * BASE_COST_PER_MILE + FIXED_LOAD_COST
        immediate_margin = price - cost

        origin_value = state_values.get(lane["origin_state"], 0.0)
        destination_value = state_values.get(lane["destination_state"], 0.0)
        opportunity_delta = destination_value - origin_value
        value_adjusted_margin = immediate_margin + opportunity_delta

        myopic_accept = immediate_margin >= 0
        value_accept = value_adjusted_margin >= 0
        if myopic_accept and not value_accept:
            case_type = "trap_accept"
        elif not myopic_accept and value_accept:
            case_type = "reposition_accept"
        elif myopic_accept and value_accept:
            case_type = "agree_accept"
        else:
            case_type = "agree_reject"

        rows.append(
            {
                "load_id": str(load_id),
                "origin_state": lane["origin_state"],
                "origin_name": lane["origin_name"],
                "destination_state": lane["destination_state"],
                "destination_name": lane["destination_name"],
                "destination_city": lane["destination_city"],
                "availability": lane["availability"],
                "distance_miles": f"{distance:.2f}",
                "price": f"{price:.2f}",
                "cost": f"{cost:.2f}",
                "immediate_margin": f"{immediate_margin:.2f}",
                "origin_value": f"{origin_value:.2f}",
                "destination_value": f"{destination_value:.2f}",
                "opportunity_delta": f"{opportunity_delta:.2f}",
                "value_adjusted_margin": f"{value_adjusted_margin:.2f}",
                "myopic_accept": str(myopic_accept),
                "value_accept": str(value_accept),
                "case_type": case_type,
            }
        )
    return rows


def summarize(rows: list[dict[str, str]]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["case_type"]] = counts.get(row["case_type"], 0) + 1

    myopic_objective = sum(
        as_float(row["value_adjusted_margin"])
        for row in rows
        if row["myopic_accept"] == "True"
    )
    value_objective = sum(
        as_float(row["value_adjusted_margin"])
        for row in rows
        if row["value_accept"] == "True"
    )
    myopic_direct_profit = sum(
        as_float(row["immediate_margin"]) for row in rows if row["myopic_accept"] == "True"
    )
    value_direct_profit = sum(
        as_float(row["immediate_margin"]) for row in rows if row["value_accept"] == "True"
    )
    return {
        "agree_accept": counts.get("agree_accept", 0),
        "agree_reject": counts.get("agree_reject", 0),
        "trap_accept": counts.get("trap_accept", 0),
        "reposition_accept": counts.get("reposition_accept", 0),
        "myopic_objective": myopic_objective,
        "value_objective": value_objective,
        "myopic_direct_profit": myopic_direct_profit,
        "value_direct_profit": value_direct_profit,
    }


def write_report(rows: list[dict[str, str]], summary: dict[str, float]) -> None:
    total = len(rows)
    disagreement = summary["trap_accept"] + summary["reposition_accept"]
    trap_examples = sorted(
        (row for row in rows if row["case_type"] == "trap_accept"),
        key=lambda row: as_float(row["value_adjusted_margin"]),
    )[:5]
    reposition_examples = sorted(
        (row for row in rows if row["case_type"] == "reposition_accept"),
        key=lambda row: as_float(row["value_adjusted_margin"]),
        reverse=True,
    )[:5]

    def format_examples(examples: list[dict[str, str]]) -> str:
        if not examples:
            return "- None found"
        return "\n".join(
            f"- {row['origin_name']} -> {row['destination_city']} ({row['destination_name']}): "
            f"margin ${float(row['immediate_margin']):,.0f}, "
            f"opp delta ${float(row['opportunity_delta']):,.0f}, "
            f"adjusted ${float(row['value_adjusted_margin']):,.0f}"
            for row in examples
        )

    content = f"""# Opportunity-Cost Sanity Report

## Configuration

- Random seed: {SEED}
- Simulated candidate loads: {NUM_LOADS:,}
- Base cost per loaded mile: ${BASE_COST_PER_MILE:.2f}
- Fixed load cost: ${FIXED_LOAD_COST:.0f}
- State opportunity-value scale: ${VALUE_SCALE_DOLLARS:.0f}
- Input lane table: `{MAPPED_LANES.relative_to(ROOT)}`

## Decision Disagreement

- Agree accept: {int(summary['agree_accept']):,}
- Agree reject: {int(summary['agree_reject']):,}
- Myopic accepts but value-aware rejects: {int(summary['trap_accept']):,}
- Myopic rejects but value-aware accepts: {int(summary['reposition_accept']):,}
- Total disagreement rate: {disagreement / total:.1%}

## Objective Comparison

This sanity objective is immediate margin plus downstream state opportunity value, not final closed-loop fleet profit.

- Myopic accepted-load objective: ${summary['myopic_objective']:,.0f}
- Value-aware accepted-load objective: ${summary['value_objective']:,.0f}
- Objective lift: ${summary['value_objective'] - summary['myopic_objective']:,.0f}
- Myopic direct accepted-load margin: ${summary['myopic_direct_profit']:,.0f}
- Value-aware direct accepted-load margin: ${summary['value_direct_profit']:,.0f}

## Trap Examples

These loads have positive direct margin but negative downstream-adjusted value.

{format_examples(trap_examples)}

## Repositioning Examples

These loads have negative direct margin but positive downstream-adjusted value.

{format_examples(reposition_examples)}

## Interpretation

The seed benchmark passes the first sanity check if both trap and repositioning cases appear in nontrivial numbers. That means the public-calibrated lane table can support experiments where myopic margin rules are measurably different from opportunity-cost-aware policies.

Next step: replace this one-shot value rule with a closed-loop simulator where accepted loads move trucks and future load arrivals are sampled over a horizon.
"""
    REPORT_OUT.write_text(content, encoding="utf-8")


def main() -> None:
    rows = simulate()
    rows_by_case = sorted(
        rows,
        key=lambda row: (
            row["case_type"],
            -abs(as_float(row["value_adjusted_margin"]) - as_float(row["immediate_margin"])),
        ),
    )
    write_csv(SAMPLES_OUT, rows_by_case)
    summary = summarize(rows)
    write_report(rows, summary)
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    print(f"Trap accepts: {int(summary['trap_accept']):,}")
    print(f"Reposition accepts: {int(summary['reposition_accept']):,}")
    print(f"Objective lift: {summary['value_objective'] - summary['myopic_objective']:,.0f}")


if __name__ == "__main__":
    main()
