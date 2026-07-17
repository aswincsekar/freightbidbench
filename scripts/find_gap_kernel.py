"""Search for certified positive-duality-gap kernels (Theorem B(ii)).

Enumerates small relocating-resource instances (trucks with staggered
starts, service budgets as clock proxies; loads with arrival times,
origins/destinations, travel times, rewards) and computes EXACTLY, in
rational arithmetic:

  V*      — the joint optimum (memoized DFS over the joint decision tree);
  LP      — the optimal value of the chain-packing LP over per-truck
            feasible-chain columns, solved by an exact Fraction simplex.

By Dantzig–Wolfe convexification, LP equals min_lambda L(lambda) for the
per-load Lagrangian dual, so LP − V* > 0 is a certified duality gap and
the instance is a replication kernel for Theorem B(ii). A systematic
absence of gaps across the search space is equally informative: it would
say the Lagrangian bound is tight on small instances and the benchmark's
bound-policy gap is not (mostly) a duality gap.

Dependency-free. Usage:
    python3 scripts/find_gap_kernel.py --instances 5000 --seed 1 \
        --output reports/gap_kernel_search.md
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Load:
    load_id: int
    t: int
    origin: int
    dest: int
    tt: int
    reward: int


@dataclass(frozen=True)
class Truck:
    truck_id: int
    market: int
    avail: int
    budget: int


# ----------------------------------------------------------------------------
# Exact joint optimum V* (loads processed in arrival order).
# ----------------------------------------------------------------------------


def joint_optimum(trucks: tuple[Truck, ...], loads: tuple[Load, ...]) -> int:
    @lru_cache(maxsize=None)
    def go(idx: int, states: tuple[tuple[int, int, int], ...]) -> int:
        if idx == len(loads):
            return 0
        load = loads[idx]
        best = go(idx + 1, states)  # reject
        for k, (market, avail, budget) in enumerate(states):
            if budget <= 0 or market != load.origin or avail > load.t:
                continue
            new = list(states)
            new[k] = (load.dest, load.t + load.tt, budget - 1)
            best = max(best, load.reward + go(idx + 1, tuple(new)))
        return best

    return go(0, tuple((tr.market, tr.avail, tr.budget) for tr in trucks))


# ----------------------------------------------------------------------------
# Per-truck feasible chains (columns of the packing LP).
# ----------------------------------------------------------------------------


def truck_chains(truck: Truck, loads: tuple[Load, ...]) -> list[tuple[frozenset[int], int]]:
    chains: dict[frozenset[int], int] = {}

    def go(idx: int, market: int, avail: int, budget: int, taken: frozenset[int], value: int) -> None:
        if taken:
            prev = chains.get(taken)
            if prev is None or value > prev:
                chains[taken] = value
        if budget <= 0:
            return
        for j in range(idx, len(loads)):
            load = loads[j]
            if load.origin == market and avail <= load.t:
                go(
                    j + 1,
                    load.dest,
                    load.t + load.tt,
                    budget - 1,
                    taken | {load.load_id},
                    value + load.reward,
                )

    go(0, truck.market, truck.avail, truck.budget, frozenset(), 0)
    return sorted(chains.items(), key=lambda kv: -kv[1])


# ----------------------------------------------------------------------------
# Exact simplex (max c^T x, A x <= b, x >= 0) in Fractions, Bland's rule.
# ----------------------------------------------------------------------------


def simplex_max(c: list[Fraction], a: list[list[Fraction]], b: list[Fraction]) -> Fraction:
    m, n = len(a), len(c)
    # Tableau: rows 0..m-1 constraints (with slacks), row m objective.
    tab = [row[:] + [Fraction(int(i == j)) for j in range(m)] + [b[i]] for i, row in enumerate(a)]
    tab.append([-cj for cj in c] + [Fraction(0)] * m + [Fraction(0)])
    basis = [n + i for i in range(m)]
    total = n + m
    while True:
        # Bland: entering = smallest index with negative reduced cost.
        enter = next((j for j in range(total) if tab[m][j] < 0), None)
        if enter is None:
            return tab[m][total]
        # Ratio test (Bland ties by smallest basis index).
        leave, best = None, None
        for i in range(m):
            if tab[i][enter] > 0:
                ratio = tab[i][total] / tab[i][enter]
                if best is None or ratio < best or (ratio == best and basis[i] < basis[leave]):
                    best, leave = ratio, i
        if leave is None:
            raise ValueError("unbounded LP (should not happen for packing)")
        piv = tab[leave][enter]
        tab[leave] = [v / piv for v in tab[leave]]
        for i in range(m + 1):
            if i != leave and tab[i][enter] != 0:
                factor = tab[i][enter]
                tab[i] = [vi - factor * vl for vi, vl in zip(tab[i], tab[leave])]
        basis[leave] = enter


def chain_packing_lp(trucks: tuple[Truck, ...], loads: tuple[Load, ...]) -> Fraction:
    cols: list[tuple[int, frozenset[int], int]] = []
    for tr in trucks:
        for loadset, value in truck_chains(tr, loads):
            cols.append((tr.truck_id, loadset, value))
    if not cols:
        return Fraction(0)
    c = [Fraction(value) for _, _, value in cols]
    a: list[list[Fraction]] = []
    b: list[Fraction] = []
    for load in loads:  # each load used at most once
        a.append([Fraction(int(load.load_id in s)) for _, s, _ in cols])
        b.append(Fraction(1))
    for tr in trucks:  # each truck runs at most one chain
        a.append([Fraction(int(tid == tr.truck_id)) for tid, _, _ in cols])
        b.append(Fraction(1))
    return simplex_max(c, a, b)


# ----------------------------------------------------------------------------
# Random instance sampler.
# ----------------------------------------------------------------------------


def sample_instance(rng: random.Random) -> tuple[tuple[Truck, ...], tuple[Load, ...]]:
    n_markets = rng.choice([3, 4])
    n_trucks = rng.choice([2, 3, 4])
    n_loads = rng.choice([4, 5, 6, 7])
    trucks = tuple(
        Truck(k, rng.randrange(n_markets), rng.choice([0, 0, 1]), rng.choice([1, 2, 2]))
        for k in range(n_trucks)
    )
    loads = []
    for i in range(n_loads):
        origin = rng.randrange(n_markets)
        dest = rng.choice([m for m in range(n_markets) if m != origin])
        loads.append(
            Load(i, rng.randrange(0, 6), origin, dest, rng.choice([1, 2]), rng.randrange(6, 15))
        )
    loads.sort(key=lambda l: (l.t, l.load_id))
    loads = tuple(
        Load(i, l.t, l.origin, l.dest, l.tt, l.reward) for i, l in enumerate(loads)
    )
    return trucks, loads


def describe(trucks: tuple[Truck, ...], loads: tuple[Load, ...]) -> str:
    lines = ["trucks (id, market, avail, budget):"]
    lines += [f"  T{t.truck_id}: M{t.market} avail={t.avail} budget={t.budget}" for t in trucks]
    lines.append("loads (id, t, origin->dest, tt, reward):")
    lines += [
        f"  L{l.load_id}: t={l.t} M{l.origin}->M{l.dest} tt={l.tt} r={l.reward}" for l in loads
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "gap_kernel_search.md")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    found: list[tuple[Fraction, int, tuple[Truck, ...], tuple[Load, ...], int, Fraction]] = []
    for trial in range(args.instances):
        trucks, loads = sample_instance(rng)
        v_star = joint_optimum(trucks, loads)
        lp = chain_packing_lp(trucks, loads)
        gap = lp - v_star
        if gap > 0:
            rel = gap / max(1, v_star)
            found.append((rel, trial, trucks, loads, v_star, lp))
    found.sort(key=lambda item: -item[0])

    lines = [
        "# Gap-Kernel Search (Theorem B(ii))",
        "",
        f"Instances searched: {args.instances} (seed {args.seed}). "
        f"Certified positive duality gaps found: {len(found)} "
        f"({100.0 * len(found) / args.instances:.2f}%).",
        "",
        "Certificate: LP value of the chain-packing relaxation (exact",
        "Fraction simplex) equals min_lambda L(lambda) by Dantzig-Wolfe;",
        "V* by exact joint enumeration. gap = LP - V* in exact rationals.",
        "",
    ]
    for rel, trial, trucks, loads, v_star, lp in found[: args.top]:
        lines += [
            f"## Kernel (trial {trial}): V* = {v_star}, LP = {lp} "
            f"(= {float(lp):.3f}), gap = {lp - v_star} "
            f"({100 * float(rel):.1f}% of V*)",
            "```",
            describe(trucks, loads),
            "```",
            "",
        ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"{len(found)}/{args.instances} instances with certified gap; "
        f"max relative gap "
        f"{(100 * float(found[0][0])):.1f}% of V*" if found else "no gaps found",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
