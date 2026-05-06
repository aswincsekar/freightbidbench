#!/usr/bin/env python3
"""Run a first CPU rollout-teacher comparison.

The rollout teacher evaluates accept vs reject by simulating stochastic future
loads from the same public-calibrated environment. This is intentionally small:
it is a correctness and latency probe before building a faster vectorized or
cascaded version.
"""

from __future__ import annotations

import csv
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import run_closed_loop_baselines as base  # noqa: E402
import freight_feasibility as feas  # noqa: E402


SUMMARY_OUT = ROOT / "data" / "processed" / "rollout_teacher_summary.csv"
DECISIONS_OUT = ROOT / "data" / "processed" / "rollout_teacher_decisions.csv"
REPORT_OUT = ROOT / "reports" / "rollout_teacher_report.md"

SEED = 20260506
ROLLOUT_SCENARIO = base.Scenario(
    "rollout_probe_tight_capacity",
    horizon_hours=72,
    loads_per_hour=14,
    fleet_size=70,
    base_cost_per_mile=3.10,
    fixed_load_cost=250.0,
    value_scale_dollars=3000.0,
)
ROLLOUT_REPLICATIONS = 5
LOOKAHEAD_HOURS = 18
FUTURE_LOADS_PER_HOUR = 10
ROLLOUT_BASE_POLICY = base.Policy("rollout_base_bid_price", 1.0, 0.0)
DECISION_SAMPLE_LIMIT = 600


def copy_fleet(fleet: dict[str, list[object]]) -> dict[str, list[object]]:
    return feas.copy_fleet(fleet)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[idx]


def generate_future_loads(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    start_hour: float,
    rng: random.Random,
) -> list[dict[str, object]]:
    weights = [max(base.as_float(lane["faf_tons_2024"]), 1e-6) for lane in lanes]
    loads: list[dict[str, object]] = []
    load_id = 0
    for offset in range(1, LOOKAHEAD_HOURS + 1):
        hour = start_hour + offset
        count = max(0, int(round(rng.gauss(FUTURE_LOADS_PER_HOUR, 2.0))))
        for _ in range(count):
            lane = base.weighted_choice(rng, lanes, weights)
            distance = base.lane_distance_miles(lane)
            scarcity = base.as_float(lane["scarcity_multiplier"])
            price_noise = min(1.35, max(0.65, rng.gauss(1.0, 0.09)))
            price = base.as_float(lane["rate_midpoint"]) * price_noise * (0.9 + 0.1 * scarcity)
            direct_cost = distance * scenario.base_cost_per_mile + scenario.fixed_load_cost
            travel_hours = distance / base.TRUCK_SPEED_MPH + base.SERVICE_HOURS
            loads.append(
                feas.decorate_load(
                    {
                        "load_id": load_id,
                        "hour": hour,
                        "origin_state": lane["origin_state"],
                        "origin_name": lane["origin_name"],
                        "destination_state": lane["destination_state"],
                        "destination_name": lane["destination_name"],
                        "destination_city": lane["destination_city"],
                        "availability": lane["availability"],
                        "distance_miles": distance,
                        "price": price,
                        "direct_cost": direct_cost,
                        "base_cost_per_mile": scenario.base_cost_per_mile,
                        "travel_hours": travel_hours,
                        "faf_tons_2024": base.as_float(lane["faf_tons_2024"]),
                    },
                    rng,
                    base.TRUCK_SPEED_MPH,
                )
            )
            load_id += 1
    return loads


def apply_accept(
    fleet: dict[str, list[object]],
    load: dict[str, object],
    hour: float,
) -> float | None:
    result = feas.apply_accept(fleet, load, hour)
    if not result.accepted:
        return None
    return result.profit


def simulate_future_profit(
    fleet: dict[str, list[object]],
    future_loads: list[dict[str, object]],
    state_values: dict[str, float],
) -> float:
    profit = 0.0
    for load in future_loads:
        accept, _, _ = base.policy_accepts(ROLLOUT_BASE_POLICY, load, state_values)
        if not accept:
            continue
        accepted_profit = apply_accept(fleet, load, float(load["hour"]))
        if accepted_profit is not None:
            profit += accepted_profit
    return profit


