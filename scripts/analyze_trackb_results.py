"""Regenerate the revision (Track B) statistics of the v0.4 paper from
raw artifacts under benchmark_runs/trackb/.

Sections mirror the paper's revision experiments:
  portability   five training days x twenty eval pairs: per-arm mean
                retention and the cross-training-day spread per pair.
  scaling       multi-seed proportional scaling: certified gap and
                policy-vs-rollout per K cell (mean +- sd over seeds).
  subcritical   the theorem-matching family: certified fraction per K
                at each solver budget (base, _ext, _ext2 dirs), zero
                forced-rejection check, and policy vs rollout.
  headline      cascade and dlp_resolve retention on the thirty pairs,
                merged against the seed30 rollout rows (the cascade
                and DLP runs carry no in-run rollout column).
  micro         exact attribution decompositions (relaxation slack /
                dispatch cost / accept loss shares).

Dependency-free, deterministic. Usage:
    python3 scripts/analyze_trackb_results.py
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import certified_bound  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRACKB = ROOT / "benchmark_runs" / "trackb"
SEED30 = ROOT / "benchmark_runs" / "v04_dev" / "seed30"
RUNS = "dual_price_experiment_runs.csv"
BOUND = "lagrangian_bound_summary.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rollout_profits(scenario: str) -> dict[int, float]:
    return {
        int(r["pair_index"]): float(r["profit"])
        for r in read(SEED30 / scenario / RUNS)
        if r["policy"] == "rollout_teacher"
    }


def section_portability() -> None:
    print("== portability (tight, eval pairs 11-30) ==")
    arms: dict[str, dict[int, float]] = {}
    roll = rollout_profits("tight")
    for d in sorted((TRACKB / "portability").iterdir()):
        arms[d.name.replace("train_", "")] = {
            int(r["pair_index"]): float(r["profit"])
            for r in read(d / RUNS)
            if r["policy"] == "dual_price_vf"
        }
    pairs = sorted(next(iter(arms.values())))
    for day, prof in arms.items():
        rets = [100 * prof[p] / roll[p] for p in pairs]
        print(f"  train {day}: mean retention {statistics.mean(rets):.1f}%")
    spread = [
        100 * (max(a[p] for a in arms.values()) - min(a[p] for a in arms.values())) / roll[p]
        for p in pairs
    ]
    print(
        f"  cross-day spread per pair: mean {statistics.mean(spread):.2f} pp,"
        f" max {max(spread):.2f} pp"
    )


def section_scaling() -> None:
    print("== multi-seed scaling (tight cells, 3 fresh seeds) ==")
    cells: dict[str, list[tuple[float, float]]] = defaultdict(list)
    fix_scaling = ROOT / "benchmark_runs" / "v041_fix" / "scaling"
    for d in sorted(fix_scaling.iterdir()):
        if d.name.endswith("_ext1") or not (d / BOUND).exists():
            continue
        best = certified_bound.best_certified_bound(
            [d, fix_scaling / (d.name + "_ext1")]
        )
        rec = {"best_bound": best}
        rows = read(TRACKB / "scaling_eval" / d.name / RUNS)
        prof = {r["policy"]: float(r["profit"]) for r in rows}
        gap = 100 * (1 - prof["dual_price_vf"] / float(rec["best_bound"]))
        vs = 100 * prof["dual_price_vf"] / prof["rollout_teacher"]
        cells[d.name.rsplit("_", 1)[0]].append((gap, vs))
    for cell, vals in cells.items():
        gaps = [g for g, _ in vals]
        vss = [v for _, v in vals]
        print(
            f"  {cell}: certified gap {statistics.mean(gaps):.1f}"
            f" +- {statistics.stdev(gaps):.1f}%,"
            f" policy vs rollout {statistics.mean(vss):.1f}%"
        )


def section_scaling_crossfit() -> None:
    """Cross-fitted scaling cells: tables from a different seed's
    solve, policy and rollout on the evaluation seed, bound from that
    same evaluation seed. Aggregated by evaluation stream (n = 3)."""
    print("== scaling cross-fit (by evaluation stream, n=3) ==")
    path = TRACKB / "scaling_crossfit" / "scaling_crossfit.csv"
    if not path.exists():
        print("  (no scaling-crossfit artifact)")
        return
    vs: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    cert: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in read(path):
        cell, ev = r["cell"], int(r["eval_seed"])
        vs[cell][ev].append(100 * float(r["profit"]) / float(r["rollout"]))
        cert[cell][ev].append(100 * float(r["profit"]) / float(r["bound"]))
    for cell in ("tight_x05", "tight_x1", "tight_x2"):
        v = [statistics.mean(x) for x in vs[cell].values()]
        c = [statistics.mean(x) for x in cert[cell].values()]
        print(
            f"  {cell}: vs rollout {statistics.mean(v):.1f}"
            f" +- {statistics.stdev(v):.1f}%,"
            f" certified gap {100 - statistics.mean(c):.1f}"
            f" +- {statistics.stdev(c):.1f}%"
        )


def best_bound_across_budgets(name: str) -> dict[str, float]:
    """Sound-certified bound per solver budget for a subcritical cell:
    base, _ext, _ext2 (each certified at its own incumbent duals)."""
    out: dict[str, float] = {}
    for suffix in ("", "_ext", "_ext2"):
        d = ROOT / "benchmark_runs" / "v041_fix" / "subcritical" / (name + suffix)
        if (d / BOUND).exists():
            out[suffix or "base"] = certified_bound.read_certified_bound(d)
    return out


def section_subcritical() -> None:
    print("== subcritical theorem-matching family ==")
    # In-sample policy profits come from the corrected-fitter rerun
    # (subcritical_insample, --pairs in); rollout denominators from the
    # original eval dirs (rollout is table-independent).
    insample = {
        (r["cell"], int(r["eval_seed"])): float(r["profit"])
        for r in read(
            TRACKB / "subcritical_insample" / "subcritical_crossfit.csv"
        )
    }
    by_cell: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    vs_rollout: dict[str, list[float]] = defaultdict(list)
    for d in sorted((TRACKB / "subcritical_eval").iterdir()):
        name = d.name
        cell, seed = name.rsplit("_", 1)
        rows = read(d / RUNS)
        rollout = next(
            float(r["profit"]) for r in rows if r["policy"] == "rollout_teacher"
        )
        profit = insample[(cell, int(seed))]
        vs_rollout[cell].append(100 * profit / rollout)
        for budget, bound in best_bound_across_budgets(name).items():
            by_cell[cell][budget].append(100 * profit / bound)
    for cell, budgets in by_cell.items():
        parts = []
        for budget in ("base", "_ext", "_ext2"):
            if budget in budgets:
                vals = budgets[budget]
                sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
                parts.append(
                    f"{budget.strip('_') or 'base'}:"
                    f" {statistics.mean(vals):.1f} +- {sd:.1f}%"
                )
        print(f"  {cell}: certified {' -> '.join(parts)}")
        print(
            f"    vs rollout {statistics.mean(vs_rollout[cell]):.1f}%"
        )


def section_headline_arms() -> None:
    print("== cascade / dlp_resolve / naive on the thirty pairs ==")
    for arm, sub in (
        ("cascade", "cascade30"),
        ("dlp 12h", "dlp30"),
        ("dlp 6h", "dlp30_r6"),
        ("dlp 3h", "dlp30_r3"),
        ("dlp 2h", "dlp30_r2"),
        ("dlp 1h", "dlp30_r1"),
        ("naive", "naive30"),
    ):
        for scen in ("tight", "scarce", "mild"):
            roll = rollout_profits(scen)
            rows = read(TRACKB / sub / scen / RUNS)
            rets = [
                100 * float(r["profit"]) / roll[int(r["pair_index"])] for r in rows
            ]
            lat = statistics.mean(float(r["mean_latency_ms"]) for r in rows)
            print(
                f"  {arm:>12} {scen:>7}: retention"
                f" {statistics.mean(rets):5.1f}% (sd {statistics.stdev(rets):.1f})"
                f" at {lat:6.2f} ms"
            )


def section_crossfit() -> None:
    print("== out-of-sample cross-fit (low-contention family) ==")
    path = TRACKB / "subcritical_crossfit" / "subcritical_crossfit.csv"
    if not path.exists():
        print("  (no crossfit artifacts)")
        return
    # Aggregate by evaluation stream: three independent streams per
    # cell, each scored under two independent training tables --- the
    # per-stream mean is one observation, not two.
    by_stream: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    guard: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in read(path):
        key = f"{r['cell']}_{r['eval_seed']}"
        roll = {
            rr["policy"]: float(rr["profit"])
            for rr in read(TRACKB / "subcritical_eval" / key / RUNS)
        }
        by_stream[r["cell"]][key].append(float(r["certified_pct"]))
        g = guard[r["cell"]]
        g["vs"].append(100 * float(r["profit"]) / roll["rollout_teacher"])
        g["guard"].append(int(r["guard_fires"]))
        g["guard_pos"].append(int(r["guard_score_positive"]))
        g["loads"].append(int(r["loads"]))
    for cell, streams in by_stream.items():
        per_stream = [statistics.mean(v) for v in streams.values()]
        c = guard[cell]
        print(
            f"  {cell}: certified {statistics.mean(per_stream):.1f}"
            f" +- {statistics.stdev(per_stream):.1f}%"
            " (out of sample; by evaluation stream, n=3),"
            f" vs rollout {statistics.mean(c['vs']):.1f}%,"
            f" guard fires {statistics.mean(c['guard']):.0f}"
            f"/{statistics.mean(c['loads']):.0f} loads"
            f" ({100 * statistics.mean(c['guard_pos']) / statistics.mean(c['loads']):.1f}%"
            " score-positive blocked)"
        )


def section_dlp_cis() -> None:
    print("== dlp_resolve - dual_price_vf paired bootstrap CI95 ==")
    import random

    import analyze_v04_results as av

    args = type(
        "Args",
        (),
        {
            "seed30_dir": str(SEED30),
            "mild_dir": str(SEED30.parent / "seed30_mild_fitted"),
        },
    )()
    rows_by_scen = av.load_scenario_rows(args)
    for scen in ("tight", "scarce", "mild"):
        vf = {
            int(r["pair_index"]): float(r["profit"])
            for r in rows_by_scen[scen]
            if r["policy"] == "dual_price_vf"
        }
        roll = rollout_profits(scen)
        for tag, sub in (
            ("12h", "dlp30"),
            ("6h", "dlp30_r6"),
            ("3h", "dlp30_r3"),
            ("2h", "dlp30_r2"),
            ("1h", "dlp30_r1"),
        ):
            dlp = {
                int(r["pair_index"]): float(r["profit"])
                for r in read(TRACKB / sub / scen / RUNS)
            }
            pairs = sorted(set(vf) & set(dlp))
            deltas = [100 * (dlp[p] - vf[p]) / roll[p] for p in pairs]
            rng = random.Random(20260701)
            lo, hi = av.bootstrap_ci(deltas, 20000, rng)
            print(
                f"  {scen:>7} {tag:>3}: {statistics.mean(deltas):+.2f} pp"
                f" [CI95 {lo:+.2f}, {hi:+.2f}]"
            )


def tuned_cadence(scen: str) -> float:
    """Training-stream-selected re-solve cadence for a scenario, from
    the tuning artifact."""
    for r in read(TRACKB / "dlp_cadence_tuning.csv"):
        if r["scenario"] == scen and int(r["selected"]):
            return float(r["cadence_hours"])
    raise KeyError(scen)


DLP_DIR_BY_CADENCE = {
    12.0: "dlp30",
    6.0: "dlp30_r6",
    3.0: "dlp30_r3",
    2.0: "dlp30_r2",
    1.0: "dlp30_r1",
}


def section_dlp_certs() -> None:
    """Certified fractions for the tuned re-solving DLP on the ten
    bound-solved instances per stress scenario -- the
    policy-agnostic-certifier row of the certificates table."""
    print("== tuned-DLP certificates (pairs 1-10, certs bounds) ==")
    # Corrected-solver certificates (invalid originals retained
    # under v04_dev/certs for the audit).
    certs = ROOT / "benchmark_runs" / "v041_fix" / "certs"
    for scen in ("tight", "scarce"):
        cadence = tuned_cadence(scen)
        dlp = {
            int(r["pair_index"]): float(r["profit"])
            for r in read(
                TRACKB / DLP_DIR_BY_CADENCE[cadence] / scen / RUNS
            )
        }
        fracs = []
        for pair in range(1, 11):
            bound = certified_bound.read_certified_bound(
                certs / f"{scen}_{20260507 + 2 * pair}"
            )
            fracs.append(100 * dlp[pair] / bound)
        print(
            f"  {scen}: dlp {tuned_cadence(scen):g}h certified >="
            f" {statistics.mean(fracs):.1f}%"
            f" ({min(fracs):.1f}--{max(fracs):.1f})"
        )


def section_matched_family() -> None:
    """The assumption-matched synthetic family: certified fraction and
    per-truck gap per fleet size (deterministic seeds, so values
    regenerate exactly)."""
    for label, name in (
        ("primary, production shrinkage", "matched_family.csv"),
        ("sensitivity, no shrinkage", "matched_family_unshrunk.csv"),
    ):
        _matched_family_block(label, TRACKB / name)


def _matched_family_block(label: str, path) -> None:
    print(f"== assumption-matched family ({label}) ==")
    if not path.exists():
        print("  (no artifact)")
        return
    by_k: dict[int, list[dict[str, str]]] = defaultdict(list)
    for r in read(path):
        by_k[int(r["fleet"])].append(r)
    for k in sorted(by_k):
        rows = by_k[k]
        cert = [float(r["certified_pct"]) for r in rows]
        gap = [float(r["gap_per_truck"]) for r in rows]
        rmse = [float(r["price_rmse"]) for r in rows]
        werr = [float(r["w_max_err"]) for r in rows]
        noblock = sum(1 for r in rows if int(r["guard_blocked"]) == 0)
        print(
            f"  K={k:5d}: certified {statistics.mean(cert):.2f}"
            f" +- {statistics.stdev(cert):.2f}%,"
            f" gap/truck ${statistics.mean(gap):.2f},"
            f" price RMSE ${statistics.mean(rmse):.0f},"
            f" max W-err ${statistics.mean(werr):.0f},"
            f" no-block {noblock}/{len(rows)}"
        )


def section_resolve_cost() -> None:
    """Echo the recorded DLP resolve-cost artifact (timings are
    machine-specific, so this checks shape and provenance, not
    values)."""
    print("== dlp resolve-cost artifact (recorded timings) ==")
    path = TRACKB / "dlp_resolve_cost.csv"
    if not path.exists():
        print("  (no resolve-cost artifact)")
        return
    for r in read(path):
        print(
            f"  x{r['replication']}: {r['lanes']} lanes,"
            f" {r['markets']} markets ->"
            f" {r['mean_solve_seconds']} s/solve"
            f" (sd {r['stdev_solve_seconds']}, n={r['repeats']};"
            f" {r['solver']})"
        )


def section_bonferroni() -> None:
    """Simultaneous 98.33% (Bonferroni 0.05/3) bootstrap CIs for the
    headline vf - surrogate differences, seed 20260701, 20k resamples
    -- the paper's multiple-comparison statement."""
    print("== Bonferroni simultaneous CIs (vf - surrogate, 98.33%) ==")
    import random

    vf_src = {
        "tight": SEED30 / "tight" / RUNS,
        "scarce": SEED30 / "scarce" / RUNS,
        "mild": SEED30.parent / "seed30_mild_fitted" / RUNS,
    }
    alpha = 0.05 / 3
    for scen in ("tight", "scarce", "mild"):
        seed_rows = read(SEED30 / scen / RUNS)
        roll = {
            int(r["pair_index"]): float(r["profit"])
            for r in seed_rows
            if r["policy"] == "rollout_teacher"
        }
        sur = {
            int(r["pair_index"]): float(r["profit"])
            for r in seed_rows
            if r["policy"] == "surrogate_linear"
        }
        vf = {
            int(r["pair_index"]): float(r["profit"])
            for r in read(vf_src[scen])
            if r["policy"] == "dual_price_vf"
        }
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


