#!/usr/bin/env python3
"""Lagrangian-per-truck information-relaxation upper bound for FreightBidBench v0.3.

This implements the Theorem 1 construction described in
``papers/freightbidbench_v03_path_b_workplan.md`` Section 4. The joint MDP's
assignment constraint (at most one truck per tendered load) is relaxed by
introducing non-negative dual prices lambda_t per load. The resulting
Lagrangian decomposes across trucks: each truck independently solves a
sub-MDP whose only coupling to other trucks is through the dual penalty
paid on each accept. The Lagrangian dual is

    L(lambda) = sum_t lambda_t + sum_k V_k_lambda(u_0_k),

where V_k_lambda is the per-truck sub-MDP optimal value. Weak duality gives
V_star <= min_lambda L(lambda).

Under common random numbers the per-truck sub-MDP is a deterministic
sequential decision problem with continuous-state (location, available_time,
HOS drive used, HOS duty used). We solve it exactly via forward enumeration
with dominance pruning. Transitions reuse ``freight_feasibility.apply_accept``
on a single-truck fleet so the bound's per-load profit accounting matches
the closed-loop simulator bit-for-bit.

The script is intentionally dependency-free.
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import math
import multiprocessing
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import freight_feasibility as feas  # noqa: E402
import run_closed_loop_baselines as base  # noqa: E402
import run_surrogate_cascade as sc  # noqa: E402


DEFAULT_CONFIG_PATH = ROOT / "configs" / "freightbidbench_v03_scenarios.json"
DEFAULT_OUTPUT_DIR = ROOT / "benchmark_runs" / "lagrangian_bound_smoke"
DEFAULT_SCENARIO = "tight"


# -----------------------------------------------------------------------------
# Per-truck sub-MDP solver
# -----------------------------------------------------------------------------


@dataclass
class TruckDPState:
    """A reachable per-truck state during the forward DP."""

    location: str
    available_time: float
    drive_used: float
    duty_used: float
    value: float
    accepted_load_ids: tuple[int, ...] = field(default_factory=tuple)


# Bucket granularities chosen to preserve upper-bound validity:
# rounding down on each dimension is "favorable" to the truck (more time,
# more HOS budget), so per-truck values can only increase, keeping the
# overall Lagrangian bound a valid upper bound on V*.
TIME_BUCKET_HOURS = 0.25  # 15-minute buckets
DRIVE_BUCKET_HOURS = 1.0
DUTY_BUCKET_HOURS = 1.0


def bucket_key_and_snapped(
    state: TruckDPState,
) -> tuple[tuple[int, int, int], TruckDPState]:
    """Return the bucket key for ``state`` and a clock-snapped copy.

    Snapping rounds each clock dimension down to its bucket's lower edge,
    which is the most permissive point in the bucket: more time available,
    less HOS used. This preserves the upper-bound validity of the
    Lagrangian relaxation, since a per-truck DP solved from the snapped
    state is at least as expressive as from the original.
    """
    t_idx = int(state.available_time / TIME_BUCKET_HOURS)
    d_idx = int(state.drive_used / DRIVE_BUCKET_HOURS)
    du_idx = int(state.duty_used / DUTY_BUCKET_HOURS)
    snapped = TruckDPState(
        location=state.location,
        available_time=t_idx * TIME_BUCKET_HOURS,
        drive_used=d_idx * DRIVE_BUCKET_HOURS,
        duty_used=du_idx * DUTY_BUCKET_HOURS,
        value=state.value,
        accepted_load_ids=state.accepted_load_ids,
    )
    return (t_idx, d_idx, du_idx), snapped


def merge_bucket(
    bucket: dict[tuple[int, int, int], TruckDPState],
    candidate: TruckDPState,
) -> None:
    """Merge a candidate state into a per-location bucket dict.

    The dict is keyed by (time, drive, duty) bucket indices (location is
    implicit). The candidate is first snapped to its bucket's
    favorable-corner clocks. Within a bucket key, the highest-value state
    is kept (since all states in the bucket share identical snapped
    clocks). Across bucket keys, Pareto pruning is applied: drop the
    candidate if any existing state has bucket indices all weakly smaller
    (more favorable) and at least as much value; remove existing entries
    the candidate Pareto-dominates.
    """
    cand_key, snapped = bucket_key_and_snapped(candidate)
    existing = bucket.get(cand_key)
    if existing is not None:
        if snapped.value > existing.value:
            bucket[cand_key] = snapped
        return
    # Cross-bucket Pareto pruning on bucket indices (favorable = smaller).
    dominated_keys: list[tuple[int, int, int]] = []
    for key, state in bucket.items():
        if (
            key[0] <= cand_key[0]
            and key[1] <= cand_key[1]
            and key[2] <= cand_key[2]
            and state.value >= snapped.value
        ):
            return  # Dominated by an existing snapped state; drop candidate.
        if (
            cand_key[0] <= key[0]
            and cand_key[1] <= key[1]
            and cand_key[2] <= key[2]
            and snapped.value >= state.value
        ):
            dominated_keys.append(key)
    for key in dominated_keys:
        del bucket[key]
    bucket[cand_key] = snapped


def transition_under_accept(
    state: TruckDPState,
    load: dict[str, object],
    truck_id: str,
) -> tuple[bool, float, TruckDPState]:
    """Attempt to accept ``load`` from per-truck state ``state``.

    Returns ``(accepted, realized_profit, new_state)``. If infeasible,
    ``accepted=False`` and ``new_state`` equals ``state`` with value
    unchanged. Implementation is inlined from ``feas.apply_accept`` for
    the single-truck case to avoid fleet-dict allocation overhead inside
    the per-truck DP hot loop.
    """
    config = feas.ACTIVE_CONFIG
    decision_hour = float(load["hour"])
    pickup_latest = float(load.get("pickup_latest", decision_hour + 4.0))
    if config.enable_time_windows and state.available_time > pickup_latest:
        return False, 0.0, state
    truck = feas.TruckState(
        truck_id,
        state.location,
        state.available_time,
        state.drive_used,
        state.duty_used,
    )
    schedule = feas.plan_schedule(truck, load, decision_hour)
    if not schedule.feasible:
        return False, 0.0, state
    profit, _extra_cost = feas.realized_profit(load)
    destination = str(load["destination_state"])
    new_state = TruckDPState(
        location=destination,
        available_time=schedule.final_available_time,
        drive_used=schedule.drive_used_hours,
        duty_used=schedule.duty_used_hours,
        value=state.value + profit,
        accepted_load_ids=state.accepted_load_ids + (int(load["load_id"]),),
    )
    return True, profit, new_state


FrontierBucket = dict[tuple[int, int, int], TruckDPState]


def solve_truck_sub_mdp(
    initial_state: TruckDPState,
    relevant_loads: list[dict[str, object]],
    duals: dict[int, float],
    terminal_value_weight: float,
    state_values: dict[str, float],
    truck_id: str,
) -> TruckDPState:
    """Solve the per-truck Lagrangian sub-MDP with bucketed state space.

    The frontier is a nested dict: location -> bucket key -> state. Bucket
    granularities (TIME_BUCKET_HOURS, DRIVE_BUCKET_HOURS, DUTY_BUCKET_HOURS)
    are chosen to preserve upper-bound validity: rounding clocks down is
    favorable to the truck, so per-truck values can only increase relative
    to the exact DP, keeping the Lagrangian bound a valid upper bound on
    V*. The bucketing collapses near-duplicate states, controlling the
    frontier size and the cost of dominance comparisons.
    """
    frontier: dict[str, FrontierBucket] = {}
    init_bucket: FrontierBucket = {}
    merge_bucket(init_bucket, initial_state)
    frontier[initial_state.location] = init_bucket
    for load in relevant_loads:
        load_origin = str(load["origin_state"])
        matching = frontier.get(load_origin)
        if not matching:
            continue
        load_id = int(load["load_id"])
        lam = duals.get(load_id, 0.0)
        # Compute accept-branch candidates from each state currently at
        # load_origin. Reject branch leaves states in place, so we only
        # need to relocate the successful accepts.
        accept_branches: list[TruckDPState] = []
        for state in list(matching.values()):
            accepted, profit, new_state = transition_under_accept(
                state, load, truck_id
            )
            if not accepted:
                continue
            adjusted = TruckDPState(
                location=new_state.location,
                available_time=new_state.available_time,
                drive_used=new_state.drive_used,
                duty_used=new_state.duty_used,
                value=state.value + profit - lam,
                accepted_load_ids=new_state.accepted_load_ids,
            )
            accept_branches.append(adjusted)
        # Merge accept-branch states into their destination buckets.
        for state in accept_branches:
            dest_bucket = frontier.setdefault(state.location, {})
            merge_bucket(dest_bucket, state)
    # Sweep over all surviving states, add terminal fleet value, pick best.
    best: TruckDPState | None = None
    for location, bucket in frontier.items():
        terminal = terminal_value_weight * state_values.get(location, 0.0)
        for state in bucket.values():
            final_value = state.value + terminal
            if best is None or final_value > best.value:
                best = TruckDPState(
                    location=state.location,
                    available_time=state.available_time,
                    drive_used=state.drive_used,
                    duty_used=state.duty_used,
                    value=final_value,
                    accepted_load_ids=state.accepted_load_ids,
                )
    assert best is not None
    return best


def filter_loads_for_truck(
    loads: list[dict[str, object]],
    truck_starting_state: str,
) -> list[dict[str, object]]:
    """Loose pre-filter: keep loads whose origin is reachable from the truck.

    The truck can in principle reach any market over the horizon, so we keep
    all loads. We still order by hour so the DP processes chronologically.
    """
    # Defensive copy + chronological sort.
    return sorted(loads, key=lambda load: float(load["hour"]))


# -----------------------------------------------------------------------------
# Joint Lagrangian bound evaluation
# -----------------------------------------------------------------------------


@dataclass
class LagrangianEvaluation:
    bound: float
    per_truck_values: list[float]
    accept_counts: dict[int, int]  # load_id -> sum_k a^(k)_t under the solver
    accepted_load_ids_per_truck: list[tuple[int, ...]]


# Per-worker context for multiprocessing: the loads, terminal weight, and
# state values are identical across trucks and iterations, so they are
# shipped to each worker once via the Pool initializer instead of being
# pickled per task.
_POOL_CTX: dict[str, object] = {}


def _pool_init(
    sorted_loads: list[dict[str, object]],
    terminal_value_weight: float,
    state_values: dict[str, float],
) -> None:
    _POOL_CTX["sorted_loads"] = sorted_loads
    _POOL_CTX["terminal_value_weight"] = terminal_value_weight
    _POOL_CTX["state_values"] = state_values


def _solve_truck_task(
    task: tuple[TruckDPState, str], duals: dict[int, float]
) -> TruckDPState:
    initial, truck_id = task
    return solve_truck_sub_mdp(
        initial,
        _POOL_CTX["sorted_loads"],  # type: ignore[arg-type]
        duals,
        _POOL_CTX["terminal_value_weight"],  # type: ignore[arg-type]
        _POOL_CTX["state_values"],  # type: ignore[arg-type]
        truck_id,
    )


def _truck_tasks(
    initial_fleet: dict[str, list[object]]
) -> list[tuple[TruckDPState, str]]:
    tasks: list[tuple[TruckDPState, str]] = []
    for state, trucks in initial_fleet.items():
        for truck in trucks:
            if isinstance(truck, feas.TruckState):
                truck_id = truck.truck_id
                avail_time = truck.available_time
                drive_used = truck.drive_used_hours
                duty_used = truck.duty_used_hours
                truck_state = truck.state
            else:
                # Bare float; pre-v0.2 compatibility.
                truck_id = f"{state}-anon"
                avail_time = float(truck)
                drive_used = 0.0
                duty_used = 0.0
                truck_state = state
            tasks.append(
                (
                    TruckDPState(
                        location=truck_state,
                        available_time=avail_time,
                        drive_used=drive_used,
                        duty_used=duty_used,
                        value=0.0,
                    ),
                    truck_id,
                )
            )
    return tasks


def evaluate_lagrangian(
    initial_fleet: dict[str, list[object]],
    loads: list[dict[str, object]],
    duals: dict[int, float],
    terminal_value_weight: float,
    state_values: dict[str, float],
    pool: object | None = None,
) -> LagrangianEvaluation:
    """Evaluate L(lambda) on a single realized scenario.

    Solves each truck's sub-MDP independently under the dual penalties,
    sums the per-truck values plus sum_t lambda_t (the constant term from
    the Lagrangian). The per-truck solves are independent; when ``pool``
    (a multiprocessing.Pool primed with ``_pool_init``) is supplied they
    run in parallel. ``Pool.map`` preserves task order, so the float
    reduction order matches the serial path and results are bit-identical.
    """
    sorted_loads = sorted(loads, key=lambda load: float(load["hour"]))
    tasks = _truck_tasks(initial_fleet)
    if pool is not None:
        results = pool.map(  # type: ignore[attr-defined]
            functools.partial(_solve_truck_task, duals=duals), tasks
        )
    else:
        results = [
            solve_truck_sub_mdp(
                initial,
                sorted_loads,
                duals,
                terminal_value_weight,
                state_values,
                truck_id,
            )
            for initial, truck_id in tasks
        ]
    per_truck_values: list[float] = []
    accept_counts: dict[int, int] = {int(load["load_id"]): 0 for load in sorted_loads}
    accepted_per_truck: list[tuple[int, ...]] = []
    for best in results:
        per_truck_values.append(best.value)
        accepted_per_truck.append(best.accepted_load_ids)
        for load_id in best.accepted_load_ids:
            accept_counts[load_id] = accept_counts.get(load_id, 0) + 1
    dual_constant = sum(duals.values())
    bound = dual_constant + sum(per_truck_values)
    return LagrangianEvaluation(
        bound=bound,
        per_truck_values=per_truck_values,
        accept_counts=accept_counts,
        accepted_load_ids_per_truck=accepted_per_truck,
    )


# -----------------------------------------------------------------------------
# Subgradient dual loop
# -----------------------------------------------------------------------------


@dataclass
class DualTrajectoryRecord:
    iteration: int
    bound: float
    overuse_count: int
    average_dual: float
    elapsed_seconds: float


def write_duals_checkpoint(path: Path, duals: dict[int, float]) -> None:
    """Atomically write duals in the lagrangian_dual_prices.csv format."""
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["load_id", "lambda"])
        for load_id in sorted(duals):
            writer.writerow([load_id, f"{duals[load_id]:.4f}"])
    tmp.replace(path)


def load_initial_duals_from_csv(
    path: Path, loads: list[dict[str, object]]
) -> dict[int, float]:
    """Read warm-start dual prices from a CSV with columns 'load_id, lambda'.

    Loads not present in the file default to 0.0. Loads present but not in the
    current load stream are ignored.
    """
    load_ids = {int(load["load_id"]) for load in loads}
    duals: dict[int, float] = {load_id: 0.0 for load_id in load_ids}
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            load_id = int(row["load_id"])
            if load_id in duals:
                duals[load_id] = float(row["lambda"])
    return duals


def subgradient_dual_loop(
    initial_fleet: dict[str, list[object]],
    loads: list[dict[str, object]],
    terminal_value_weight: float,
    state_values: dict[str, float],
    *,
    iterations: int,
    step_scale: float,
    initial_duals: dict[int, float] | None = None,
    iter_offset: int = 0,
    verbose: bool = False,
    workers: int = 1,
    checkpoint_dir: Path | None = None,
) -> tuple[dict[int, float], LagrangianEvaluation, list[DualTrajectoryRecord]]:
    """Subgradient ascent on the dual L(lambda).

    Note: L(lambda) is convex in lambda (pointwise sup of affine
    functions). Minimizing L corresponds to descent. The "subgradient" of L
    with respect to lambda_t at the current solution is
        partial L / partial lambda_t = 1 - sum_k a^(k)_t.
    If the relaxed solver over-uses load t (sum_k a^(k)_t > 1), the gradient
    is negative; to decrease L we increase lambda_t. The update is
        lambda_t <- max(0, lambda_t + step * (sum_k a^(k)_t - 1)).

    Pass ``initial_duals`` (a dict from load_id to lambda value) to warm-start
    from a previous run. ``iter_offset`` shifts the step-size schedule so the
    diminishing step matches the resumed iteration count.
    """
    if initial_duals is not None:
        duals = {int(load["load_id"]): 0.0 for load in loads}
        for load_id, lam in initial_duals.items():
            if load_id in duals:
                duals[load_id] = float(lam)
    else:
        duals = {int(load["load_id"]): 0.0 for load in loads}
    trajectory: list[DualTrajectoryRecord] = []
    best_bound: float = float("inf")
    best_duals: dict[int, float] = dict(duals)
    best_eval: LagrangianEvaluation | None = None
    start = time.perf_counter()
    pool = None
    if workers > 1:
        sorted_loads = sorted(loads, key=lambda load: float(load["hour"]))
        pool = multiprocessing.Pool(
            workers,
            initializer=_pool_init,
            initargs=(sorted_loads, terminal_value_weight, state_values),
        )
    try:
        for n in range(1, iterations + 1):
            evaluation = evaluate_lagrangian(
                initial_fleet,
                loads,
                duals,
                terminal_value_weight,
                state_values,
                pool=pool,
            )
            overuse_count = sum(1 for v in evaluation.accept_counts.values() if v > 1)
            avg_dual = sum(duals.values()) / max(1, len(duals))
            record = DualTrajectoryRecord(
                iteration=n,
                bound=evaluation.bound,
                overuse_count=overuse_count,
                average_dual=avg_dual,
                elapsed_seconds=time.perf_counter() - start,
            )
            trajectory.append(record)
            if verbose:
                print(
                    f"iter {n:3d} | bound = {evaluation.bound:>14,.2f} | "
                    f"overuse_count = {overuse_count:4d} | "
                    f"avg_lambda = {avg_dual:>8,.2f} | "
                    f"elapsed = {record.elapsed_seconds:.1f}s"
                )
            if evaluation.bound < best_bound:
                best_bound = evaluation.bound
                best_duals = dict(duals)
                best_eval = evaluation
            # Subgradient step.
            step = step_scale / math.sqrt(n + iter_offset)
            for load_id, count in evaluation.accept_counts.items():
                slack = count - 1
                duals[load_id] = max(0.0, duals[load_id] + step * slack)
            # Checkpoint after every iteration so an interrupted run can be
            # resumed with --initial-duals-csv/--iter-offset instead of
            # losing all progress (post-step duals; best-so-far separately).
            if checkpoint_dir is not None:
                write_duals_checkpoint(
                    checkpoint_dir / "lagrangian_duals_checkpoint.csv", duals
                )
                write_duals_checkpoint(
                    checkpoint_dir / "lagrangian_best_duals_checkpoint.csv",
                    best_duals,
                )
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    assert best_eval is not None
    return best_duals, best_eval, trajectory


# -----------------------------------------------------------------------------
# Configuration and scenario loading (mirrors run_relaxed_hindsight_bound.py)
# -----------------------------------------------------------------------------


def scenario_from_config(config: dict[str, object]) -> base.Scenario:
    return base.Scenario(
        str(config["name"]),
        horizon_hours=int(config["horizon_hours"]),
        loads_per_hour=int(config["loads_per_hour"]),
        fleet_size=int(config["fleet_size"]),
        base_cost_per_mile=float(config["base_cost_per_mile"]),
        fixed_load_cost=float(config["fixed_load_cost"]),
        value_scale_dollars=float(config["value_scale_dollars"]),
        service_failure_penalty_dollars=config.get("service_failure_penalty_dollars"),
        terminal_value_weight=config.get("terminal_value_weight"),
        demand_wave_schedule=config.get("demand_wave_schedule"),
    )


def load_config(config_path: Path) -> tuple[Path, dict[str, object], dict[str, base.Scenario]]:
    path = config_path if config_path.is_absolute() else ROOT / config_path
    config = json.loads(path.read_text(encoding="utf-8"))
    scenarios = {
        name: scenario_from_config(scenario_config)
        for name, scenario_config in dict(config["scenarios"]).items()
    }
    return path, config, scenarios


# -----------------------------------------------------------------------------
# Output writers
# -----------------------------------------------------------------------------


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def money(value: float) -> str:
    return f"${value:,.0f}"


def write_report(
    path: Path,
    config_path: Path,
    scenario_key: str,
    scenario: base.Scenario,
    eval_seed: int,
    loads_seen: int,
    iterations: int,
    step_scale: float,
    initial_bound: float,
    final_bound: float,
    final_overuse: int,
    elapsed_seconds: float,
    lp_bound_reference: float | None = None,
    rollout_reference: float | None = None,
) -> None:
    lp_section = ""
    if lp_bound_reference is not None and lp_bound_reference > 0:
        tighter_pct = (lp_bound_reference - final_bound) / lp_bound_reference
        lp_section = (
            "\n## Comparison vs LP Relaxation\n\n"
            f"- LP relaxation upper bound (reference): {money(lp_bound_reference)}\n"
            f"- Lagrangian best bound: {money(final_bound)}\n"
            f"- Relative tightness: Lagrangian is {tighter_pct:.1%} tighter than LP.\n"
        )
    rollout_section = ""
    if rollout_reference is not None and rollout_reference > 0:
        valid = final_bound >= rollout_reference
        rollout_section = (
            "\n## Validity Check vs Rollout Teacher\n\n"
            f"- Rollout teacher realized profit (reference): "
            f"{money(rollout_reference)}\n"
            f"- Lagrangian best bound: {money(final_bound)}\n"
            f"- Validity (bound >= rollout): "
            f"{'PASS' if valid else 'FAIL (bound is invalid; debug)'}\n"
        )
    content = f"""# FreightBidBench v0.3 Lagrangian-per-truck Upper Bound

