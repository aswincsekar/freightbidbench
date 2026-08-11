"""Assumption-matched synthetic family: Theorem 2 on its own terms.

The benchmark violates (A1)-(A4), so no benchmark experiment can test
Theorem 2's asymptotic predictions. This driver builds the idealized
model the theorem analyzes and runs the paper's pipeline on it -- an
exact dual solve of each training realization's relaxation, cell-mean
lane-hour price fitting with shrinkage, the dual-netted backward W
recursion, and the soft-margin gradient policy -- so the distinctive
mechanism (duals price time, gradients price place) is exercised, not
hard-coded.

Model: four markets on a directed cycle (both directions); arrivals
realized as independent Poisson cell counts AT integer hour epochs
(grid alignment); integer occupation time tau; zero within-cell
reward dispersion; NONCONSTANT terminal values V = (500, 400, 500,
400), so fluid thresholds theta = V(o) - V(dest) = +/-100 and the
spatial gradient is materially nonzero; profitable forward lanes
(r = 800; fluid rents 700 or 900 by lane) and unprofitable reverse
lanes (r = -200; fluid-rejected on all four); accepted utilization
50% per market (subcritical, A1); no windows / HOS / yard delays
(A2 exact).

Per (K, train seed, eval seed) cell: solve the training
realization's relaxation to numerical optimality (dense float simplex,
1e-9 tolerance) --- the cell-level arc-flow LP of Lemma 3(c), whose
demand-row duals are the optimal load prices of the
sample path's relaxation, precisely the object Theorem 2 stipulates
(the production benchmark uses a subgradient solver because its
trucks are heterogeneous; in this family trucks are exactly
interchangeable, which degenerates the subgradient's per-truck
response to one path per market and makes the exact LP both correct
and cheap) --- fit lane-hour tables + W from that solve, solve the
evaluation realization's LP independently and evaluate the pathwise
per-truck bound L(lambda_eval) for the certificate denominator, and
simulate the policy on the evaluation stream under the training
tables.

Predictions (Theorem 2 + Corollary): certified fraction -> 1 and
per-truck gap -> 0 as K grows. Diagnostics: fitted-price RMSE against
the known fluid rents, max W-error against the pinned omega*V,
guard-blocked count, and the no-block path fraction.

Dependency-free, deterministic. Usage:
    python3 scripts/run_matched_family.py \
        --output benchmark_runs/trackb/matched_family.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MARKETS = ("A", "B", "C", "D")
TERMINAL = {"A": 500.0, "B": 400.0, "C": 500.0, "D": 400.0}
TAU = 4  # integer hours, rest-inclusive (A2/A4 grid alignment)
HORIZON = 24
REWARD_FORWARD = 800.0  # A->B->C->D->A, homogeneous per cell
REWARD_REVERSE = -200.0  # fluid-rejected: r - theta < 0 on all four
LAMBDA_PER_K = 1.0 / 32.0  # accepted (forward) intensity K/32 per
# market occupies (K/32)*tau = K/8 of the K/4 stationed trucks: 50%
# utilization (subcritical, A1)
MARGIN = 25.0
# The production fitter's empirical-Bayes rule (fit_dual_prices.py):
# cell means are pulled toward the lane mean with this many
# pseudo-observations.
SHRINKAGE_PSEUDO_COUNT = 5.0


def fluid_rent(o: str, d: str, r: float) -> float:
    """(r - theta)_+ with theta = V(o) - V(d): the known fluid rents
    this family's fitted prices should approach."""
    return max(0.0, r - (TERMINAL[o] - TERMINAL[d]))


def lanes() -> list[tuple[str, str, float]]:
    out = []
    m = len(MARKETS)
    for i, o in enumerate(MARKETS):
        out.append((o, MARKETS[(i + 1) % m], REWARD_FORWARD))
        out.append((o, MARKETS[(i - 1) % m], REWARD_REVERSE))
    return out


