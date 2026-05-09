#!/usr/bin/env python3
"""Compute paired-seed policy profit deltas for FreightBidBench runs."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


SCENARIO_ORDER = [
    "freightbidbench_mild_capacity",
    "freightbidbench_tight_capacity",
    "freightbidbench_scarce_capacity",
]

SCENARIO_LABELS = {
    "freightbidbench_mild_capacity": "mild",
    "freightbidbench_tight_capacity": "tight",
    "freightbidbench_scarce_capacity": "scarce",
}

POLICY_ORDER = [
    "accept_all_feasible",
    "myopic_margin",
    "bid_price",
    "surrogate_linear",
    "cascade_surrogate_rollout",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def as_float(value: str) -> float:
    if not value:
        return 0.0
    return float(value)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    index = int(pct * (len(values) - 1))
    return values[index]


def bootstrap_ci(deltas: list[float], samples: int, rng: random.Random) -> tuple[float, float]:
    if not deltas:
        return 0.0, 0.0
    n = len(deltas)
    means: list[float] = []
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            total += deltas[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    return percentile(means, 0.025), percentile(means, 0.975)


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def policy_label(policy: str, cascade_band: float) -> str:
    if policy == "accept_all_feasible":
        return "Accept all feasible"
    if policy == "myopic_margin":
        return "Myopic"
    if policy == "bid_price":
        return "Bid price"
    if policy == "surrogate_linear":
        return "Linear surrogate"
    if policy == "cascade_surrogate_rollout":
        return f"Cascade +/- ${cascade_band:,.0f}"
    return policy


def summarize(run_dir: Path, cascade_band: float, samples: int, seed: int) -> list[dict[str, str]]:
    rows = load_csv(run_dir / "freightbidbench_policy_runs.csv")
    selected: dict[tuple[str, str, str, str], float] = {}
    seed_pairs_by_scenario: dict[str, set[tuple[str, str]]] = {}

    for row in rows:
        policy = row["policy"]
        if policy == "cascade_surrogate_rollout":
            if abs(as_float(row.get("cascade_band_dollars", "")) - cascade_band) > 1e-9:
                continue
        elif policy not in {*POLICY_ORDER, "rollout_teacher"}:
            continue

        scenario = row["scenario"]
        train_seed = row["train_seed"]
        eval_seed = row["eval_seed"]
        seed_pairs_by_scenario.setdefault(scenario, set()).add((train_seed, eval_seed))
        selected[(scenario, train_seed, eval_seed, policy)] = as_float(row["profit"])

    rng = random.Random(seed)
    output: list[dict[str, str]] = []
    scenarios = [scenario for scenario in SCENARIO_ORDER if scenario in seed_pairs_by_scenario]
    scenarios += sorted(set(seed_pairs_by_scenario) - set(scenarios))

    for scenario in scenarios:
        seed_pairs = sorted(seed_pairs_by_scenario[scenario])
        for policy in POLICY_ORDER:
            deltas: list[float] = []
            for train_seed, eval_seed in seed_pairs:
                key = (scenario, train_seed, eval_seed, policy)
                rollout_key = (scenario, train_seed, eval_seed, "rollout_teacher")
                if key not in selected or rollout_key not in selected:
                    continue
                deltas.append(selected[key] - selected[rollout_key])
            if not deltas:
                continue
            ci_low, ci_high = bootstrap_ci(deltas, samples, rng)
            mean_delta = sum(deltas) / len(deltas)
            output.append(
                {
                    "scenario": scenario,
                    "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
                    "policy": policy,
                    "policy_label": policy_label(policy, cascade_band),
                    "n_pairs": str(len(deltas)),
                    "mean_delta_vs_rollout": f"{mean_delta:.2f}",
                    "bootstrap_ci95_low": f"{ci_low:.2f}",
                    "bootstrap_ci95_high": f"{ci_high:.2f}",
                }
            )
    return output


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "scenario",
        "scenario_label",
        "policy",
        "policy_label",
        "n_pairs",
        "mean_delta_vs_rollout",
        "bootstrap_ci95_low",
        "bootstrap_ci95_high",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Paired Policy Delta Summary",
        "",
        "Negative values mean the policy earns less closed-loop profit than the finite rollout teacher on the same train/eval seed pair.",
        "",
        "| Scenario | Policy | N | Mean Delta | Paired Bootstrap 95% CI |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        mean_delta = float(row["mean_delta_vs_rollout"])
        ci_low = float(row["bootstrap_ci95_low"])
        ci_high = float(row["bootstrap_ci95_high"])
        lines.append(
            "| "
            f"`{row['scenario_label']}` | {row['policy_label']} | {row['n_pairs']} | "
            f"{money(mean_delta)} | [{money(ci_low)}, {money(ci_high)}] |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cascade-band", type=float, default=500.0)
    parser.add_argument("--bootstrap-samples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20260509)
    args = parser.parse_args()

    rows = summarize(args.run_dir, args.cascade_band, args.bootstrap_samples, args.seed)
    write_csv(args.run_dir / "freightbidbench_policy_delta_summary.csv", rows)
    write_markdown(args.run_dir / "freightbidbench_policy_delta_summary.md", rows)


if __name__ == "__main__":
    main()