def section_micro() -> None:
    print("== exact attribution at micro scale ==")
    designs = (
        (
            "windowed ex-ante (primary)",
            [d for d in sorted(TRACKB.glob("exact_micro_*_window"))],
        ),
        (
            "stream-prefix (legacy)",
            [
                d
                for d in sorted(TRACKB.glob("exact_micro_*"))
                if not d.name.endswith("_window")
            ],
        ),
    )
    for label, dirs in designs:
        rows = [
            r for d in dirs for r in read(d / "exact_micro_decomposition.csv")
        ]
        n = len(rows)
        total_gap = sum(
            float(r["lp_bound"]) - float(r["v_policy"]) for r in rows
        )
        slack = sum(float(r["relaxation_slack"]) for r in rows)
        dispatch = sum(float(r["dispatch_cost"]) for r in rows)
        accept = sum(float(r["accept_loss"]) for r in rows)
        integral = sum(int(r["lp_integral_optimum"]) for r in rows)
        shares = sorted(
            100
            * float(r["dispatch_cost"])
            / max(1e-9, float(r["lp_bound"]) - float(r["v_policy"]))
            for r in rows
        )
        median = statistics.median(shares)
        zero = sum(1 for s in shares if abs(s) < 0.01)
        print(
            f"  {label}, {n} instances: pooled slack/dispatch/accept ="
            f" {100 * slack / total_gap:.1f}/{100 * dispatch / total_gap:.1f}"
            f"/{100 * accept / total_gap:.1f}%;"
            f" integral optimal solution on {integral}/{n}"
            " (exact rational, integer-cent inputs)"
        )
        print(
            f"    per-instance dispatch share: mean"
            f" {statistics.mean(shares):.1f}%, median {median:.1f}%,"
            f" max {max(shares):.1f}%, zero on {zero}/{n}"
        )


def main() -> None:
    section_portability()
    section_scaling()
    section_scaling_crossfit()
    section_subcritical()
    section_headline_arms()
    section_crossfit()
    section_dlp_cis()
    section_dlp_certs()
    section_matched_family()
    section_resolve_cost()
    section_bonferroni()
    section_micro()


if __name__ == "__main__":
    main()