## Configuration

- Scenario: `{scenario_key}` (`{scenario.name}`)
- Scenario config: `{config_path.relative_to(ROOT)}`
- Eval seed: `{eval_seed}`
- Realized loads: `{loads_seen}`
- Fleet size: `{scenario.fleet_size}`
- Subgradient iterations: `{iterations}`
- Step scale: `{step_scale}`
- Runtime: `{elapsed_seconds:.2f}` seconds

## Bound Trajectory

| Quantity | Value |
| --- | ---: |
| Initial bound L(0) | {money(initial_bound)} |
| Final best bound min_n L(lambda_n) | {money(final_bound)} |
| Final iteration constraint over-use count | {final_overuse} |

The initial bound at lambda = 0 corresponds to the per-truck offline DP
without any inter-truck assignment penalty: each truck is allowed to
accept any feasible load independently, with potential duplication across
trucks. As lambda climbs through subgradient ascent, duplicate accepts
become costly to the per-truck sub-MDP solver and the bound tightens.
{lp_section}{rollout_section}
## Interpretation

This is an information-relaxation upper bound in the sense of Brown,
Smith, and Sun (2010): the relaxation provides perfect future
information to each truck independently while the assignment constraint
is dualized. The bound is valid by weak duality. Tightness depends on
how well the dualized assignment constraint approximates the joint
single-assignment integrality.

