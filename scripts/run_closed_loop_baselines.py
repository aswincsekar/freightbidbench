#!/usr/bin/env python3
"""Run the first closed-loop FreightBidBench baseline simulation.

This MVP uses the public-calibrated USDA/FAF seed lane table. It is still a
small benchmark harness, not a rollout teacher. The goal is to verify that
accept/reject policies create different fleet states and realized profit when
accepted loads move trucks across the network.
"""

from __future__ import annotations

import csv
import random
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANES = ROOT / "data" / "processed" / "v1_usda_faf_mapped_lanes.csv"
IMBALANCE = ROOT / "data" / "processed" / "faf_state_imbalance_2024.csv"
SUMMARY_OUT = ROOT / "data" / "processed" / "closed_loop_policy_summary.csv"
DECISIONS_OUT = ROOT / "data" / "processed" / "closed_loop_decision_samples.csv"
REPORT_OUT = ROOT / "reports" / "closed_loop_baseline_report.md"

SEED = 20260506
HORIZON_HOURS = 168
LOADS_PER_HOUR = 18
FLEET_SIZE = 250
TRUCK_SPEED_MPH = 50.0
SERVICE_HOURS = 3.0
BASE_COST_PER_MILE = 2.85
FIXED_LOAD_COST = 250.0
VALUE_SCALE_DOLLARS = 2200.0
DECISION_SAMPLE_LIMIT = 500

STATE_NAMES = {
    "04": "Arizona",
    "06": "California",
    "08": "Colorado",
    "12": "Florida",
    "13": "Georgia",
    "17": "Illinois",
    "24": "Maryland",
    "25": "Massachusetts",
    "36": "New York",
    "42": "Pennsylvania",
    "48": "Texas",
    "53": "Washington",
}


@dataclass(frozen=True)
class Policy:
    name: str
    future_delta_scale: float
    threshold: float
    always_reject: bool = False


@dataclass(frozen=True)
class Scenario:
    name: str
    horizon_hours: int
    loads_per_hour: int
    fleet_size: int
    base_cost_per_mile: float
    fixed_load_cost: float
    value_scale_dollars: float


POLICIES = [
    Policy("always_reject", 0.0, 0.0, always_reject=True),
    Policy("myopic_margin", 0.0, 0.0),
    Policy("lane_score_weak", 0.35, 0.0),
    Policy("bid_price", 1.0, 0.0),
    Policy("bid_price_conservative", 1.0, 250.0),
    Policy("bid_price_strong_future", 1.5, 0.0),
]

SCENARIOS = [
    Scenario("base_public_calibrated", 168, 18, 250, 2.85, 250.0, 2200.0),
    Scenario("tight_capacity", 168, 24, 150, 3.10, 250.0, 2200.0),
    Scenario("scarce_capacity_high_demand", 168, 24, 100, 3.10, 250.0, 3000.0),
]


def as_float(value: str) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def state_name(state: str) -> str:
    return STATE_NAMES.get(state, state)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def lane_distance_miles(lane: dict[str, str]) -> float:
    tons = as_float(lane["faf_tons_2024"])
    tmiles = as_float(lane["faf_tmiles_2024"])
    if tons <= 0 or tmiles <= 0:
        return 1000.0
    return 1000.0 * tmiles / tons


def weighted_choice(rng: random.Random, rows: list[dict[str, str]], weights: list[float]) -> dict[str, str]:
    total = sum(weights)
    target = rng.random() * total
    running = 0.0
    for row, weight in zip(rows, weights):
        running += weight
        if running >= target:
            return row
    return rows[-1]


