"""Confirmatory analysis on the pre-registered pairs 31-60.

Applies the FROZEN estimators (analyze_v04_results.bootstrap_ci /
wilcoxon / sign test, and the Bonferroni / DLP-delta / naive-retention
conventions of analyze_trackb_results) to the locked confirmation
directories under benchmark_runs/v04_dev/confirm60. No estimator is
redefined here; this driver only re-targets the frozen ones at the
confirmatory artifacts, per PREREG_manifest_amended.json.

Usage:
    python3 scripts/analyze_confirmation.py
"""

from __future__ import annotations

import csv
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_v04_results as av  # noqa: E402

CONFIRM = ROOT / "benchmark_runs" / "v04_dev" / "confirm60"
RUNS = "dual_price_experiment_runs.csv"
SCENARIOS = ("tight", "scarce", "mild")


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def profits(path: Path, policy: str) -> dict[int, float]:
    return {
        int(r["pair_index"]): float(r["profit"])
        for r in read(path)
        if r["policy"] == policy
    }


def main() -> None:
    print("== Bonferroni simultaneous CIs (vf - surrogate, 98.33%),"
          " confirmation pairs 31-60 ==")
    alpha = 0.05 / 3
    for scen in SCENARIOS:
        src = CONFIRM / scen / RUNS
        roll = profits(src, "rollout_teacher")
        sur = profits(src, "surrogate_linear")
        vf = profits(src, "dual_price_vf")
        deltas = [100 * (vf[p] - sur[p]) / roll[p] for p in sorted(vf)]
        rng = random.Random(20260701)
        means = sorted(
            statistics.mean(rng.choices(deltas, k=len(deltas)))
            for _ in range(20000)
        )
        lo = means[int(20000 * alpha / 2)]
        hi = means[int(20000 * (1 - alpha / 2)) - 1]
        print(
            f"  {scen:>7}: {statistics.mean(deltas):+.2f} pp"
            f" [{lo:+.2f}, {hi:+.2f}]"
            f" {'excludes 0' if lo > 0 or hi < 0 else 'includes 0'}"
        )

    print("== dlp_resolve (tuned cadence) - dual_price_vf paired"
          " bootstrap CI95, confirmation ==")
    for scen in SCENARIOS:
        src = CONFIRM / scen / RUNS
        roll = profits(src, "rollout_teacher")
        vf = profits(src, "dual_price_vf")
        dlp = profits(CONFIRM / "dlp_tuned" / scen / RUNS, "dlp_resolve")
        pairs = sorted(set(vf) & set(dlp))
        deltas = [100 * (dlp[p] - vf[p]) / roll[p] for p in pairs]
        rng = random.Random(20260701)
        lo, hi = av.bootstrap_ci(deltas, 20000, rng)
        rets = [100 * dlp[p] / roll[p] for p in pairs]
        lat = statistics.mean(
            float(r["mean_latency_ms"])
            for r in read(CONFIRM / "dlp_tuned" / scen / RUNS)
        )
        print(
            f"  {scen:>7}: dlp retention {statistics.mean(rets):.1f}%"
            f" (sd {statistics.stdev(rets):.1f}, {lat:.2f} ms);"
            f" delta {statistics.mean(deltas):+.2f} pp"
            f" [CI95 {lo:+.2f}, {hi:+.2f}]"
        )

    print("== naive-continuation ablation retention, confirmation ==")
    for scen in SCENARIOS:
        roll = profits(CONFIRM / scen / RUNS, "rollout_teacher")
        naive = profits(
            CONFIRM / "naive" / scen / RUNS, "dual_price_vf_naive"
        )
        rets = [100 * naive[p] / roll[p] for p in sorted(naive)]
        print(
            f"  {scen:>7}: {statistics.mean(rets):.1f}%"
            f" (sd {statistics.stdev(rets):.1f})"
        )

    print("== vf vs rollout teacher (paired, confirmation) ==")
    for scen in SCENARIOS:
        src = CONFIRM / scen / RUNS
        roll = profits(src, "rollout_teacher")
        vf = profits(src, "dual_price_vf")
        rets = [100 * vf[p] / roll[p] for p in sorted(vf)]
        wins = sum(1 for p in vf if vf[p] > roll[p])
        print(
            f"  {scen:>7}: {statistics.mean(rets):.1f}%"
            f" (sd {statistics.stdev(rets):.1f}); beats rollout on"
            f" {wins}/30 pairs"
        )


if __name__ == "__main__":
    main()
