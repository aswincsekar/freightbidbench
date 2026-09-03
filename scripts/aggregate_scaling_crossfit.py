"""Aggregate the cross-fitted scaling run directories into the
analyzer's artifact.

Deterministic: reads only the 18 run directories produced by
run_scaling_crossfit.sh plus the evaluation seeds' rollout rows and
bound summaries, and writes scaling_crossfit.csv with explicit
table provenance (table_train_seed is the seed whose dual solve
supplied the fitted tables; the child runner CSVs' train_seed column
records the paired stream's nominal seed and should not be read as
table provenance).

Usage:
    python3 scripts/aggregate_scaling_crossfit.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import certified_bound  # noqa: E402
TRACKB = ROOT / "benchmark_runs" / "trackb"
RUNS = "dual_price_experiment_runs.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def best_bound(cell: str, seed: int) -> float:
    """Tightest sound-certified bound for the evaluation seed's own
    solves (base directory plus any warm extensions, each certified at
    its own incumbent duals). Search-only originals are retained under
    trackb/scaling for the audit."""
    base_dir = ROOT / "benchmark_runs" / "v041_fix" / "scaling"
    return certified_bound.best_certified_bound(
        sorted(base_dir.glob(f"{cell}_{seed}*"))
    )


def aggregate(out_path: Path | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for d in sorted(TRACKB.glob("scaling_crossfit/*_train*_eval*")):
        name = d.name
        cell = name.split("_train")[0]
        train = int(name.split("_train")[1].split("_eval")[0])
        ev = int(name.split("_eval")[1])
        prof = {
            r["policy"]: float(r["profit"]) for r in read(d / RUNS)
        }
        eva = read(TRACKB / "scaling_eval" / f"{cell}_{ev}" / RUNS)
        rollout = next(
            float(r["profit"]) for r in eva if r["policy"] == "rollout_teacher"
        )
        rows.append(
            {
                "cell": cell,
                "table_train_seed": train,
                "eval_seed": ev,
                "profit": f"{prof['dual_price_vf']:.2f}",
                "rollout": f"{rollout:.2f}",
                "bound": f"{best_bound(cell, ev):.2f}",
            }
        )
    if out_path is not None:
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    return rows


def main() -> None:
    out = TRACKB / "scaling_crossfit" / "scaling_crossfit.csv"
    rows = aggregate(out)
    print(f"Wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