def build_state_values(lanes: list[dict[str, str]], scenario: Scenario) -> dict[str, float]:
    imbalance_rows = load_csv(IMBALANCE)
    imbalances = {
        row["state"]: as_float(row["net_outbound_tons_2024"]) for row in imbalance_rows
    }
    max_abs_imbalance = max(abs(value) for value in imbalances.values())

    outbound_tons: defaultdict[str, float] = defaultdict(float)
    all_states: set[str] = set()
    for lane in lanes:
        origin = lane["origin_state"]
        destination = lane["destination_state"]
        all_states.add(origin)
        all_states.add(destination)
        outbound_tons[origin] += as_float(lane["faf_tons_2024"])
    max_outbound = max(outbound_tons.values())

    values: dict[str, float] = {}
    for state in all_states:
        outbound_norm = 2.0 * (outbound_tons.get(state, 0.0) / max_outbound) - 1.0
        imbalance_norm = imbalances.get(state, 0.0) / max_abs_imbalance
        values[state] = scenario.value_scale_dollars * (
            0.70 * outbound_norm + 0.30 * imbalance_norm
        )
    return values


def initial_fleet(lanes: list[dict[str, str]], scenario: Scenario) -> dict[str, list[float]]:
    rng = random.Random(SEED + 17)
    origin_weights: defaultdict[str, float] = defaultdict(float)
    for lane in lanes:
        origin_weights[lane["origin_state"]] += as_float(lane["faf_tons_2024"])

    states = sorted(origin_weights)
    weights = [origin_weights[state] for state in states]
    fleet: dict[str, list[float]] = {state: [] for state in states}
    for _ in range(scenario.fleet_size):
        state = weighted_choice(
            rng, [{"state": state} for state in states], weights
        )["state"]
        fleet[state].append(0.0)
    return fleet


def generate_loads(lanes: list[dict[str, str]], scenario: Scenario) -> list[dict[str, object]]:
    rng = random.Random(SEED)
    weights = [max(as_float(lane["faf_tons_2024"]), 1e-6) for lane in lanes]
    loads: list[dict[str, object]] = []
    load_id = 0
    for hour in range(scenario.horizon_hours):
        count = max(0, int(round(rng.gauss(scenario.loads_per_hour, 3.0))))
        for _ in range(count):
            lane = weighted_choice(rng, lanes, weights)
            distance = lane_distance_miles(lane)
            scarcity = as_float(lane["scarcity_multiplier"])
            price_noise = min(1.35, max(0.65, rng.gauss(1.0, 0.09)))
            price = as_float(lane["rate_midpoint"]) * price_noise * (0.9 + 0.1 * scarcity)
            direct_cost = distance * scenario.base_cost_per_mile + scenario.fixed_load_cost
            travel_hours = distance / TRUCK_SPEED_MPH + SERVICE_HOURS
            loads.append(
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
                    "travel_hours": travel_hours,
                    "faf_tons_2024": as_float(lane["faf_tons_2024"]),
                }
            )
            load_id += 1
    return loads


def pop_available_truck(fleet: dict[str, list[float]], state: str, hour: float) -> bool:
    available_times = fleet.setdefault(state, [])
    best_index = None
    best_time = None
    for idx, available_time in enumerate(available_times):
        if available_time <= hour and (best_time is None or available_time < best_time):
            best_index = idx
            best_time = available_time
    if best_index is None:
        return False
    available_times.pop(best_index)
    return True


def add_truck(fleet: dict[str, list[float]], state: str, available_time: float) -> None:
    fleet.setdefault(state, []).append(available_time)


def available_count(fleet: dict[str, list[float]], state: str, hour: float) -> int:
    return sum(1 for available_time in fleet.get(state, []) if available_time <= hour)


def policy_accepts(policy: Policy, load: dict[str, object], state_values: dict[str, float]) -> tuple[bool, float, float]:
    if policy.always_reject:
        return False, 0.0, 0.0
    margin = float(load["price"]) - float(load["direct_cost"])
    origin = str(load["origin_state"])
    destination = str(load["destination_state"])
    future_delta = state_values.get(destination, 0.0) - state_values.get(origin, 0.0)
    score = margin + policy.future_delta_scale * future_delta
    return score >= policy.threshold, score, future_delta