State-space bucketing favors the upper bound: clocks are rounded down
to the most-permissive corner of each bucket so the per-truck DP can
only over-estimate the per-truck Lagrangian sup, preserving the
joint upper-bound guarantee.
"""
    path.write_text(content, encoding="utf-8")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Lagrangian-per-truck upper bound for FreightBidBench v0.3."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--eval-seed", type=int)
    parser.add_argument("--eval-load-limit", type=int)
    parser.add_argument("--fleet-limit", type=int)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--step-scale", type=float, default=50.0)
    parser.add_argument(
        "--initial-duals-csv",
        type=Path,
        help="Warm-start from a previously written lagrangian_dual_prices.csv "
        "(load_id, lambda columns). Loads not in the file default to 0.",
    )
    parser.add_argument(
        "--iter-offset",
        type=int,
        default=0,
        help="Shift the diminishing-step schedule by this offset. Use when "
        "warm-starting after N prior iterations so step = step_scale / "
        "sqrt(n + offset).",
    )
    parser.add_argument(
        "--lp-bound-reference",
        type=float,
        help="LP relaxation bound from run_relaxed_hindsight_bound.py for the "
        "same scenario/seed; printed in the report for direct comparison.",
    )
    parser.add_argument(
        "--rollout-reference",
        type=float,
        help="Rollout teacher realized profit for the same scenario/seed; "
        "used to validate the upper-bound property (bound >= rollout).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallelize per-truck sub-MDP solves across this many "
        "processes (stdlib multiprocessing). Results are bit-identical "
        "to the serial path; default 1.",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.eval_load_limit is not None and args.eval_load_limit <= 0:
        raise SystemExit("--eval-load-limit must be positive")
    if args.iterations <= 0:
        raise SystemExit("--iterations must be positive")

    start = time.perf_counter()
    config_path, config, scenarios = load_config(args.config)
    if args.scenario not in scenarios:
        raise SystemExit(
            f"--scenario must be one of: {', '.join(sorted(scenarios))}"
        )
    eval_seed = (
        args.eval_seed
        if args.eval_seed is not None
        else int(config["default_first_seed"]) + 1
    )
    scenario = scenarios[args.scenario]
    lanes = base.load_csv(base.LANES)
    loads = sc.generate_loads_with_seed(lanes, scenario, eval_seed)
    if args.eval_load_limit is not None:
        loads = loads[: args.eval_load_limit]
    initial_fleet = sc.initial_fleet_with_seed(lanes, scenario, eval_seed)
    if args.fleet_limit is not None and args.fleet_limit > 0:
        # Truncate the fleet to a small subset for smoke testing.
        trimmed: dict[str, list[object]] = {}
        remaining = args.fleet_limit
        for state, trucks in initial_fleet.items():
            keep = trucks[:remaining]
            if keep:
                trimmed[state] = keep
            remaining -= len(keep)
            if remaining <= 0:
                break
        initial_fleet = trimmed
    state_values = base.build_state_values(lanes, scenario)
    terminal_weight = base.terminal_value_weight(scenario)

    initial_duals: dict[int, float] | None = None
    if args.initial_duals_csv is not None:
        initial_duals = load_initial_duals_from_csv(args.initial_duals_csv, loads)
    initial_eval = evaluate_lagrangian(
        initial_fleet,
        loads,
        initial_duals if initial_duals is not None else {},
        terminal_weight,
        state_values,
    )
    initial_bound = initial_eval.bound
    args.output_dir.mkdir(parents=True, exist_ok=True)
    best_duals, best_eval, trajectory = subgradient_dual_loop(
        initial_fleet,
        loads,
        terminal_weight,
        state_values,
        iterations=args.iterations,
        step_scale=args.step_scale,
        initial_duals=initial_duals,
        iter_offset=args.iter_offset,
        verbose=args.verbose,
        workers=args.workers,
        checkpoint_dir=args.output_dir,
    )
    summary_rows = [
        {
            "scenario": args.scenario,
            "scenario_name": scenario.name,
            "eval_seed": eval_seed,
            "loads_seen": len(loads),
            "fleet_size_evaluated": sum(len(v) for v in initial_fleet.values()),
            "iterations": args.iterations,
            "step_scale": args.step_scale,
            "initial_bound_L0": f"{initial_bound:.2f}",
            "best_bound": f"{best_eval.bound:.2f}",
            "best_iteration_overuse_count": sum(
                1 for c in best_eval.accept_counts.values() if c > 1
            ),
            "elapsed_seconds": f"{time.perf_counter() - start:.4f}",
        }
    ]
    write_csv(args.output_dir / "lagrangian_bound_summary.csv", summary_rows)
    write_csv(
        args.output_dir / "lagrangian_dual_trajectory.csv",
        [
            {
                "iteration": record.iteration,
                "bound": f"{record.bound:.2f}",
                "overuse_count": record.overuse_count,
                "average_dual": f"{record.average_dual:.4f}",
                "elapsed_seconds": f"{record.elapsed_seconds:.4f}",
            }
            for record in trajectory
        ],
    )
    write_csv(
        args.output_dir / "lagrangian_dual_prices.csv",
        [
            {"load_id": load_id, "lambda": f"{best_duals.get(load_id, 0.0):.4f}"}
            for load_id in sorted(best_duals)
        ],
    )
    final_overuse = sum(1 for c in best_eval.accept_counts.values() if c > 1)
    write_report(
        args.output_dir / "lagrangian_bound_report.md",
        config_path,
        args.scenario,
        scenario,
        eval_seed,
        len(loads),
        args.iterations,
        args.step_scale,
        initial_bound,
        best_eval.bound,
        final_overuse,
        time.perf_counter() - start,
        lp_bound_reference=args.lp_bound_reference,
        rollout_reference=args.rollout_reference,
    )
    print(
        f"Wrote {args.output_dir / 'lagrangian_bound_report.md'} "
        f"(L(0) = {money(initial_bound)}, best = {money(best_eval.bound)})"
    )


if __name__ == "__main__":
    main()
