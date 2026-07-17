"""DP-1 prototype experiment: dual-price policy vs baselines (v0.4 track).

Evaluates the `dual_price` policy (Lagrangian dual prices as calibrated
opportunity costs, see `scripts/fit_dual_prices.py`) against the standing
baselines on held-out seed pairs, without touching the public benchmark
contract. Mirrors the per-cell orchestration of the benchmark runner:
train-surrogate on the train stream, simulate all policies on the eval
stream under common random numbers.

Seed hygiene: the dual tables are fitted on eval seed 20260507 (seed pair
0), so this experiment defaults to pairs 1..3 (eval seeds 20260509,
20260511, 20260513) to keep the evaluation out-of-sample. Pass
--first-pair 0 to include the in-sample pair for reference.

Usage:
    python3 scripts/run_dual_price_experiment.py \
        --config configs/freightbidbench_v03_scenarios.json \
        --scenarios tight,scarce --first-pair 1 --pair-count 3 \
        --label-limit 200 \
        --output-dir benchmark_runs/v04_dev/dual_price_experiment
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT = ROOT / "benchmark_runs" / "v04_dev" / "dual_price_experiment"
DEFAULT_POLICIES = [
    "bid_price",
    "surrogate_linear",
    "dual_price",
    "rollout_teacher",
]


def as_float(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scenarios", default="tight,scarce")
    parser.add_argument("--first-pair", type=int, default=1)
    parser.add_argument("--pair-count", type=int, default=3)
    parser.add_argument("--label-limit", type=int, default=200)
    parser.add_argument("--policies", default=",".join(DEFAULT_POLICIES))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with (args.config if args.config.is_absolute() else ROOT / args.config).open(
        encoding="utf-8"
    ) as handle:
        config = json.load(handle)
    first_seed = int(config["default_first_seed"])
    policies = [name.strip() for name in args.policies.split(",") if name.strip()]
    scenario_keys = [key.strip() for key in args.scenarios.split(",") if key.strip()]

    sc.LABEL_DECISION_LIMIT = args.label_limit
    lanes = base.load_csv(base.LANES)

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for scenario_key in scenario_keys:
        scenario = lag.scenario_from_config(config["scenarios"][scenario_key])
        state_values = base.build_state_values(lanes, scenario)

        for pair_index in range(args.first_pair, args.first_pair + args.pair_count):
            train_seed = first_seed + 2 * pair_index
            eval_seed = train_seed + 1
            print(f"[{scenario_key}] pair {pair_index}: train={train_seed} eval={eval_seed}")

            needs_model = any(
                name in ("surrogate_linear", "cascade_surrogate_rollout")
                for name in policies
            )
            if needs_model:
                train_labels, _, _ = sc.generate_rollout_labels(
                    lanes, scenario, train_seed, state_values
                )
                model = sc.train_linear_model(train_labels)
            else:
                model = sc.LinearModel(["bias_only"], [0.0], [1.0], [0.0, 0.0])
            eval_loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
            starting_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)

            summaries: dict[str, dict[str, object]] = {}
            for policy_name in policies:
                summary, _ = sc.simulate_policy(
                    policy_name,
                    eval_loads,
                    starting_fleet,
                    lanes,
                    scenario,
                    state_values,
                    model,
                    rollout_seed_offset=eval_seed,
                )
                summaries[policy_name] = summary

            rollout_profit = as_float(summaries.get("rollout_teacher", {}).get("profit"))
            for policy_name in policies:
                summary = summaries[policy_name]
                profit = as_float(summary["profit"])
                rows.append(
                    {
                        "scenario": scenario_key,
                        "pair_index": pair_index,
                        "train_seed": train_seed,
                        "eval_seed": eval_seed,
                        "policy": policy_name,
                        "profit": f"{profit:.2f}",
                        "retention_vs_rollout": f"{profit / rollout_profit:.4f}"
                        if rollout_profit
                        else "",
                        "mean_latency_ms": summary["mean_latency_ms"],
                        "accepted": summary["accepted"],
                        "infeasible": summary["infeasible"],
                        "service_failure_penalty_cost": summary.get(
                            "service_failure_penalty_cost", ""
                        ),
                        "terminal_fleet_value": summary.get("terminal_fleet_value", ""),
                    }
                )

    sc.write_csv(output_dir / "dual_price_experiment_runs.csv", rows)

    print("\n=== Mean retention vs rollout (held-out pairs) ===")
    print(f"{'scenario':8s} {'policy':18s} {'retention':>10s} {'latency ms':>11s}")
    for scenario_key in scenario_keys:
        for policy_name in policies:
            cells = [
                row
                for row in rows
                if row["scenario"] == scenario_key and row["policy"] == policy_name
            ]
            if not cells:
                continue
            retentions = [as_float(row["retention_vs_rollout"]) for row in cells]
            latencies = [as_float(row["mean_latency_ms"]) for row in cells]
            print(
                f"{scenario_key:8s} {policy_name:18s} "
                f"{100 * sum(retentions) / len(retentions):9.1f}% "
                f"{sum(latencies) / len(latencies):11.3f}"
            )
    print(f"\nWrote {output_dir / 'dual_price_experiment_runs.csv'}")


if __name__ == "__main__":
    main()