def simulate_policy(
    policy: Policy,
    scenario: Scenario,
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[float]],
    state_values: dict[str, float],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    fleet = {state: list(times) for state, times in starting_fleet.items()}
    accepted = 0
    rejected = 0
    no_truck = 0
    profit = 0.0
    revenue = 0.0
    direct_cost = 0.0
    loaded_miles = 0.0
    busy_hours = 0.0
    latency_ms: list[float] = []
    decision_rows: list[dict[str, object]] = []

    for load in loads:
        hour = float(load["hour"])
        start = time.perf_counter_ns()
        wants_accept, score, future_delta = policy_accepts(policy, load, state_values)
        latency_ms.append((time.perf_counter_ns() - start) / 1_000_000)

        origin = str(load["origin_state"])
        destination = str(load["destination_state"])
        available_at_origin = available_count(fleet, origin, hour)

        outcome = "reject"
        if wants_accept:
            if pop_available_truck(fleet, origin, hour):
                accepted += 1
                load_profit = float(load["price"]) - float(load["direct_cost"])
                profit += load_profit
                revenue += float(load["price"])
                direct_cost += float(load["direct_cost"])
                loaded_miles += float(load["distance_miles"])
                busy_hours += float(load["travel_hours"])
                add_truck(fleet, destination, hour + float(load["travel_hours"]))
                outcome = "accept"
            else:
                no_truck += 1
                outcome = "no_truck"
        else:
            rejected += 1

        if len(decision_rows) < DECISION_SAMPLE_LIMIT or outcome in {"no_truck"}:
            margin = float(load["price"]) - float(load["direct_cost"])
            decision_rows.append(
                {
                    "scenario": scenario.name,
                    "policy": policy.name,
                    "load_id": load["load_id"],
                    "hour": load["hour"],
                    "origin": load["origin_name"],
                    "destination_city": load["destination_city"],
                    "destination_state": load["destination_name"],
                    "availability": load["availability"],
                    "available_at_origin": available_at_origin,
                    "price": f"{float(load['price']):.2f}",
                    "direct_cost": f"{float(load['direct_cost']):.2f}",
                    "margin": f"{margin:.2f}",
                    "future_delta": f"{future_delta:.2f}",
                    "policy_score": f"{score:.2f}",
                    "wants_accept": wants_accept,
                    "outcome": outcome,
                }
            )

    final_trucks = Counter({state: len(times) for state, times in fleet.items()})
    active_origin_states = {
        str(load["origin_state"]) for load in loads
    }
    stranded_trucks = sum(
        count for state, count in final_trucks.items() if state not in active_origin_states
    )

    summary = {
        "scenario": scenario.name,
        "horizon_hours": scenario.horizon_hours,
        "loads_per_hour": scenario.loads_per_hour,
        "fleet_size": scenario.fleet_size,
        "base_cost_per_mile": f"{scenario.base_cost_per_mile:.2f}",
        "fixed_load_cost": f"{scenario.fixed_load_cost:.2f}",
        "value_scale_dollars": f"{scenario.value_scale_dollars:.2f}",
        "policy": policy.name,
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
        "p50_latency_ms": f"{statistics.median(latency_ms):.6f}",
        "p95_latency_ms": f"{percentile(latency_ms, 0.95):.6f}",
        "final_stranded_trucks": stranded_trucks,
        "final_top_states": "; ".join(
            f"{state}:{count}" for state, count in final_trucks.most_common(6)
        ),
    }
    return summary, decision_rows


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[idx]


