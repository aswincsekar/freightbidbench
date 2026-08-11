"""Select the DLP re-solve cadence on training streams.

The re-solving DLP baseline has one hyperparameter: the re-solve
cadence. Selecting it on the thirty evaluation pairs would leak the
test set, so this driver evaluates the DLP at each candidate cadence
on the thirty *training* streams (the seeds the dual tables' pair
indices reserve for training: 20260508, 20260510, ...) and reports
mean profit per cadence per scenario. The evaluation-pair comparison
in the paper is then run at the training-selected cadence, alongside
the full sensitivity sweep.

Writes one CSV (scenario, cadence_hours, train_streams, mean_profit,
selected) per run. Dependency-free, deterministic.

Usage:
    python3 scripts/tune_dlp_cadence.py \
        --output benchmark_runs/trackb/dlp_cadence_tuning.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_closed_loop_baselines as base  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402

CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
CADENCES = (12.0, 6.0, 3.0, 2.0, 1.0)
FIRST_SEED = 20260506
PAIRS = range(1, 31)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "benchmark_runs" / "trackb" / "dlp_cadence_tuning.csv",
    )
    args = parser.parse_args()

    import json

    import run_dlp_resolve as dlp

    config = json.loads(CONFIG.read_text())
    lanes = base.load_csv(base.LANES)

    rows: list[dict[str, object]] = []
    for scen_key in ("tight", "scarce", "mild"):
        scenario = lag.scenario_from_config(config["scenarios"][scen_key])
        state_values = base.build_state_values(lanes, scenario)
        by_cadence: dict[float, list[float]] = {}
        for cadence in CADENCES:
            dlp.RESOLVE_EVERY_HOURS = cadence
            profits: list[float] = []
            for pair in PAIRS:
                train_seed = FIRST_SEED + 2 * pair
                loads = sc.generate_loads_with_seed(lanes, scenario, train_seed)
                fleet = sc.initial_fleet_with_seed(lanes, scenario, train_seed)
                dlp._RESOLVE_STATE.clear()
                summary, _ = sc.simulate_policy(
                    "dlp_resolve",
                    loads,
                    fleet,
                    lanes,
                    scenario,
                    state_values,
                    None,
                )
                profits.append(float(summary["profit"]))
            by_cadence[cadence] = profits
            print(
                f"{scen_key} cadence {cadence:g}h:"
                f" mean profit {statistics.mean(profits):,.0f}"
            )
        best = max(by_cadence, key=lambda c: statistics.mean(by_cadence[c]))
        for cadence, profits in by_cadence.items():
            rows.append(
                {
                    "scenario": scen_key,
                    "cadence_hours": cadence,
                    "train_streams": len(profits),
                    "mean_profit": f"{statistics.mean(profits):.2f}",
                    "selected": int(cadence == best),
                }
            )
        print(f"{scen_key}: selected cadence {best:g}h (on training streams)")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
