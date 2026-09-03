"""Read certified (sound-solver) upper bounds from solve directories.

Every certificate in the paper divides a realized policy value by
L(lambda) evaluated with the sound per-truck solver at a dual
search's incumbent duals (scripts/certify_bound.py writes that value
to sound_bound_summary.csv beside the search's own summary). The
search's best_bound in lagrangian_bound_summary.csv was produced by
the legacy corner rule and is not a valid upper bound in general, so
this module refuses to fall back to it.
"""

from __future__ import annotations

import csv
from pathlib import Path

SOUND_SUMMARY = "sound_bound_summary.csv"


def read_certified_bound(solve_dir: Path) -> float:
    path = Path(solve_dir) / SOUND_SUMMARY
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing: run scripts/certify_bound.py --solve-dir "
            f"{solve_dir} (the search's best_bound is not a valid certificate)"
        )
    with path.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    return float(row["sound_bound"])


def read_certified_elapsed(solve_dir: Path) -> float:
    """Wall-clock seconds of the sound evaluation."""
    with (Path(solve_dir) / SOUND_SUMMARY).open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    return float(row["elapsed_seconds"])


def best_certified_bound(solve_dirs: list[Path]) -> float:
    """Tightest certified bound across several solves of the same
    instance (each is a valid upper bound at its own duals, so the
    minimum is valid)."""
    bounds = [read_certified_bound(d) for d in solve_dirs if (Path(d) / SOUND_SUMMARY).exists()]
    if not bounds:
        raise FileNotFoundError(f"no {SOUND_SUMMARY} in any of {solve_dirs}")
    return min(bounds)