def write_report(
    summary_rows: list[dict[str, object]],
    scenario_load_counts: dict[str, int],
    scenario_state_values: dict[str, dict[str, float]],
) -> None:
    config_lines = [
        "| Scenario | Horizon | Loads | Fleet | Loads/Hour | Cost/Mile | Value Scale |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scenario in SCENARIOS:
        config_lines.append(
            f"| {scenario.name} | {scenario.horizon_hours}h | "
            f"{scenario_load_counts[scenario.name]:,} | {scenario.fleet_size} | "
            f"{scenario.loads_per_hour} | ${scenario.base_cost_per_mile:.2f} | "
            f"${scenario.value_scale_dollars:,.0f} |"
        )

    result_sections: list[str] = []
    key_findings: list[str] = []
    for scenario in SCENARIOS:
        scenario_rows = [
            row for row in summary_rows if row["scenario"] == scenario.name
        ]
        best_profit = max(float(row["profit"]) for row in scenario_rows)
        myopic_profit = next(
            float(row["profit"])
            for row in scenario_rows
            if row["policy"] == "myopic_margin"
        )
        best_row = max(scenario_rows, key=lambda row: float(row["profit"]))
        key_findings.append(
            f"- `{scenario.name}` best policy: `{best_row['policy']}` "
            f"(${float(best_row['profit']):,.0f}); lift over myopic: "
            f"${float(best_row['profit']) - myopic_profit:,.0f}."
        )

        table_lines = [
            "| Policy | Profit | Retention vs Best | Accepted | No Truck | Utilization | p95 Latency ms | Stranded Trucks |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for row in sorted(scenario_rows, key=lambda item: float(item["profit"]), reverse=True):
            profit = float(row["profit"])
            table_lines.append(
                f"| {row['policy']} | ${profit:,.0f} | {profit / best_profit:.1%} | "
                f"{row['accepted']} | {row['no_truck']} | {float(row['utilization']):.1%} | "
                f"{float(row['p95_latency_ms']):.6f} | {row['final_stranded_trucks']} |"
            )
        result_sections.append(
            f"### {scenario.name}\n\n" + "\n".join(table_lines)
        )

    base_values = scenario_state_values[SCENARIOS[0].name]
    state_lines = "\n".join(
        f"- {state_name(state)} ({state}): ${value:,.0f}" for state, value in sorted(
            base_values.items(), key=lambda item: item[1], reverse=True
        )[:10]
    )

    content = f"""# Closed-Loop Baseline Report

## Configuration

- Random seed: {SEED}
- Input lane table: `{LANES.relative_to(ROOT)}`

{chr(10).join(config_lines)}

## Key Findings

{chr(10).join(key_findings)}

## Policy Results

{chr(10) + (chr(10) * 2).join(result_sections)}

## Highest State Opportunity Values In Base Scenario

The first bid-price policies use a simple future-value proxy derived from seed-lane outbound intensity and FAF state imbalance.

{state_lines}

## Interpretation

This is the first closed-loop harness: accepted loads move trucks to destination states and make those trucks unavailable until delivery. The result is not an ADP or rollout teacher yet, but it verifies that policy choices compound through fleet state.

The base public-calibrated setting is intentionally mild. It shows whether simple direct-margin bidding is already enough. The tight-capacity scenarios are stress tests designed to expose downstream opportunity cost by making truck placement scarce.

The next benchmark step is to add a rollout teacher that evaluates accept versus reject by simulating future loads from this same environment.
"""
    REPORT_OUT.write_text(content, encoding="utf-8")


def main() -> None:
    lanes = load_csv(LANES)
    summaries: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    scenario_load_counts: dict[str, int] = {}
    scenario_state_values: dict[str, dict[str, float]] = {}

    for scenario in SCENARIOS:
        loads = generate_loads(lanes, scenario)
        state_values = build_state_values(lanes, scenario)
        starting_fleet = initial_fleet(lanes, scenario)
        scenario_load_counts[scenario.name] = len(loads)
        scenario_state_values[scenario.name] = state_values

        for policy in POLICIES:
            summary, policy_decisions = simulate_policy(
                policy, scenario, loads, starting_fleet, state_values
            )
            summaries.append(summary)
            decisions.extend(policy_decisions)

    write_csv(SUMMARY_OUT, summaries)
    write_csv(DECISIONS_OUT, decisions)
    write_report(summaries, scenario_load_counts, scenario_state_values)
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    for scenario in SCENARIOS:
        scenario_rows = [row for row in summaries if row["scenario"] == scenario.name]
        print(scenario.name)
        for row in sorted(scenario_rows, key=lambda item: float(item["profit"]), reverse=True):
            print(f"  {row['policy']}: profit ${float(row['profit']):,.0f}, accepted {row['accepted']}")


if __name__ == "__main__":
    main()