def realize(k: int, seed: int) -> list[tuple[int, str, str, float]]:
    """Poisson cell counts at integer hour epochs (grid-aligned)."""
    rng = random.Random(seed)
    loads = []
    for h in range(HORIZON):
        for o, d, r in lanes():
            mean = k * LAMBDA_PER_K
            u, p, x, cdf = rng.random(), math.exp(-mean), 0, math.exp(-mean)
            while u > cdf:
                x += 1
                p *= mean / x
                cdf += p
            for _ in range(x):
                loads.append((h, o, d, r))
    return loads


def truck_dp(
    loads: list[tuple[int, str, str, float]],
    lam: list[float],
) -> tuple[dict[tuple[str, int], float], dict[tuple[str, int], int | None]]:
    """Per-truck DP over the realized stream with dual-netted rewards.
    Returns epoch values and, per (market, epoch), the index of the
    load the optimal action dispatches (None = wait)."""
    by_cell: dict[tuple[str, int], list[int]] = {}
    for i, (h, o, d, r) in enumerate(loads):
        by_cell.setdefault((o, h), []).append(i)
    value: dict[tuple[str, int], float] = {}
    choice: dict[tuple[str, int], int | None] = {}
    for m in MARKETS:
        for t in range(HORIZON, HORIZON + TAU + 1):
            value[(m, t)] = TERMINAL[m]
    for h in range(HORIZON - 1, -1, -1):
        for m in MARKETS:
            best, pick = value[(m, h + 1)], None
            for i in by_cell.get((m, h), []):
                _, _, d, r = loads[i]
                cand = r - lam[i] + value[(d, h + TAU)]
                if cand > best + 1e-9:
                    best, pick = cand, i
            value[(m, h)] = best
            choice[(m, h)] = pick
    return value, choice


def solve_duals(
    loads: list[tuple[int, str, str, float]], k: int
) -> tuple[list[float], float]:
    """Optimal duals of the realized instance's relaxation, solved to
    numerical optimality (dense float two-phase simplex, 1e-9
    tolerance): the cell-level hourly arc-flow LP (equal to the chain
    relaxation under grid alignment, Lemma 3(c) of the paper); the
    demand rows' duals are
    the per-cell load prices for every lane, reverse included (when a
    pool empties, backward relocation can enter the optimum, so
    reverse cells are genuine columns, usually at dual zero). The
    returned bound L(lambda) is the per-truck-DP weak-duality bound
    over all loads at those duals. Returns (per-load duals, bound)."""
    import run_dlp_resolve as dlp

    per_market = k // len(MARKETS)
    demand: dict[tuple[str, str, int], int] = {}
    reward_of: dict[tuple[str, str, int], float] = {}
    for h, o, d, r in loads:
        demand[(o, d, h)] = demand.get((o, d, h), 0) + 1
        reward_of[(o, d, h)] = r
    u_keys = sorted(demand)
    z_keys = [(m, h) for h in range(HORIZON) for m in MARKETS]
    u_index = {key: i for i, key in enumerate(u_keys)}
    z_index = {key: len(u_keys) + i for i, key in enumerate(z_keys)}
    n_vars = len(u_keys) + len(z_keys)

    c = [0.0] * n_vars
    for (o, d, h), i in u_index.items():
        r = reward_of[(o, d, h)]
        if h + TAU >= HORIZON:
            r += TERMINAL[d]
            if h == HORIZON - 1:
                r -= TERMINAL[o]
        c[i] = r
    for m in MARKETS:
        c[z_index[(m, HORIZON - 1)]] += TERMINAL[m]

    rows: list[list[float]] = []
    rhs: list[float] = []
    senses: list[str] = []
    demand_row_of: dict[tuple[str, str, int], int] = {}
    for h in range(HORIZON):
        for m in MARKETS:
            row = [0.0] * n_vars
            row[z_index[(m, h)]] = 1.0
            if h > 0:
                row[z_index[(m, h - 1)]] -= 1.0
                for (o, d, hh), i in u_index.items():
                    if o == m and hh == h - 1:
                        row[i] += 1.0
                    if d == m and hh == h - TAU:
                        row[i] -= 1.0
            rows.append(row)
            rhs.append(float(per_market) if h == 0 else 0.0)
            senses.append("=")
    for h in range(HORIZON):
        for m in MARKETS:
            row = [0.0] * n_vars
            any_u = False
            for (o, d, hh), i in u_index.items():
                if o == m and hh == h:
                    row[i] = 1.0
                    any_u = True
            if not any_u:
                continue
            row[z_index[(m, h)]] = -1.0
            rows.append(row)
            rhs.append(0.0)
            senses.append("<=")
    for key, i in u_index.items():
        row = [0.0] * n_vars
        row[i] = 1.0
        demand_row_of[key] = len(rows)
        rows.append(row)
        rhs.append(float(demand[key]))
        senses.append("<=")

    _, duals = dlp.float_simplex_max(c, rows, rhs, senses)
    cell_dual = {key: max(0.0, duals[r_i]) for key, r_i in demand_row_of.items()}
    lam = [cell_dual.get((o, d, h), 0.0) for h, o, d, r in loads]
    value, _ = truck_dp(loads, lam)
    bound = sum(lam) + per_market * sum(value[(m, 0)] for m in MARKETS)
    return lam, bound


