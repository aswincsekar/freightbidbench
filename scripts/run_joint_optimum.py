"""Exact joint optimum vs exact relaxation on micro benchmark instances.

The certificate gap L - V^pi observed at benchmark scale cannot be
attributed between relaxation slack and policy loss without the exact
joint optimum V*, which fixes neither the accept rule nor the dispatch
rule (the exact hindsight DP of run_hindsight_bound.py fixes dispatch,
so it lower-bounds V*). On truncated micro instances --- the first L
loads of a real stream against the first K trucks of the benchmark's
proportional placement, under the same feasibility dynamics the
Lagrangian solver uses (transition_under_accept) --- this script
computes four exact or simulated quantities on one objective
(profits plus terminal fleet value):

  lp_bound   exact min_lambda L via the chain-packing LP (Dantzig-
             Wolfe equivalence, Lemma dw in the paper), solved with
             the exact rational simplex from find_gap_kernel;
  v_joint    exact joint accept-and-assign optimum (memoized DFS);
  v_fixed    exact best accept sequence under the benchmark's fixed
             dispatch rule (run_hindsight_bound);
  v_policy   the dual_price_vf policy simulated closed-loop.

Per-instance decomposition:
  relaxation slack = lp_bound - v_joint
  dispatch cost    = v_joint - v_fixed
  accept loss      = v_fixed - v_policy

Dependency-free (Python standard library only).

Usage:
    python3 scripts/run_joint_optimum.py \
        --config configs/freightbidbench_v03_scenarios.json \
        --scenario tight --trucks 3 --loads 12 --instances 10 \
        --output-dir benchmark_runs/trackb/exact_micro_tight
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import find_gap_kernel as kern  # noqa: E402


def cents(value: float) -> int:
    """Quantize a monetary float to integer cents. All four exact
    quantities (chain LP, joint DP, fixed-dispatch DP, terminals) are
    computed over integer cents, so 'exact rational arithmetic' means
    exact over quantized monetary inputs --- not over raw binary
    floats, whose rationalization admits ~1e-13 pseudo-slack. The
    pre-round to six decimals makes quantization consistent across
    the feasibility layer's two profit code paths, whose results can
    differ in the last ulp and would otherwise straddle a half-cent
    boundary."""
    return round(round(value, 6) * 100)
import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_hindsight_bound as hb  # noqa: E402
import run_lagrangian_bound as lag  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


def joint_optimum(
    starts: list[lag.TruckDPState],
    loads: list[dict[str, object]],
    omega: float,
    state_values: dict[str, float],
) -> float:
    """Exact joint accept-and-assign optimum by memoized DFS.

    States are canonicalized by sorting per-truck clock tuples, so
    interchangeable trucks collapse; the same real feasibility layer
    as the Lagrangian solver decides transitions.
    """
    memo: dict[tuple[int, tuple], int] = {}

    def terminal(states: tuple[lag.TruckDPState, ...]) -> int:
        return sum(
            cents(omega * state_values.get(s.location, 0.0)) for s in states
        )

    def canon(states: tuple[lag.TruckDPState, ...]) -> tuple:
        return tuple(
            sorted(
                (s.location, s.available_time, s.drive_used, s.duty_used)
                for s in states
            )
        )

    def go(idx: int, states: tuple[lag.TruckDPState, ...]) -> int:
        if idx == len(loads):
            return terminal(states)
        key = (idx, canon(states))
        if key in memo:
            return memo[key]
        best = go(idx + 1, states)  # reject
        load = loads[idx]
        origin = str(load["origin_state"])
        for i, s in enumerate(states):
            # Market gate: mirrors the solver's frontier-by-location
            # lookup and apply_accept's fleet[origin] candidacy.
            if s.location != origin:
                continue
            accepted, profit, ns = lag.transition_under_accept(s, load, f"t{i}")
            if accepted:
                nxt = states[:i] + (ns,) + states[i + 1 :]
                best = max(best, cents(profit) + go(idx + 1, nxt))
        memo[key] = best
        return best

    return go(0, tuple(starts)) / 100.0


def truck_chains(
    start: lag.TruckDPState,
    loads: list[dict[str, object]],
    omega: float,
    state_values: dict[str, float],
) -> list[tuple[frozenset[int], float]]:
    """Enumerate every feasible service chain of one truck, with value
    equal to chain profits plus the terminal value of its final market
    (the empty chain carries the start market's terminal value)."""
    chains: list[tuple[frozenset[int], int]] = []

    def go(idx: int, state: lag.TruckDPState, taken: frozenset[int], value: int) -> None:
        chains.append(
            (
                taken,
                value + cents(omega * state_values.get(state.location, 0.0)),
            )
        )
        for j in range(idx, len(loads)):
            if state.location != str(loads[j]["origin_state"]):
                continue
            accepted, profit, ns = lag.transition_under_accept(
                state, loads[j], "probe"
            )
            if accepted:
                go(
                    j + 1,
                    ns,
                    taken | {int(loads[j]["load_id"])},
                    value + cents(profit),
                )

    go(0, start, frozenset(), 0)
    return chains


def chain_packing_bound(
    starts: list[lag.TruckDPState],
    loads: list[dict[str, object]],
    omega: float,
    state_values: dict[str, float],
) -> tuple[float, bool, int]:
    """Exact min_lambda L via the chain-packing LP in exact rationals.
    Also reports the longest feasible chain across all trucks (the
    instance-depth diagnostic the micro study conditions on).

    The per-resource convexity constraint is an equality (a truck that
    runs no chain still stands somewhere and earns that market's
    terminal value, which may be negative). We keep the simplex in
    <=-form by normalizing every chain's value against its truck's
    stand-still value and adding the stand-still total back as a
    constant.
    """
    cols: list[tuple[int, frozenset[int], Fraction]] = []
    constant = Fraction(0)
    max_chain = 0
    for k, start in enumerate(starts):
        chains = truck_chains(start, loads, omega, state_values)
        empty_value = next(
            Fraction(v, 100) for ids, v in chains if not ids
        )
        constant += empty_value
        for ids, value in chains:
            max_chain = max(max_chain, len(ids))
            if ids:
                cols.append((k, ids, Fraction(value, 100) - empty_value))
    if not cols:
        return float(constant), True, max_chain
    c = [v for _, _, v in cols]
    a: list[list[Fraction]] = []
    b: list[Fraction] = []
    for load in loads:
        lid = int(load["load_id"])
        a.append([Fraction(int(lid in ids)) for _, ids, _ in cols])
        b.append(Fraction(1))
    for k in range(len(starts)):
        a.append([Fraction(int(kk == k)) for kk, _, _ in cols])
        b.append(Fraction(1))
    value, x = kern.simplex_max(c, a, b)
    # Exact integrality check (Fractions): an integral optimum is a
    # feasible joint assignment, so it certifies min L = V* exactly,
    # independent of any floating-point display rounding.
    integral = all(xi == 0 or xi == 1 for xi in x)
    return float(value + constant), integral, max_chain


def fixed_dispatch_optimum(
    loads: list[dict[str, object]],
    fleet0: dict[str, list[object]],
    scenario: base.Scenario,
    state_values: dict[str, float],
) -> float:
    """Exact best accept sequence under the benchmark's fixed dispatch
    rule, by the same memoized DFS as joint_optimum but with the truck
    choice delegated to apply_accept. Replaces the standalone hindsight
    DP here because windowed instances explode its state encoding; on
    the legacy prefix instances the two agree.
    """
    memo: dict[tuple[int, tuple], int] = {}

    def canon(fleet: dict[str, list[object]]) -> tuple:
        return tuple(
            sorted(
                (t.state, t.available_time, t.drive_used_hours, t.duty_used_hours)
                for trucks in fleet.values()
                for t in trucks
            )
        )

    omega = base.terminal_value_weight(scenario)

    def go(idx: int, fleet: dict[str, list[object]]) -> int:
        if idx == len(loads):
            # Per-truck cent quantization, matching joint_optimum and
            # truck_chains exactly (quantizing the fleet total instead
            # differs by up to one cent per truck).
            return sum(
                cents(omega * state_values.get(t.state, 0.0))
                for trucks in fleet.values()
                for t in trucks
            )
        key = (idx, canon(fleet))
        if key in memo:
            return memo[key]
        best = go(idx + 1, fleet)  # reject
        load = loads[idx]
        trial = feas.copy_fleet(fleet)
        assignment = feas.apply_accept(trial, load, float(load["hour"]))
        if assignment.accepted:
            best = max(best, cents(assignment.profit) + go(idx + 1, trial))
        memo[key] = best
        return best

    return go(0, fleet0) / 100.0


def policy_value_cents(
    loads: list[dict[str, object]],
    fleet0: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
) -> float:
    """Simulate dual_price_vf on the same integer-cent ledger as the
    three exact quantities: per-accept profits and per-truck terminal
    values quantized identically, so all four decomposition components
    are evaluated on one quantized objective."""
    fleet = feas.copy_fleet(fleet0)
    total = 0
    for idx, load in enumerate(loads):
        wants, _, _ = sc.choose_action(
            "dual_price_vf",
            load,
            fleet,
            lanes,
            scenario,
            state_values,
            None,
            idx,
        )
        if not wants:
            continue
        assignment = feas.apply_accept(fleet, load, float(load["hour"]))
        if assignment.accepted:
            total += cents(assignment.profit)
    omega = base.terminal_value_weight(scenario)
    total += sum(
        cents(omega * state_values.get(t.state, 0.0))
        for trucks in fleet.values()
        for t in trucks
    )
    return total / 100.0


def micro_instance(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    seed: int,
    n_trucks: int,
    n_loads: int,
    window_hours: float = 0.0,
    top_markets: int = 0,
) -> tuple[list[dict[str, object]], list[tuple[str, float]]]:
    """Micro instance construction.

    window_hours == 0 (legacy): first L loads of the real stream, with
    K trucks placed round-robin over the window's most frequent origin
    markets. This placement observes the load prefix, and the dense
    prefix spans under two hours, so feasible chains are short --- kept
    only for comparison with the original study.

    window_hours > 0 (the ex-ante design): a window start is drawn
    uniformly over the horizon, the window's loads are stride-thinned
    to L so arrivals span the full window (long chains become
    feasible), and the K trucks are placed ex ante --- an FAF-weighted
    draw over origin states using only lane data, never the realized
    loads.
    """
    all_loads = sc.generate_loads_with_seed(lanes, scenario, seed)
    if window_hours <= 0:
        loads = all_loads[:n_loads]
        counts: dict[str, int] = {}
        for load in loads:
            origin = str(load["origin_state"])
            counts[origin] = counts.get(origin, 0) + 1
        top = sorted(counts, key=lambda m: (-counts[m], m))
        placement = [(top[i % len(top)], 0.0) for i in range(n_trucks)]
        return loads, placement

    weights: dict[str, float] = {}
    for lane in lanes:
        state = str(lane["origin_state"])
        weights[state] = weights.get(state, 0.0) + base.as_float(
            lane["faf_tons_2024"]
        )
    region = set(weights)
    if top_markets > 0:
        # Ex-ante regional restriction: the top-M origin markets by FAF
        # weight, a rule of the lane data only. Keeping both endpoints
        # inside the region lets chains stay serviceable, so chain
        # conflicts between trucks can arise.
        region = set(
            sorted(weights, key=lambda s: (-weights[s], s))[:top_markets]
        )
    window_rng = random.Random(seed + 101)
    start = window_rng.uniform(0.0, max(0.0, scenario.horizon_hours - window_hours))
    window = [
        load
        for load in all_loads
        if start <= float(load["hour"]) < start + window_hours
        and str(load["origin_state"]) in region
        and str(load["destination_state"]) in region
    ]
    if len(window) > n_loads:
        idx = sorted(
            {
                round(i * (len(window) - 1) / (n_loads - 1))
                for i in range(n_loads)
            }
        )
        window = [window[i] for i in idx]

    # Ex-ante placement, mirroring the benchmark's initial_fleet rule:
    # independent FAF-weighted draws (with replacement, so same-market
    # starts occur naturally) using only lane data.
    placement_rng = random.Random(seed + 31)
    states = sorted(region)
    chosen: list[str] = []
    for _ in range(n_trucks):
        total = sum(weights[s] for s in states)
        pick = placement_rng.uniform(0.0, total)
        acc = 0.0
        for s in states:
            acc += weights[s]
            if pick <= acc:
                chosen.append(s)
                break
        else:
            chosen.append(states[-1])
    placement = [(state, start) for state in chosen]
    return window, placement


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/freightbidbench_v03_scenarios.json")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--trucks", type=int, default=3)
    parser.add_argument("--loads", type=int, default=12)
    parser.add_argument("--instances", type=int, default=10)
    parser.add_argument(
        "--window-hours",
        type=float,
        default=0.0,
        help="0 keeps the legacy stream-prefix design; > 0 samples a "
        "random window with stride-thinned loads and ex-ante FAF-"
        "weighted truck placement.",
    )
    parser.add_argument(
        "--top-markets",
        type=int,
        default=0,
        help="restrict windowed instances to the top-M FAF origin "
        "markets (ex-ante rule; both load endpoints inside), so trucks "
        "share a region and chain conflicts arise. 0 disables.",
    )
    parser.add_argument("--first-seed", type=int, default=20260509)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    with (args.config if args.config.is_absolute() else ROOT / args.config).open(
        encoding="utf-8"
    ) as handle:
        config = json.load(handle)
    scenario = lag.scenario_from_config(config["scenarios"][args.scenario])
    lanes = base.load_csv(base.LANES)
    state_values = base.build_state_values(lanes, scenario)
    omega = base.terminal_value_weight(scenario)

    rows: list[dict[str, object]] = []
    for i in range(args.instances):
        seed = args.first_seed + 2 * i
        loads, placement = micro_instance(
            lanes, scenario, seed, args.trucks, args.loads,
            window_hours=args.window_hours,
            top_markets=args.top_markets,
        )
        starts = [
            lag.TruckDPState(
                location=market,
                available_time=avail,
                drive_used=0.0,
                duty_used=0.0,
                value=0.0,
            )
            for market, avail in placement
        ]
        fleet = {}
        for j, (market, avail) in enumerate(placement):
            fleet.setdefault(market, []).append(
                lag.feas.TruckState(f"t{j}", market, avail)
            )

        lp, integral, max_chain = chain_packing_bound(
            starts, loads, omega, state_values
        )
        v_joint = joint_optimum(starts, loads, omega, state_values)
        v_fixed = fixed_dispatch_optimum(loads, fleet, scenario, state_values)
        v_policy = policy_value_cents(
            loads, fleet, lanes, scenario, state_values
        )

        rows.append(
            {
                "scenario": scenario.name,
                "seed": seed,
                "trucks": args.trucks,
                "loads": len(loads),
                "window_hours": args.window_hours,
                "top_markets": args.top_markets,
                "window_start": f"{placement[0][1]:.2f}",
                "max_chain_len": max_chain,
                "lp_bound": f"{lp:.2f}",
                "lp_integral_optimum": int(integral),
                "v_joint": f"{v_joint:.2f}",
                "v_fixed": f"{v_fixed:.2f}",
                "v_policy": f"{v_policy:.2f}",
                "relaxation_slack": f"{lp - v_joint:.2f}",
                "dispatch_cost": f"{v_joint - v_fixed:.2f}",
                "accept_loss": f"{v_fixed - v_policy:.2f}",
            }
        )
        print(
            f"seed {seed}: LP {lp:,.0f} >= V*_joint {v_joint:,.0f} >= "
            f"V*_fixed {v_fixed:,.0f}; policy {v_policy:,.0f} | "
            f"slack {lp - v_joint:,.0f} vs dispatch {v_joint - v_fixed:,.0f}"
            f" vs accept {v_fixed - v_policy:,.0f}"
        )

    out = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    path = out / "exact_micro_decomposition.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    total_gap = sum(float(r["lp_bound"]) - float(r["v_policy"]) for r in rows)
    slack = sum(float(r["relaxation_slack"]) for r in rows)
    print(
        f"\n{len(rows)} instances: relaxation slack is "
        f"{100 * slack / total_gap:.0f}% of the total certificate gap."
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
