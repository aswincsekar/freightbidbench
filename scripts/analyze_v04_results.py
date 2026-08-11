"""Regenerate the v0.4 methods-paper tables and statistics from raw CSVs.

Consumes the artifacts of scripts/run_30seed_program.sh and emits every
number in the paper's empirical tables:

  Table 1 (methods comparison): per-scenario policy means of retention
    and latency; the paired dual_price_vf - surrogate_linear delta in
    percentage points and in dollars, with paired-bootstrap 95% CIs;
    Wilcoxon signed-rank p; exact sign-test p; win counts.
  Table 2 (certificates): per-scenario certified fraction
    profit / best_bound for dual_price_vf and rollout_teacher across
    the ten bound-solved eval seeds (mean and min-max), plus mean
    bound-solve wall time.

Dependency-free (Python standard library only) and deterministic
(fixed bootstrap seed).

Usage:
    python3 scripts/analyze_v04_results.py \
        --seed30-dir benchmark_runs/v04_dev/seed30 \
        --mild-dir benchmark_runs/v04_dev/seed30_mild_fitted \
        --certs-dir benchmark_runs/v04_dev/certs \
        --output-dir benchmark_runs/v04_dev/analysis
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from pathlib import Path

RUNS_FILENAME = "dual_price_experiment_runs.csv"
BOUND_FILENAME = "lagrangian_bound_summary.csv"
POLICY_A = "dual_price_vf"
POLICY_B = "surrogate_linear"


def read_runs(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_scenario_rows(args: argparse.Namespace) -> dict[str, list[dict[str, str]]]:
    rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for scen in ("tight", "scarce"):
        run_csv = Path(args.seed30_dir) / scen / RUNS_FILENAME
        for row in read_runs(run_csv):
            rows[row["scenario"]].append(row)

    # The paper's corrected mild rows merge two artifacts: the original
    # mild run supplies the baselines and the rollout teacher; the
    # fitted-tables rerun supplies dual_price and dual_price_vf (whose
    # original rows used zero-fallback tables). Retention for the
    # replaced rows is recomputed against the original run's rollout
    # profit on the same pair.
    original = read_runs(Path(args.seed30_dir) / "mild" / RUNS_FILENAME)
    fitted = read_runs(Path(args.mild_dir) / RUNS_FILENAME)
    fitted_policies = {r["policy"] for r in fitted}
    rollout_profit = {
        r["pair_index"]: float(r["profit"])
        for r in original
        if r["policy"] == "rollout_teacher"
    }
    for row in original:
        if row["policy"] not in fitted_policies:
            rows[row["scenario"]].append(row)
    for row in fitted:
        row = dict(row)
        base = rollout_profit.get(row["pair_index"])
        if base and not row.get("retention_vs_rollout"):
            row["retention_vs_rollout"] = f"{float(row['profit']) / base:.6f}"
        rows[row["scenario"]].append(row)
    return rows


def paired_series(
    rows: list[dict[str, str]], field: str
) -> tuple[list[float], list[float]]:
    by_pair: dict[int, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if row["policy"] in (POLICY_A, POLICY_B) and row[field] not in ("", None):
            by_pair[int(row["pair_index"])][row["policy"]] = float(row[field])
    pairs = [p for p in sorted(by_pair) if len(by_pair[p]) == 2]
    a = [by_pair[p][POLICY_A] for p in pairs]
    b = [by_pair[p][POLICY_B] for p in pairs]
    return a, b


def bootstrap_ci(
    deltas: list[float], resamples: int, rng: random.Random
) -> tuple[float, float]:
    n = len(deltas)
    means = sorted(
        sum(deltas[rng.randrange(n)] for _ in range(n)) / n
        for _ in range(resamples)
    )
    lo = means[int(0.025 * resamples)]
    hi = means[int(0.975 * resamples) - 1]
    return lo, hi


def wilcoxon_signed_rank_p(deltas: list[float]) -> float:
    """Two-sided p for the signed-rank test.

    Normal approximation without continuity correction; zero
    differences dropped; average ranks for tied |d| groups, with the
    matching variance reduction sum(t^3 - t)/48 per tie group.
    """
    nonzero = [d for d in deltas if d != 0.0]
    n = len(nonzero)
    if n == 0:
        return 1.0
    ordered = sorted(nonzero, key=abs)
    ranks = [0.0] * n
    tie_correction = 0.0
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(ordered[j + 1]) == abs(ordered[i]):
            j += 1
        mean_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = mean_rank
        t = j - i + 1
        tie_correction += (t**3 - t) / 48
        i = j + 1
    w_plus = sum(r for r, d in zip(ranks, ordered) if d > 0)
    mean_w = n * (n + 1) / 4
    var_w = n * (n + 1) * (2 * n + 1) / 24 - tie_correction
    if var_w <= 0:
        return 1.0
    z = (w_plus - mean_w) / math.sqrt(var_w)
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def sign_test_p(deltas: list[float]) -> tuple[int, int, float]:
    """Wins for A, effective n, exact two-sided binomial p."""
    wins = sum(1 for d in deltas if d > 0)
    n = sum(1 for d in deltas if d != 0.0)
    if n == 0:
        return 0, 0, 1.0
    tail = sum(math.comb(n, k) for k in range(min(wins, n - wins) + 1))
    p = min(1.0, 2 * tail / 2**n)
    return wins, n, p


def analyze_methods(
    rows_by_scen: dict[str, list[dict[str, str]]],
    resamples: int,
    seed: int,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for scen in sorted(rows_by_scen):
        rows = rows_by_scen[scen]
        means: dict[str, dict[str, float]] = defaultdict(dict)
        by_policy: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_policy[row["policy"]].append(row)
        for policy, prows in by_policy.items():
            rets = [
                float(r["retention_vs_rollout"])
                for r in prows
                if r["retention_vs_rollout"] not in ("", None)
            ]
            means[policy]["retention_pct"] = (
                100 * sum(rets) / len(rets) if rets else 100.0
            )
            means[policy]["latency_ms"] = sum(
                float(r["mean_latency_ms"]) for r in prows
            ) / len(prows)

        ret_a, ret_b = paired_series(rows, "retention_vs_rollout")
        prof_a, prof_b = paired_series(rows, "profit")
        pp = [100 * (x - y) for x, y in zip(ret_a, ret_b)]
        dollars = [x - y for x, y in zip(prof_a, prof_b)]
        rng = random.Random(seed)
        pp_ci = bootstrap_ci(pp, resamples, rng)
        usd_ci = bootstrap_ci(dollars, resamples, rng)
        wins, n_eff, p_sign = sign_test_p(pp)
        out.append(
            {
                "scenario": scen,
                "policy_means": dict(means),
                "delta_pp_mean": sum(pp) / len(pp),
                "delta_pp_ci95": pp_ci,
                "delta_usd_mean": sum(dollars) / len(dollars),
                "delta_usd_ci95": usd_ci,
                "wilcoxon_p": wilcoxon_signed_rank_p(pp),
                "sign_wins": wins,
                "sign_n": n_eff,
                "sign_p": p_sign,
                "n_pairs": len(pp),
            }
        )
    return out


def analyze_certs(
    rows_by_scen: dict[str, list[dict[str, str]]], certs_dir: Path
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    profit_lookup: dict[tuple[str, str, str], float] = {}
    for scen, rows in rows_by_scen.items():
        for row in rows:
            profit_lookup[(scen, row["eval_seed"], row["policy"])] = float(
                row["profit"]
            )
    for scen in ("tight", "scarce"):
        fracs: dict[str, list[float]] = defaultdict(list)
        elapsed: list[float] = []
        for bound_dir in sorted(certs_dir.glob(f"{scen}_*")):
            summary = bound_dir / BOUND_FILENAME
            if not summary.exists():
                continue
            with summary.open(newline="", encoding="utf-8") as handle:
                rec = next(csv.DictReader(handle))
            bound = float(rec["best_bound"])
            elapsed.append(float(rec["elapsed_seconds"]))
            for policy in (POLICY_A, "rollout_teacher"):
                key = (scen, rec["eval_seed"], policy)
                if key in profit_lookup:
                    fracs[policy].append(100 * profit_lookup[key] / bound)
        row: dict[str, object] = {"scenario": scen, "instances": len(elapsed)}
        for policy, values in fracs.items():
            row[f"{policy}_mean_pct"] = sum(values) / len(values)
            row[f"{policy}_min_pct"] = min(values)
            row[f"{policy}_max_pct"] = max(values)
        row["mean_solve_seconds"] = sum(elapsed) / len(elapsed) if elapsed else 0.0
        out.append(row)
    return out


SCALING_BOUND_DIRS = {
    "tight_x05": "benchmark_runs/v04_dev/scaling/tight_x05_warm",
    "tight_x1": "benchmark_runs/lagrangian_bound_full_v6_warm",
    "tight_x2": "benchmark_runs/v04_dev/scaling/tight_x2_warm",
}


def analyze_scaling(repo_root: Path, diag_csv: Path) -> list[dict[str, object]]:
    """Table 3: proportional-scaling cells (in-sample, pair 0).

    Policy and rollout profits come from the scaling rollout
    diagnostic run; each cell's bound comes from its
    plateau-converged solve (the x1 cell reuses the deep tight solve
    --- same scenario, same seed, more iterations).
    """
    profits: dict[tuple[str, str], float] = {}
    retention: dict[str, float] = {}
    for row in read_runs(diag_csv):
        profits[(row["scenario"], row["policy"])] = float(row["profit"])
        if row["policy"] == POLICY_A and row["retention_vs_rollout"]:
            retention[row["scenario"]] = 100 * float(
                row["retention_vs_rollout"]
            )
    out: list[dict[str, object]] = []
    for cell, bound_dir in SCALING_BOUND_DIRS.items():
        summary = repo_root / bound_dir / BOUND_FILENAME
        with summary.open(newline="", encoding="utf-8") as handle:
            rec = next(csv.DictReader(handle))
        bound = float(rec["best_bound"])
        fleet = int(rec["fleet_size_evaluated"])
        policy = profits[(cell, POLICY_A)]
        out.append(
            {
                "cell": cell,
                "K": fleet,
                "bound_per_k": bound / fleet,
                "policy_per_k": policy / fleet,
                "policy_vs_rollout_pct": retention.get(cell),
                "certified_gap_pct": 100 * (1 - policy / bound),
            }
        )
    return out


def write_report(
    methods: list[dict[str, object]],
    certs: list[dict[str, object]],
    scaling: list[dict[str, object]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# v0.4 analysis (regenerated from raw CSVs)", ""]
    lines.append("## Table 1 inputs: methods comparison")
    for m in methods:
        lines.append(f"\n### {m['scenario']} (n = {m['n_pairs']} pairs)")
        for policy, vals in sorted(m["policy_means"].items()):  # type: ignore[union-attr]
            lines.append(
                f"- {policy}: retention {vals['retention_pct']:.1f}%,"
                f" latency {vals['latency_ms'] * 1000:.3f} us/decision"
                if vals["latency_ms"] < 1
                else f"- {policy}: retention {vals['retention_pct']:.1f}%,"
                f" latency {vals['latency_ms']:.2f} ms"
            )
        lo, hi = m["delta_pp_ci95"]  # type: ignore[misc]
        ulo, uhi = m["delta_usd_ci95"]  # type: ignore[misc]
        lines.append(
            f"- paired vf-surrogate: {m['delta_pp_mean']:+.1f} pp"
            f" [CI95 {lo:+.1f}, {hi:+.1f}];"
            f" ${m['delta_usd_mean']:+,.0f} [CI95 {ulo:+,.0f}, {uhi:+,.0f}]"
        )
        lines.append(
            f"- Wilcoxon p = {m['wilcoxon_p']:.3f};"
            f" sign test {m['sign_wins']}/{m['sign_n']} wins,"
            f" p = {m['sign_p']:.3f}"
        )
    lines.append("\n## Table 2 inputs: certificates")
    for c in certs:
        lines.append(f"\n### {c['scenario']} ({c['instances']} instances)")
        for policy in (POLICY_A, "rollout_teacher"):
            key = f"{policy}_mean_pct"
            if key in c:
                lines.append(
                    f"- {policy}: certified >= {c[key]:.1f}% of hindsight"
                    f" optimum ({c[f'{policy}_min_pct']:.1f}"
                    f"--{c[f'{policy}_max_pct']:.1f})"
                )
        lines.append(
            f"- mean bound-solve time: {float(c['mean_solve_seconds']) / 60:.0f}"
            " minutes"
        )
    lines.append("\n## Table 3 inputs: proportional scaling (tight, pair 0)")
    for s in scaling:
        lines.append(
            f"- {s['cell']} (K={s['K']}): bound/K ${s['bound_per_k']:,.0f},"
            f" policy/K ${s['policy_per_k']:,.0f},"
            f" policy vs rollout {s['policy_vs_rollout_pct']:.1f}%,"
            f" certified gap {s['certified_gap_pct']:.1f}%"
        )
    report = output_dir / "v04_analysis_report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report}")
    print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed30-dir", default="benchmark_runs/v04_dev/seed30")
    parser.add_argument(
        "--mild-dir", default="benchmark_runs/v04_dev/seed30_mild_fitted"
    )
    parser.add_argument("--certs-dir", default="benchmark_runs/v04_dev/certs")
    parser.add_argument(
        "--output-dir", default="benchmark_runs/v04_dev/analysis"
    )
    parser.add_argument(
        "--scaling-diag-csv",
        default="benchmark_runs/v04_dev/scaling_rollout_diag/"
        "dual_price_experiment_runs.csv",
    )
    parser.add_argument("--bootstrap-resamples", type=int, default=20000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260701)
    args = parser.parse_args()

    rows_by_scen = load_scenario_rows(args)
    methods = analyze_methods(
        rows_by_scen, args.bootstrap_resamples, args.bootstrap_seed
    )
    certs = analyze_certs(rows_by_scen, Path(args.certs_dir))
    scaling = analyze_scaling(Path("."), Path(args.scaling_diag_csv))
    write_report(methods, certs, scaling, Path(args.output_dir))


if __name__ == "__main__":
    main()