def rollout_accepts(
    load: dict[str, object],
    fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    decision_index: int,
) -> tuple[bool, float, float, float]:
    hour = float(load["hour"])
    origin = str(load["origin_state"])
    if feas.available_count(fleet, origin, hour) <= 0:
        return False, float("-inf"), 0.0, 0.0

    accept_values: list[float] = []
    reject_values: list[float] = []
    for rep in range(ROLLOUT_REPLICATIONS):
        rng = random.Random(SEED + decision_index * 1009 + rep * 9176)
        future_loads = generate_future_loads(lanes, scenario, hour, rng)

        reject_fleet = copy_fleet(fleet)
        reject_values.append(
            simulate_future_profit(reject_fleet, future_loads, state_values)
        )

        accept_fleet = copy_fleet(fleet)
        accepted_profit = apply_accept(accept_fleet, load, hour)
        if accepted_profit is None:
            accept_values.append(float("-inf"))
        else:
            accept_values.append(
                accepted_profit
                + simulate_future_profit(accept_fleet, future_loads, state_values)
            )

    accept_value = statistics.mean(accept_values)
    reject_value = statistics.mean(reject_values)
    incremental_value = accept_value - reject_value
    return incremental_value >= 0, incremental_value, accept_value, reject_value


def choose_action(
    policy_name: str,
    load: dict[str, object],
    fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    decision_index: int,
) -> tuple[bool, float, float, float]:
    if policy_name == "myopic_margin":
        margin = float(load["price"]) - float(load["direct_cost"])
        return margin >= 0, margin, margin, 0.0
    if policy_name == "bid_price":
        accept, score, future_delta = base.policy_accepts(
            base.Policy("bid_price", 1.0, 0.0), load, state_values
        )
        return accept, score, future_delta, 0.0
    if policy_name == "rollout_teacher":
        return rollout_accepts(
            load, fleet, lanes, scenario, state_values, decision_index
        )
    raise ValueError(f"Unknown policy {policy_name}")