def fit_tables(
    loads: list[tuple[int, str, str, float]],
    lam: list[float],
    shrinkage: bool = True,
) -> tuple[
    dict[tuple[str, str, int], float],
    dict[tuple[str, str], float],
    dict[tuple[str, int], float],
]:
    """Fitting from the training solve, using the production fitter's
    actual empirical-Bayes rule (fit_dual_prices.py): each lane-hour
    cell mean is pulled toward the lane mean with
    SHRINKAGE_PSEUDO_COUNT pseudo-observations,
    (sum(cell duals) + 5 * lane_mean) / (n + 5). shrinkage=False keeps
    the raw cell means (the theory-aligned sensitivity variant). The
    W table is the dual-netted backward recursion on the (market,
    hour) grid."""
    cell_sum: dict[tuple[str, str, int], list[float]] = {}
    lane_sum: dict[tuple[str, str], list[float]] = {}
    for i, (h, o, d, r) in enumerate(loads):
        cell_sum.setdefault((o, d, h), []).append(lam[i])
        lane_sum.setdefault((o, d), []).append(lam[i])
    lane = {key: statistics.mean(v) for key, v in lane_sum.items()}
    if shrinkage:
        cell = {
            (o, d, h): (
                sum(v) + SHRINKAGE_PSEUDO_COUNT * lane[(o, d)]
            )
            / (len(v) + SHRINKAGE_PSEUDO_COUNT)
            for (o, d, h), v in cell_sum.items()
        }
    else:
        cell = {key: statistics.mean(v) for key, v in cell_sum.items()}

    by_cell: dict[tuple[str, int], list[int]] = {}
    for i, (h, o, d, r) in enumerate(loads):
        by_cell.setdefault((o, h), []).append(i)
    w: dict[tuple[str, int], float] = {}
    for m in MARKETS:
        for t in range(HORIZON, HORIZON + TAU + 1):
            w[(m, t)] = TERMINAL[m]
    for h in range(HORIZON - 1, -1, -1):
        for m in MARKETS:
            best = w[(m, h + 1)]
            for i in by_cell.get((m, h), []):
                _, _, d, r = loads[i]
                best = max(best, r - lam[i] + w[(d, h + TAU)])
            w[(m, h)] = best
    return cell, lane, w


def rent_of(cell, lane, o, d, h):
    if (o, d, h) in cell:
        return cell[(o, d, h)]
    return lane.get((o, d), 0.0)


def w_of(w, m, t):
    return w.get((m, t), TERMINAL[m])


