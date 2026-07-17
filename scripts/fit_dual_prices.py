"""Fit a dual-price table for the v0.4 `dual_price` policy prototype.

Joins converged Lagrangian dual prices (`lagrangian_dual_prices.csv`, one
lambda per realized load id) with the deterministic load stream regenerated
from the same scenario and eval seed, then aggregates lambda into a lookup
table keyed by (scenario, origin_state, hour-of-day bucket) with per-origin
and global fallback rows.

The resulting table is the opportunity-cost surface consumed by the
`dual_price` policy branch in `run_surrogate_cascade.choose_action`.
Dependency-free (Python standard library only).

Usage (one invocation per scenario whose duals exist):
    python3 scripts/fit_dual_prices.py \
        --config configs/freightbidbench_v03_scenarios.json \
        --scenario tight \
        --eval-seed 20260507 \
        --duals-csv benchmark_runs/lagrangian_bound_full_v6_warm/lagrangian_dual_prices.csv

    python3 scripts/fit_dual_prices.py \
        --config configs/freightbidbench_v03_scenarios.json \
        --scenario scarce \
        --eval-seed 20260507 \
        --duals-csv benchmark_runs/lagrangian_bound_scarce_full/lagrangian_dual_prices.csv

Rows for a scenario are replaced on refit; other scenarios' rows are kept.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

DEFAULT_CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "dual_price_tables.csv"

GLOBAL_ORIGIN = "*"
ALL_HOURS = -1
# Empirical-Bayes shrinkage: hour-bucket means are pulled toward the origin
# mean with this many pseudo-observations, since ~28% of (origin, hour)
# buckets rest on fewer than 3 realized loads in a single stream.
SHRINKAGE_PSEUDO_COUNT = 5.0


def load_duals(path: Path) -> dict[int, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            int(row["load_id"]): float(row["lambda"])
            for row in csv.DictReader(handle)
        }


def fit_table(
    scenario: base.Scenario,
    loads: list[dict[str, object]],
    duals: dict[int, float],
) -> list[dict[str, object]]:
    by_bucket: defaultdict[tuple[str, int], list[float]] = defaultdict(list)
    by_origin: defaultdict[str, list[float]] = defaultdict(list)
    all_lambdas: list[float] = []

    for load in loads:
        lam = duals.get(int(load["load_id"]))
        if lam is None:
            continue
        origin = str(load["origin_state"])
        hour_bucket = int(float(load["hour"])) % 24
        by_bucket[(origin, hour_bucket)].append(lam)
        by_origin[origin].append(lam)
        all_lambdas.append(lam)

    def row(
        origin: str, hour_bucket: int, lambda_mean: float, n_loads: int
    ) -> dict[str, object]:
        return {
            "scenario": scenario.name,
            "origin_state": origin,
            "hour_bucket": hour_bucket,
            "lambda_mean": f"{lambda_mean:.4f}",
            "n_loads": n_loads,
        }

    origin_means = {
        origin: sum(values) / len(values) for origin, values in by_origin.items()
    }
    rows = []
    for (origin, hour_bucket), values in sorted(by_bucket.items()):
        n = len(values)
        shrunk = (sum(values) + SHRINKAGE_PSEUDO_COUNT * origin_means[origin]) / (
            n + SHRINKAGE_PSEUDO_COUNT
        )
        rows.append(row(origin, hour_bucket, shrunk, n))
    rows.extend(
        row(origin, ALL_HOURS, origin_means[origin], len(values))
        for origin, values in sorted(by_origin.items())
    )
    if all_lambdas:
        rows.append(
            row(GLOBAL_ORIGIN, ALL_HOURS, sum(all_lambdas) / len(all_lambdas), len(all_lambdas))
        )
    return rows


def write_table(path: Path, scenario_name: str, new_rows: list[dict[str, object]]) -> None:
    kept: list[dict[str, object]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            kept = [
                row for row in csv.DictReader(handle) if row["scenario"] != scenario_name
            ]
    fieldnames = ["scenario", "origin_state", "hour_bucket", "lambda_mean", "n_loads"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
        writer.writerows(new_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--eval-seed", type=int, required=True)
    parser.add_argument("--duals-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with (args.config if args.config.is_absolute() else ROOT / args.config).open(
        encoding="utf-8"
    ) as handle:
        config = json.load(handle)
    scenario_config = config["scenarios"][args.scenario]
    scenario = lag.scenario_from_config(scenario_config)

    lanes = base.load_csv(base.LANES)
    loads = sc.generate_loads_with_seed(lanes, scenario, args.eval_seed)
    duals = load_duals(
        args.duals_csv if args.duals_csv.is_absolute() else ROOT / args.duals_csv
    )

    matched = sum(1 for load in loads if int(load["load_id"]) in duals)
    if matched != len(duals):
        raise SystemExit(
            f"Stream/dual mismatch: {len(loads)} regenerated loads matched "
            f"{matched} of {len(duals)} duals. Check --scenario/--eval-seed."
        )

    rows = fit_table(scenario, loads, duals)
    write_table(
        args.output if args.output.is_absolute() else ROOT / args.output,
        scenario.name,
        rows,
    )
    nonzero = sum(1 for lam in duals.values() if lam > 0)
    print(
        f"Fitted {len(rows)} table rows for {scenario.name} from {len(duals)} duals "
        f"({nonzero} nonzero) at eval seed {args.eval_seed}."
    )


if __name__ == "__main__":
    main()
