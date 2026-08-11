"""Re-solving deterministic-LP (DLP) bid-price baseline.

The classical comparator the methods paper was missing: every
``RESOLVE_EVERY_HOURS`` the policy solves a deterministic LP on
expected demand-to-go from the current fleet state, keeps the LP's
market--stage potentials, and between resolves accepts a load iff

    profit + w(dest, stage(t_done)) - w(origin, stage(now)) >= 0,

the textbook bid-price rule under re-solving. Expected demand and
rewards mirror the benchmark generator in expectation: arrival
intensity = expected_loads_per_hour x wave multiplier x FAF lane
share; expected price = rate midpoint x (0.9 + 0.1 scarcity) x wave
price multiplier (price noise has mean ~1); costs = distance x
cost-per-mile + fixed, minus a scenario-level mean extra cost
(deadhead + yard delays) estimated once from a calibration stream.

Duration conventions are consistent between the LP arcs and the
decision score, matching the transition semantics the dual policy
uses: LP arc durations are travel_hours (which already include base
service time) plus a scenario-level mean schedule overhead ---
waiting/deadhead, yard delay, and HOS rests beyond that base ---
estimated once from a fixed calibration stream via fresh-truck
plan_schedule; the decision score reads the destination potential at
the probe assignment's actual final_available_time.

The LP is a stage-aggregated fluid network (STAGE_HOURS-wide stages,
at most MAX_STAGES to the horizon): variables are lane dispatches
u[lane, stage] and idle masses z[market, stage]; balance equalities
carry idle mass and completed dispatches forward; dispatches are
capped by idle mass and expected demand; dispatches completing past
the horizon earn the destination's terminal value (the paper's
in-transit terminal convention). Solved with a dense float simplex
(Bland's rule, standard library only); potentials are the balance
rows' duals.

This is a baseline, deliberately simple: no per-decision re-solve, no
integer rounding, stage granularity coarse enough that a re-solve
costs tens of milliseconds at benchmark scale (amortized into the
mean per-decision latency the experiment runner reports).
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402

STAGE_HOURS = 12.0
MAX_STAGES = 6
# Re-solve cadence, overridable for the interval-sensitivity study
# (the paper reports 12 h alongside 6 h and 3 h).
RESOLVE_EVERY_HOURS = float(os.environ.get("FREIGHTBID_DLP_RESOLVE_HOURS", "12.0"))
EPS = 1e-9


def stage_count(duration: float) -> int:
    """Number of stages a dispatch occupies: exact ceiling on the
    float duration (integer-division tricks mis-bin fractional
    durations, e.g. 24.49 h is three 12-h stages, not two)."""
    return max(1, math.ceil(duration / STAGE_HOURS - EPS))


def float_simplex_max(
    c: list[float],
    a: list[list[float]],
    b: list[float],
    senses: list[str],
) -> tuple[float, list[float]]:
    """Two-phase dense simplex for max c'x s.t. a_i x (<=|=) b_i, x >= 0.

    Bland's rule throughout (anti-cycling). Returns (value, duals):
    duals[i] is row i's dual at optimality, read from the objective row
    on the row's slack column (<= rows) or artificial column (= rows).
    """
    m, n = len(a), len(c)
    # Normalize to b >= 0 (flip equality rows; <= rows with b < 0 get
    # flipped to >= and receive a surplus + artificial).
    a = [row[:] for row in a]
    b = b[:]
    senses = senses[:]
    flipped = [False] * m
    for i in range(m):
        if b[i] < 0:
            a[i] = [-v for v in a[i]]
            b[i] = -b[i]
            flipped[i] = True
            senses[i] = {"<=": ">=", ">=": "<=", "=": "="}[senses[i]]

    # Column layout: x (n) | slack/surplus per row | artificials.
    slack_col: dict[int, int] = {}
    art_col: dict[int, int] = {}
    col = n
    for i in range(m):
        if senses[i] in ("<=", ">="):
            slack_col[i] = col
            col += 1
    for i in range(m):
        if senses[i] in ("=", ">="):
            art_col[i] = col
            col += 1
    total = col

    tab = []
    basis = []
    for i in range(m):
        row = a[i] + [0.0] * (total - n) + [b[i]]
        if i in slack_col:
            row[slack_col[i]] = 1.0 if senses[i] == "<=" else -1.0
        if i in art_col:
            row[art_col[i]] = 1.0
            basis.append(art_col[i])
        else:
            basis.append(slack_col[i])
        tab.append(row)

    def pivot(leave: int, enter: int) -> None:
        piv = tab[leave][enter]
        tab[leave] = [v / piv for v in tab[leave]]
        for i in range(len(tab)):
            if i != leave and tab[i][enter] != 0.0:
                f = tab[i][enter]
                tab[i] = [vi - f * vl for vi, vl in zip(tab[i], tab[leave])]
        basis[leave] = enter

    def run(obj_row: list[float], banned: set[int]) -> None:
        tab.append(obj_row)
        while True:
            enter = next(
                (
                    j
                    for j in range(total)
                    if j not in banned and tab[m][j] < -EPS
                ),
                None,
            )
            if enter is None:
                break
            leave, best = None, None
            for i in range(m):
                if tab[i][enter] > EPS:
                    ratio = tab[i][total] / tab[i][enter]
                    if (
                        best is None
                        or ratio < best - EPS
                        or (abs(ratio - best) <= EPS and basis[i] < basis[leave])
                    ):
                        best, leave = ratio, i
            if leave is None:
                raise ValueError("unbounded DLP (should not happen)")
            pivot(leave, enter)

    # Phase 1: minimize artificial sum (maximize its negation).
    if art_col:
        obj = [0.0] * total + [0.0]
        for i in art_col:
            obj = [o - v for o, v in zip(obj, tab[i])]
        for j in art_col.values():
            obj[j] = 0.0
        run(obj, banned=set())
        if tab[m][total] < -1e-6:
            raise ValueError("infeasible DLP (should not happen)")
        tab.pop()

    # Phase 2: original objective, artificials banned from re-entering.
    obj = [-cj for cj in c] + [0.0] * (total - n) + [0.0]
    for i in range(m):
        if basis[i] < n and abs(obj[basis[i]]) > 0.0:
            f = obj[basis[i]]
            obj = [o - f * v for o, v in zip(obj, tab[i])]
    run(obj, banned=set(art_col.values()))

    duals = [0.0] * m
    for i in range(m):
        col_i = art_col.get(i, slack_col.get(i))
        y = tab[m][col_i]
        if i in slack_col and senses[i] == ">=":
            y = -y
        duals[i] = -y if flipped[i] else y
    return tab[m][total], duals


def lane_aggregates(lanes: list[dict[str, str]]) -> list[dict[str, object]]:
    total_tons = sum(max(base.as_float(l["faf_tons_2024"]), 1e-6) for l in lanes)
    out = []
    for lane in lanes:
        distance = base.lane_distance_miles(lane)
        out.append(
            {
                "origin": str(lane["origin_state"]),
                "dest": str(lane["destination_state"]),
                "share": max(base.as_float(lane["faf_tons_2024"]), 1e-6) / total_tons,
                "exp_price_base": base.as_float(lane["rate_midpoint"])
                * (0.9 + 0.1 * base.as_float(lane["scarcity_multiplier"])),
                "distance": distance,
                "travel_hours": distance / base.TRUCK_SPEED_MPH + base.SERVICE_HOURS,
                "lane_row": lane,
            }
        )
    return out


_MEAN_EXTRA_COST: dict[str, float] = {}
_MEAN_SCHEDULE_OVERHEAD: dict[str, float] = {}


def _calibrate(scenario: base.Scenario, lanes: list[dict[str, str]]) -> None:
    """Estimate scenario-level calibration constants once, from a
    fixed calibration stream (seed 20260506, outside the evaluation
    seeds): the mean extra cost (deadhead + yard delay) and the mean
    schedule overhead (fresh-truck plan_schedule completion minus
    nominal travel_hours: waiting, yard delay, and HOS rests beyond
    the base service time already in travel_hours)."""
    if scenario.name in _MEAN_EXTRA_COST:
        return
    import run_surrogate_cascade as sc

    loads = sc.generate_loads_with_seed(lanes, scenario, 20260506)
    extras: list[float] = []
    overheads: list[float] = []
    for load in loads[:400]:
        extras.append(feas.realized_profit(load)[1])
        hour = float(load["hour"])
        schedule = feas.plan_schedule(
            feas.TruckState("probe", str(load["origin_state"]), hour),
            load,
            hour,
        )
        if schedule.feasible:
            overheads.append(
                schedule.final_available_time
                - hour
                - float(load["travel_hours"])
            )
    _MEAN_EXTRA_COST[scenario.name] = (
        sum(extras) / len(extras) if extras else 0.0
    )
    _MEAN_SCHEDULE_OVERHEAD[scenario.name] = (
        sum(overheads) / len(overheads) if overheads else 0.0
    )


def mean_extra_cost(scenario: base.Scenario, lanes: list[dict[str, str]]) -> float:
    _calibrate(scenario, lanes)
    return _MEAN_EXTRA_COST[scenario.name]


def mean_schedule_overhead(
    scenario: base.Scenario, lanes: list[dict[str, str]]
) -> float:
    _calibrate(scenario, lanes)
    return _MEAN_SCHEDULE_OVERHEAD[scenario.name]


def solve_potentials(
    scenario: base.Scenario,
    lanes: list[dict[str, str]],
    fleet: dict[str, list[object]],
    now: float,
    state_values: dict[str, float],
) -> tuple[float, dict[tuple[str, int], float]]:
    """Solve the stage DLP from the current fleet state; return
    (lp_value, potentials): w[(market, stage)] with stages past the LP
    horizon falling back to omega * V(market) at lookup time. The LP
    value is exposed for the network-flow invariant tests (terminal
    conservation, post-horizon capacity)."""
    horizon = float(scenario.horizon_hours)
    n_stages = min(MAX_STAGES, stage_count(horizon - now))
    omega = base.terminal_value_weight(scenario)
    aggs = lane_aggregates(lanes)
    extra = mean_extra_cost(scenario, lanes)
    overhead = mean_schedule_overhead(scenario, lanes)
    markets = sorted(
        {a["origin"] for a in aggs} | {a["dest"] for a in aggs} | set(fleet)
    )

    idle: dict[str, float] = {m: 0.0 for m in markets}
    pipe: dict[tuple[str, int], float] = {}
    for market, trucks in fleet.items():
        for raw in trucks:
            avail = raw.available_time if hasattr(raw, "available_time") else float(raw)
            if avail <= now:
                idle[market] = idle.get(market, 0.0) + 1.0
            else:
                s = int((avail - now) // STAGE_HOURS)
                if s >= n_stages or avail >= horizon:
                    # Available after the horizon: terminal value is a
                    # decision-independent constant and the truck adds
                    # no usable capacity, so it stays out of the LP.
                    continue
                pipe[(market, s)] = pipe.get((market, s), 0.0) + 1.0

    # Expected demand and reward per (lane, stage).
    demand: dict[tuple[int, int], float] = {}
    reward: dict[tuple[int, int], float] = {}
    for s in range(n_stages):
        h0 = now + s * STAGE_HOURS
        hours = [h0 + k for k in range(int(STAGE_HOURS)) if h0 + k < horizon]
        if not hours:
            continue
        per_hour = sum(base.expected_loads_per_hour(scenario, h) for h in hours) / len(hours)
        for li, agg in enumerate(aggs):
            mult = sum(
                base.lane_demand_wave_multiplier(scenario, agg["lane_row"], h)
                for h in hours
            ) / len(hours)
            price_mult = sum(
                base.demand_wave_price_multiplier(scenario, agg["lane_row"], h)
                for h in hours
            ) / len(hours)
            n_exp = per_hour * len(hours) * agg["share"] * mult
            if n_exp < 1e-6:
                continue
            price = agg["exp_price_base"] * price_mult
            cost = (
                agg["distance"] * scenario.base_cost_per_mile
                + scenario.fixed_load_cost
            )
            r = price - cost - extra
            duration = agg["travel_hours"] + overhead
            d_stages = stage_count(duration)
            if s + d_stages >= n_stages:
                # Completes past the LP horizon: earn the destination
                # terminal in the reward. A final-stage dispatch is
                # never subtracted from the terminal-valued idle stock
                # z[m, S] (there is no later balance row), so its
                # origin terminal must be netted out here or the truck
                # earns terminal value twice.
                r += omega * state_values.get(agg["dest"], 0.0)
                if s == n_stages - 1:
                    r -= omega * state_values.get(agg["origin"], 0.0)
            demand[(li, s)] = n_exp
            reward[(li, s)] = r

    # Column layout: u columns then z columns.
    u_cols = sorted(demand)
    z_cols = [(m, s) for s in range(n_stages) for m in markets]
    u_index = {k: i for i, k in enumerate(u_cols)}
    z_index = {k: len(u_cols) + i for i, k in enumerate(z_cols)}
    n_vars = len(u_cols) + len(z_cols)
    c = [0.0] * n_vars
    for k, i in u_index.items():
        c[i] = reward[k]
    for m in markets:
        c[z_index[(m, n_stages - 1)]] += omega * state_values.get(m, 0.0)

    rows: list[list[float]] = []
    rhs: list[float] = []
    senses: list[str] = []
    balance_row_of: dict[tuple[str, int], int] = {}

    def add_balance(m: str, s: int, coeffs: dict[int, float], b_val: float) -> None:
        row_pos = [0.0] * n_vars
        for i, v in coeffs.items():
            row_pos[i] = v
        balance_row_of[(m, s)] = len(rows)
        rows.append(row_pos)
        rhs.append(b_val)
        senses.append("=")

    for s in range(n_stages):
        for m in markets:
            coeffs: dict[int, float] = {z_index[(m, s)]: 1.0}
            b_val = idle.get(m, 0.0) + pipe.get((m, s), 0.0) if s == 0 else pipe.get((m, s), 0.0)
            if s > 0:
                coeffs[z_index[(m, s - 1)]] = coeffs.get(z_index[(m, s - 1)], 0.0) - 1.0
                for (li, ss), i in u_index.items():
                    if ss == s - 1 and aggs[li]["origin"] == m:
                        coeffs[i] = coeffs.get(i, 0.0) + 1.0
                for (li, ss), i in u_index.items():
                    d_stages = stage_count(
                        aggs[li]["travel_hours"]
                        + mean_schedule_overhead(scenario, lanes)
                    )
                    if aggs[li]["dest"] == m and ss + d_stages == s:
                        coeffs[i] = coeffs.get(i, 0.0) - 1.0
            add_balance(m, s, coeffs, b_val)

    for s in range(n_stages):
        for m in markets:
            row = [0.0] * n_vars
            any_u = False
            for (li, ss), i in u_index.items():
                if ss == s and aggs[li]["origin"] == m:
                    row[i] = 1.0
                    any_u = True
            if not any_u:
                continue
            row[z_index[(m, s)]] = -1.0
            rows.append(row)
            rhs.append(0.0)
            senses.append("<=")

    for k, i in u_index.items():
        row = [0.0] * n_vars
        row[i] = 1.0
        rows.append(row)
        rhs.append(demand[k])
        senses.append("<=")

    value, duals = float_simplex_max(c, rows, rhs, senses)
    return value, {key: duals[r_i] for key, r_i in balance_row_of.items()}


_RESOLVE_STATE: dict[tuple[str, int], tuple[float, dict[tuple[str, int], float]]] = {}


def dlp_score(
    scenario: base.Scenario,
    lanes: list[dict[str, str]],
    fleet: dict[str, list[object]],
    load: dict[str, object],
    profit: float,
    state_values: dict[str, float],
    done: float | None = None,
) -> float:
    """Bid-price score for one decision under the re-solving DLP.
    `done` is the probe assignment's actual completion time; the
    nominal travel-hours fallback exists only for callers without a
    schedule."""
    now = float(load["hour"])
    key = (scenario.name, id(fleet))
    cached = _RESOLVE_STATE.get(key)
    if cached is None or now - cached[0] >= RESOLVE_EVERY_HOURS:
        _, w = solve_potentials(scenario, lanes, fleet, now, state_values)
        _RESOLVE_STATE[key] = (now, w)
    else:
        w = cached[1]
    resolve_time = _RESOLVE_STATE[key][0]
    omega = base.terminal_value_weight(scenario)

    def potential(market: str, hour: float) -> float:
        s = int(max(0.0, hour - resolve_time) // STAGE_HOURS)
        if (market, s) in w:
            return w[(market, s)]
        return omega * state_values.get(market, 0.0)

    if done is None:
        done = now + float(load["travel_hours"])
    return (
        profit
        + potential(str(load["destination_state"]), done)
        - potential(str(load["origin_state"]), now)
    )
