"""Time the dense reference DLP solve on replicated networks.

Scope, stated narrowly: this measures how *this repository's dense
standard-library simplex* scales when the lane table is replicated k
times with disjoint market names (74 lanes / 12 markets at k = 1).
The replicated model is block-diagonal --- the copies are disconnected
--- so a sparse or decomposition-aware solver could exploit exactly
that structure, and total expected demand is not rescaled with the
copies. These timings therefore characterize the reference
implementation only; they are *not* evidence about the inherent cost
of re-solving on realistically refined (connected, demand-scaled)
networks, and the paper cites them only as reference-implementation
timings.

Usage:
    python3 scripts/measure_dlp_resolve_cost.py \
        --output benchmark_runs/trackb/dlp_resolve_cost.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_dlp_resolve as dlp  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402

CONFIG = ROOT / "configs" / "freightbidbench_v03_scenarios.json"


def replicate_lanes(
    lanes: list[dict[str, str]], k: int
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for copy in range(k):
        suffix = "" if copy == 0 else f"_{copy}"
        for lane in lanes:
            row = dict(lane)
            row["origin_state"] = str(lane["origin_state"]) + suffix
            row["destination_state"] = (
                str(lane["destination_state"]) + suffix
            )
            out.append(row)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "benchmark_runs" / "trackb" / "dlp_resolve_cost.csv",
    )
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    scenario = lag.scenario_from_config(config["scenarios"]["tight"])
    base_lanes = base.load_csv(base.LANES)
    state_values = base.build_state_values(base_lanes, scenario)

    rows: list[dict[str, object]] = []
    for k in (1, 2, 4, 8):
        lanes = replicate_lanes(base_lanes, k)
        sv = dict(state_values)
        for lane in lanes:
            for m in (lane["origin_state"], lane["destination_state"]):
                sv.setdefault(m, state_values.get(str(m).split("_")[0], 0.0))
        markets = {l["origin_state"] for l in lanes} | {
            l["destination_state"] for l in lanes
        }
        fleet = {
            m: [feas.TruckState(f"{m}-0", str(m), 0.0)] for m in markets
        }
        # Calibration constants transfer from the base network.
        dlp._MEAN_EXTRA_COST[scenario.name] = dlp.mean_extra_cost(
            scenario, base_lanes
        )
        dlp._MEAN_SCHEDULE_OVERHEAD[scenario.name] = (
            dlp.mean_schedule_overhead(scenario, base_lanes)
        )
        # One warm-up solve (excluded), then timed cold-state solves:
        # every call rebuilds the LP from scratch (no caching inside
        # solve_potentials), so repeats differ only by machine noise.
        dlp.solve_potentials(scenario, lanes, fleet, 0.0, sv)
        times = []
        for _ in range(args.repeats):
            t0 = time.perf_counter()
            dlp.solve_potentials(scenario, lanes, fleet, 0.0, sv)
            times.append(time.perf_counter() - t0)
        rows.append(
            {
                "replication": k,
                "lanes": len(lanes),
                "markets": len(markets),
                "mean_solve_seconds": f"{statistics.mean(times):.3f}",
                "stdev_solve_seconds": f"{statistics.stdev(times):.3f}",
                "repeats": args.repeats,
                "solver": "dense two-phase simplex (stdlib, Bland)",
                "platform": platform.platform(),
                "python": platform.python_version(),
            }
        )
        print(
            f"x{k}: {len(lanes)} lanes, {len(markets)} markets ->"
            f" {statistics.mean(times):.3f} s per solve"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