def simulate_policy(
    policy_name: str,
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    fleet = copy_fleet(starting_fleet)
    latency_ms: list[float] = []
    accepted = 0
    rejected = 0
    no_truck = 0
    profit = 0.0
    revenue = 0.0
    direct_cost = 0.0
    loaded_miles = 0.0
    busy_hours = 0.0
    sampled_decisions: list[dict[str, object]] = []

    for idx, load in enumerate(loads):
        hour = float(load["hour"])
        start = time.perf_counter_ns()
        wants_accept, score, branch_a, branch_b = choose_action(
            policy_name, load, fleet, lanes, scenario, state_values, idx
        )
        latency_ms.append((time.perf_counter_ns() - start) / 1_000_000)

        outcome = "reject"
        if wants_accept:
            accepted_profit = apply_accept(fleet, load, hour)
            if accepted_profit is None:
                no_truck += 1
                outcome = "no_truck"
            else:
                accepted += 1
                profit += accepted_profit
                revenue += float(load["price"])
                direct_cost += float(load["direct_cost"])
                loaded_miles += float(load["distance_miles"])
                busy_hours += float(load["travel_hours"])
                outcome = "accept"
        else:
            rejected += 1

        if len(sampled_decisions) < DECISION_SAMPLE_LIMIT:
            sampled_decisions.append(
                {
                    "policy": policy_name,
                    "load_id": load["load_id"],
                    "hour": load["hour"],
                    "origin": load["origin_name"],
                    "destination_city": load["destination_city"],
                    "destination_state": load["destination_name"],
                    "price": f"{float(load['price']):.2f}",
                    "direct_cost": f"{float(load['direct_cost']):.2f}",
                    "margin": f"{float(load['price']) - float(load['direct_cost']):.2f}",
                    "score": f"{score:.2f}",
                    "branch_a": f"{branch_a:.2f}",
                    "branch_b": f"{branch_b:.2f}",
                    "wants_accept": wants_accept,
                    "outcome": outcome,
                    "latency_ms": f"{latency_ms[-1]:.6f}",
                }
            )

    final_trucks = Counter({state: len(times) for state, times in fleet.items()})
    summary = {
        "policy": policy_name,
        "loads_seen": len(loads),
        "accepted": accepted,
        "rejected": rejected,
        "no_truck": no_truck,
        "accept_rate": f"{accepted / len(loads):.4f}",
        "profit": f"{profit:.2f}",
        "revenue": f"{revenue:.2f}",
        "direct_cost": f"{direct_cost:.2f}",
        "loaded_miles": f"{loaded_miles:.2f}",
        "profit_per_loaded_mile": f"{profit / loaded_miles if loaded_miles else 0.0:.4f}",
        "utilization": f"{busy_hours / (scenario.fleet_size * scenario.horizon_hours):.4f}",
        "mean_latency_ms": f"{statistics.mean(latency_ms):.6f}",
        "p50_latency_ms": f"{statistics.median(latency_ms):.6f}",
        "p95_latency_ms": f"{percentile(latency_ms, 0.95):.6f}",
        "final_top_states": "; ".join(
            f"{state}:{count}" for state, count in final_trucks.most_common(6)
        ),
    }
    return summary, sampled_decisions


def write_report(summary_rows: list[dict[str, object]], elapsed_seconds: float) -> None:
    best_profit = max(float(row["profit"]) for row in summary_rows)
    myopic_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "myopic_margin"
    )
    rollout_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "rollout_teacher"
    )

    table = [
        "| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | Mean Latency ms | p95 Latency ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(summary_rows, key=lambda item: float(item["profit"]), reverse=True):
        profit = float(row["profit"])
        table.append(
            f"| {row['policy']} | ${profit:,.0f} | {profit / best_profit:.1%} | "
            f"{row['accepted']} | {row['no_truck']} | {float(row['utilization']):.1%} | "
            f"{float(row['mean_latency_ms']):.3f} | {float(row['p95_latency_ms']):.3f} |"
        )

    content = f"""# Rollout Teacher Report

## Configuration

- Scenario: `{ROLLOUT_SCENARIO.name}`
- Horizon: {ROLLOUT_SCENARIO.horizon_hours} hours
- Loads/hour target: {ROLLOUT_SCENARIO.loads_per_hour}
- Fleet size: {ROLLOUT_SCENARIO.fleet_size}
- Rollout replications per decision: {ROLLOUT_REPLICATIONS}
- Rollout lookahead window: {LOOKAHEAD_HOURS} hours
- Future rollout load rate: {FUTURE_LOADS_PER_HOUR} loads/hour
- Future base policy: `{ROLLOUT_BASE_POLICY.name}`
- Total script runtime: {elapsed_seconds:.2f} seconds

## Policy Results

{chr(10).join(table)}

## Key Findings

- Rollout profit lift over myopic: ${rollout_profit - myopic_profit:,.0f}
- Rollout profit retention versus best policy in this probe: {rollout_profit / best_profit:.1%}
- The rollout teacher is much slower than the analytic bid-price policies, which is exactly the latency gap the paper should later exploit with surrogates or cascades.

## Interpretation

This is the first CPU rollout teacher. For each online candidate load, it compares accept and reject by running common-random-number future simulations from the branch fleet states. It is intentionally small and not optimized.

The next step is to turn rollout decisions into offline labels and test whether a cheap surrogate or cascade can recover most of the rollout behavior at bid-price-like latency.
"""
    REPORT_OUT.write_text(content, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    lanes = base.load_csv(base.LANES)
    loads = base.generate_loads(lanes, ROLLOUT_SCENARIO)
    state_values = base.build_state_values(lanes, ROLLOUT_SCENARIO)
    starting_fleet = base.initial_fleet(lanes, ROLLOUT_SCENARIO)

    summary_rows: list[dict[str, object]] = []
    decision_rows: list[dict[str, object]] = []
    for policy_name in ["myopic_margin", "bid_price", "rollout_teacher"]:
        summary, decisions = simulate_policy(
            policy_name, loads, starting_fleet, lanes, ROLLOUT_SCENARIO, state_values
        )
        summary_rows.append(summary)
        decision_rows.extend(decisions)

    elapsed = time.perf_counter() - start
    write_csv(SUMMARY_OUT, summary_rows)
    write_csv(DECISIONS_OUT, decision_rows)
    write_report(summary_rows, elapsed)
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    for row in sorted(summary_rows, key=lambda item: float(item["profit"]), reverse=True):
        print(
            f"{row['policy']}: profit ${float(row['profit']):,.0f}, "
            f"mean latency {float(row['mean_latency_ms']):.3f} ms"
        )


if __name__ == "__main__":
    main()