def simulate(
    loads: list[tuple[int, str, str, float]],
    cell,
    lane,
    w,
    k: int,
) -> tuple[float, int, int]:
    """Closed-loop soft-margin gradient policy: accept iff
    r - lambda_hat + W(d, t+tau) - W(o, t+tau) >= -MARGIN and an idle
    truck is present. Terminal fleet value credited at the horizon
    (in-transit trucks earn their destination's terminal, the paper's
    pipeline convention)."""
    idle = {m: k // len(MARKETS) for m in MARKETS}
    arriving: dict[int, list[str]] = {}
    profit = 0.0
    accepted = 0
    blocked = 0
    current_hour = -1
    for h, o, d, r in loads:
        if h != current_hour:
            for hh in range(current_hour + 1, h + 1):
                for m in arriving.pop(hh, []):
                    idle[m] += 1
            current_hour = h
        g = w_of(w, d, h + TAU) - w_of(w, o, h + TAU)
        score = r - rent_of(cell, lane, o, d, h) + g
        if score < -MARGIN:
            continue
        if idle[o] == 0:
            blocked += 1
            continue
        idle[o] -= 1
        arriving.setdefault(h + TAU, []).append(d)
        profit += r
        accepted += 1
    for pending in arriving.values():
        for m in pending:
            profit += TERMINAL[m]
    for m, n in idle.items():
        profit += n * TERMINAL[m]
    return profit, accepted, blocked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "benchmark_runs" / "trackb" / "matched_family.csv",
    )
    parser.add_argument("--fleet-sizes", default="48,96,192,384,768")
    parser.add_argument("--pairs", type=int, default=30)
    parser.add_argument(
        "--no-shrinkage",
        action="store_true",
        help="fit raw cell means instead of the production shrinkage "
        "rule (sensitivity variant)",
    )
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    for k in (int(s) for s in args.fleet_sizes.split(",")):
        for pair in range(args.pairs):
            train = realize(k, 1000 + 2 * pair)
            evalu = realize(k, 1001 + 2 * pair)
            lam_train, _ = solve_duals(train, k)
            cell, lane, w = fit_tables(
                train, lam_train, shrinkage=not args.no_shrinkage
            )
            _, bound = solve_duals(evalu, k)
            profit, acc, blocked = simulate(evalu, cell, lane, w, k)
            price_sq = [
                (rent_of(cell, lane, o, d, h) - fluid_rent(o, d, r)) ** 2
                for h, o, d, r in evalu
            ]
            w_err = max(
                abs(w_of(w, m, t) - TERMINAL[m])
                for m in MARKETS
                for t in range(HORIZON + 1)
            )
            rows.append(
                {
                    "fleet": k,
                    "pair": pair,
                    "loads": len(evalu),
                    "accepted": acc,
                    "guard_blocked": blocked,
                    "profit": f"{profit:.2f}",
                    "bound": f"{bound:.2f}",
                    "certified_pct": f"{100 * profit / bound:.2f}",
                    "gap_per_truck": f"{(bound - profit) / k:.2f}",
                    "price_rmse": f"{math.sqrt(statistics.mean(price_sq)):.2f}",
                    "w_max_err": f"{w_err:.2f}",
                }
            )
    by_k: dict[int, list[dict[str, object]]] = {}
    for r in rows:
        by_k.setdefault(int(r["fleet"]), []).append(r)
    for k in sorted(by_k):
        cert = [float(r["certified_pct"]) for r in by_k[k]]
        gap = [float(r["gap_per_truck"]) for r in by_k[k]]
        rmse = [float(r["price_rmse"]) for r in by_k[k]]
        werr = [float(r["w_max_err"]) for r in by_k[k]]
        noblock = sum(1 for r in by_k[k] if int(r["guard_blocked"]) == 0)
        sd = statistics.stdev(cert) if len(cert) > 1 else 0.0
        print(
            f"K={k:5d}: certified {statistics.mean(cert):.2f}"
            f" +- {sd:.2f}%,"
            f" gap/truck ${statistics.mean(gap):.2f},"
            f" price RMSE ${statistics.mean(rmse):.0f},"
            f" max W-err ${statistics.mean(werr):.0f},"
            f" no-block {noblock}/{len(by_k[k])}"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
