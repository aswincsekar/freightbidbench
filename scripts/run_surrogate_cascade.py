#!/usr/bin/env python3
"""Train a first rollout-label surrogate and evaluate a cascade.

This script is intentionally dependency-free. The surrogate is a small linear
regression model trained on rollout incremental-value labels. It is not meant to
be the final ML model; it is the first end-to-end test of the paper's core
idea: can offline rollout labels support a much faster online approximation?
"""

from __future__ import annotations

import csv
import math
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

import run_closed_loop_baselines as base  # noqa: E402
import run_rollout_teacher as rollout  # noqa: E402
import freight_feasibility as feas  # noqa: E402


TRAIN_LABELS_OUT = ROOT / "data" / "processed" / "surrogate_train_rollout_labels.csv"
EVAL_LABELS_OUT = ROOT / "data" / "processed" / "surrogate_eval_rollout_labels.csv"
WEIGHTS_OUT = ROOT / "data" / "processed" / "surrogate_linear_weights.csv"
SUMMARY_OUT = ROOT / "data" / "processed" / "surrogate_cascade_summary.csv"
DECISIONS_OUT = ROOT / "data" / "processed" / "surrogate_cascade_decisions.csv"
FRONTIER_OUT = ROOT / "data" / "processed" / "cascade_frontier.csv"
REPORT_OUT = ROOT / "reports" / "surrogate_cascade_report.md"

TRAIN_SEED = 20260506
EVAL_SEED = 20260507
TARGET_SCALE = 5000.0
PREDICTION_TARGET = "rollout_incremental_value"
CASCADE_BAND_DOLLARS = 500.0
CASCADE_FRONTIER_BANDS = [0.0, 100.0, 250.0, 500.0, 700.0, 900.0, 1200.0]
LABEL_DECISION_LIMIT = 1200
DECISION_SAMPLE_LIMIT = 500

SCENARIO = base.Scenario(
    "surrogate_probe_tight_capacity",
    horizon_hours=72,
    loads_per_hour=14,
    fleet_size=70,
    base_cost_per_mile=3.10,
    fixed_load_cost=250.0,
    value_scale_dollars=3000.0,
)


@dataclass
class LinearModel:
    feature_names: list[str]
    means: list[float]
    scales: list[float]
    weights: list[float]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[idx]


def copy_fleet(fleet: dict[str, list[object]]) -> dict[str, list[object]]:
    return feas.copy_fleet(fleet)


def generate_loads_with_seed(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    seed: int,
) -> list[dict[str, object]]:
    rng = random.Random(seed)
    base_weights = [max(base.as_float(lane["faf_tons_2024"]), 1e-6) for lane in lanes]
    loads: list[dict[str, object]] = []
    load_id = 0
    for hour in range(scenario.horizon_hours):
        expected_count = base.expected_loads_per_hour(scenario, float(hour))
        count = max(0, int(round(rng.gauss(expected_count, 3.0))))
        hour_weights = [
            weight * base.lane_demand_wave_multiplier(scenario, lane, float(hour))
            for lane, weight in zip(lanes, base_weights)
        ]
        for _ in range(count):
            lane = base.weighted_choice(rng, lanes, hour_weights)
            distance = base.lane_distance_miles(lane)
            scarcity = base.as_float(lane["scarcity_multiplier"])
            price_noise = min(1.35, max(0.65, rng.gauss(1.0, 0.09)))
            price = (
                base.as_float(lane["rate_midpoint"])
                * price_noise
                * (0.9 + 0.1 * scarcity)
                * base.demand_wave_price_multiplier(scenario, lane, float(hour))
            )
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
                        "scarcity_multiplier": scarcity,
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


def initial_fleet_with_seed(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    seed: int,
) -> dict[str, list[object]]:
    rng = random.Random(seed + 17)
    origin_weights: defaultdict[str, float] = defaultdict(float)
    for lane in lanes:
        origin_weights[lane["origin_state"]] += base.as_float(lane["faf_tons_2024"])

    states = sorted(origin_weights)
    weights = [origin_weights[state] for state in states]
    fleet: dict[str, list[object]] = {state: [] for state in states}
    for truck_idx in range(scenario.fleet_size):
        state = base.weighted_choice(
            rng, [{"state": state} for state in states], weights
        )["state"]
        fleet[state].append(feas.TruckState(f"T{truck_idx:04d}", state, 0.0))
    return fleet


def extract_features(
    load: dict[str, object],
    fleet: dict[str, list[object]],
    scenario: base.Scenario,
    state_values: dict[str, float],
) -> dict[str, float]:
    hour = float(load["hour"])
    origin = str(load["origin_state"])
    destination = str(load["destination_state"])
    price = float(load["price"])
    direct_cost = float(load["direct_cost"])
    distance = float(load["distance_miles"])
    margin = price - direct_cost
    origin_value = state_values.get(origin, 0.0)
    destination_value = state_values.get(destination, 0.0)
    future_delta = destination_value - origin_value
    available = feas.available_count(fleet, origin, hour)
    price_per_mile = price / max(distance, 1.0)
    cost_per_mile = direct_cost / max(distance, 1.0)
    pickup_slack = float(load.get("pickup_latest", hour)) - hour
    delivery_slack = float(load.get("delivery_latest", hour + float(load["travel_hours"]))) - hour
    feasibility_probe = feas.apply_accept(feas.copy_fleet(fleet), load, hour)
    service_failure_penalty = base.service_failure_penalty_dollars(scenario)
    terminal_weight = base.terminal_value_weight(scenario)
    price_wave_multiplier = base.demand_wave_price_multiplier(scenario, load, hour)
    terminal_origin_value = terminal_weight * origin_value
    terminal_destination_value = terminal_weight * destination_value
    realized_profit_if_feasible = feasibility_probe.profit if feasibility_probe.accepted else -service_failure_penalty
    return {
        "bias": 1.0,
        "margin": margin / 5000.0,
        "realized_profit_if_feasible": realized_profit_if_feasible / 5000.0,
        "future_delta": future_delta / 5000.0,
        "price_per_mile": price_per_mile / 5.0,
        "cost_per_mile": cost_per_mile / 5.0,
        "price_wave_multiplier": price_wave_multiplier,
        "price_window_premium": max(0.0, price_wave_multiplier - 1.0),
        "distance": distance / 3000.0,
        "available_at_origin": min(available, 20) / 20.0,
        "has_available_truck": 1.0 if available > 0 else 0.0,
        "feasible_accept": 1.0 if feasibility_probe.accepted else 0.0,
        "service_failure_risk": 0.0 if feasibility_probe.accepted else 1.0,
        "service_failure_penalty": service_failure_penalty / 5000.0,
        "pickup_deadhead_hours": float(load.get("pickup_deadhead_hours", 0.0)) / 6.0,
        "pickup_slack": pickup_slack / 24.0,
        "delivery_slack": delivery_slack / 72.0,
        "pickup_window": float(load.get("pickup_window_hours", 0.0)) / 12.0,
        "delivery_window": float(load.get("delivery_window_hours", 0.0)) / 24.0,
        "scarcity_multiplier": float(load.get("scarcity_multiplier", 1.0)),
        "origin_value": origin_value / 5000.0,
        "destination_value": destination_value / 5000.0,
        "terminal_origin_value": terminal_origin_value / 5000.0,
        "terminal_destination_value": terminal_destination_value / 5000.0,
        "terminal_delta": (terminal_destination_value - terminal_origin_value) / 5000.0,
        "same_state": 1.0 if origin == destination else 0.0,
        "hour_sin": math.sin(2.0 * math.pi * hour / 24.0),
        "hour_cos": math.cos(2.0 * math.pi * hour / 24.0),
        "faf_tons": math.log1p(float(load["faf_tons_2024"])) / 10.0,
    }


def generate_rollout_labels(
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    seed: int,
    state_values: dict[str, float],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, list[object]]]:
    loads = generate_loads_with_seed(lanes, scenario, seed)
    fleet = initial_fleet_with_seed(lanes, scenario, seed)
    labels: list[dict[str, object]] = []
    decision_rows: list[dict[str, object]] = []

    for idx, load in enumerate(loads[:LABEL_DECISION_LIMIT]):
        hour = float(load["hour"])
        feature_values = extract_features(load, fleet, scenario, state_values)
        start = time.perf_counter_ns()
        accept, incremental_value, accept_value, reject_value = rollout.rollout_accepts(
            load, fleet, lanes, scenario, state_values, idx + seed
        )
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000

        if incremental_value == float("-inf"):
            incremental_value = -TARGET_SCALE
        accepted_profit = None
        if accept:
            accepted_profit = rollout.apply_accept(fleet, load, hour)
            if accepted_profit is None:
                accept = False

        row: dict[str, object] = {
            "seed": seed,
            "load_id": load["load_id"],
            "hour": load["hour"],
            "origin_state": load["origin_state"],
            "destination_state": load["destination_state"],
            "origin_name": load["origin_name"],
            "destination_name": load["destination_name"],
            "destination_city": load["destination_city"],
            "price": f"{float(load['price']):.2f}",
            "direct_cost": f"{float(load['direct_cost']):.2f}",
            "pickup_earliest": f"{float(load.get('pickup_earliest', 0.0)):.2f}",
            "pickup_latest": f"{float(load.get('pickup_latest', 0.0)):.2f}",
            "delivery_earliest": f"{float(load.get('delivery_earliest', 0.0)):.2f}",
            "delivery_latest": f"{float(load.get('delivery_latest', 0.0)):.2f}",
            "pickup_deadhead_miles": f"{float(load.get('pickup_deadhead_miles', 0.0)):.2f}",
            "margin_dollars": f"{float(load['price']) - float(load['direct_cost']):.2f}",
            "rollout_accept": accept,
            "rollout_incremental_value": f"{incremental_value:.2f}",
            "accept_value": f"{accept_value:.2f}",
            "reject_value": f"{reject_value:.2f}",
            "rollout_latency_ms": f"{latency_ms:.6f}",
        }
        for name, value in feature_values.items():
            row[f"feature_{name}"] = f"{value:.8f}"
        labels.append(row)

        if len(decision_rows) < DECISION_SAMPLE_LIMIT:
            decision_rows.append(row)

    return labels, decision_rows, fleet


def train_linear_model(labels: list[dict[str, object]]) -> LinearModel:
    feature_names = sorted(
        key.removeprefix("feature_")
        for key in labels[0]
        if key.startswith("feature_") and key != "feature_bias"
    )
    # Bias is handled explicitly as the first weight.
    x_raw: list[list[float]] = []
    y: list[float] = []
    for row in labels:
        x_raw.append([as_float(row[f"feature_{name}"]) for name in feature_names])
        y.append(as_float(row[PREDICTION_TARGET]) / TARGET_SCALE)

    means = [
        statistics.mean(values) for values in zip(*x_raw)
    ]
    scales = []
    for col, mean in zip(zip(*x_raw), means):
        variance = statistics.mean([(value - mean) ** 2 for value in col])
        scales.append(math.sqrt(variance) or 1.0)

    x = [
        [1.0] + [(value - mean) / scale for value, mean, scale in zip(row, means, scales)]
        for row in x_raw
    ]
    weights = solve_ridge_regression(x, y, ridge=0.25)
    return LinearModel(feature_names, means, scales, weights)


def solve_ridge_regression(x: list[list[float]], y: list[float], ridge: float) -> list[float]:
    """Solve (X'X + ridge I)w = X'y with Gauss-Jordan elimination."""
    dim = len(x[0])
    xtx = [[0.0 for _ in range(dim)] for _ in range(dim)]
    xty = [0.0 for _ in range(dim)]

    for row, target in zip(x, y):
        for i in range(dim):
            xty[i] += row[i] * target
            for j in range(dim):
                xtx[i][j] += row[i] * row[j]

    for i in range(1, dim):
        xtx[i][i] += ridge

    matrix = [xtx_row + [rhs] for xtx_row, rhs in zip(xtx, xty)]
    for col in range(dim):
        pivot = max(range(col, dim), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1e-12:
            continue
        if pivot != col:
            matrix[col], matrix[pivot] = matrix[pivot], matrix[col]

        pivot_value = matrix[col][col]
        matrix[col] = [value / pivot_value for value in matrix[col]]
        for row_idx in range(dim):
            if row_idx == col:
                continue
            factor = matrix[row_idx][col]
            if factor == 0.0:
                continue
            matrix[row_idx] = [
                value - factor * pivot_value
                for value, pivot_value in zip(matrix[row_idx], matrix[col])
            ]

    return [row[-1] for row in matrix]


def predict_incremental_value(model: LinearModel, features: dict[str, float]) -> float:
    values = [features[name] for name in model.feature_names]
    x = [1.0] + [
        (value - mean) / scale
        for value, mean, scale in zip(values, model.means, model.scales)
    ]
    return TARGET_SCALE * sum(weight * value for weight, value in zip(model.weights, x))


def evaluate_static_labels(
    model: LinearModel,
    labels: list[dict[str, object]],
) -> dict[str, float]:
    correct = 0
    abs_errors: list[float] = []
    for row in labels:
        features = {
            key.removeprefix("feature_"): as_float(value)
            for key, value in row.items()
            if key.startswith("feature_")
        }
        pred = predict_incremental_value(model, features)
        actual = as_float(row[PREDICTION_TARGET])
        abs_errors.append(abs(pred - actual))
        if (pred >= 0) == (str(row["rollout_accept"]) == "True"):
            correct += 1
    return {
        "agreement": correct / len(labels),
        "mae": statistics.mean(abs_errors),
        "p90_abs_error": percentile(abs_errors, 0.90),
    }


def write_weights(model: LinearModel) -> None:
    rows = [
        {
            "feature": "bias",
            "mean": "0.000000",
            "scale": "1.000000",
            "weight": f"{model.weights[0]:.8f}",
        }
    ]
    for name, mean, scale, weight in zip(
        model.feature_names, model.means, model.scales, model.weights[1:]
    ):
        rows.append(
            {
                "feature": name,
                "mean": f"{mean:.8f}",
                "scale": f"{scale:.8f}",
                "weight": f"{weight:.8f}",
            }
        )
    write_csv(WEIGHTS_OUT, rows)


def choose_action(
    policy_name: str,
    load: dict[str, object],
    fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    model: LinearModel,
    decision_index: int,
    cascade_band_dollars: float = CASCADE_BAND_DOLLARS,
    rollout_seed_offset: int = EVAL_SEED,
) -> tuple[bool, float, str]:
    if policy_name == "reject_all":
        return False, 0.0, "rule"
    if policy_name == "accept_all_feasible":
        assignment = feas.apply_accept(
            feas.copy_fleet(fleet), load, float(load["hour"])
        )
        score = assignment.profit if assignment.accepted else -TARGET_SCALE
        return assignment.accepted, score, "feasibility_check"
    if policy_name == "myopic_margin":
        margin = float(load["price"]) - float(load["direct_cost"])
        return margin >= 0, margin, "myopic"
    if policy_name == "bid_price":
        accept, score, _ = base.policy_accepts(
            base.Policy("bid_price", 1.0, 0.0), load, state_values
        )
        return accept, score, "bid_price"
    if policy_name == "rollout_teacher":
        accept, incremental, _, _ = rollout.rollout_accepts(
            load, fleet, lanes, scenario, state_values, decision_index + rollout_seed_offset
        )
        return accept, incremental, "rollout"

    features = extract_features(load, fleet, scenario, state_values)
    pred = predict_incremental_value(model, features)
    if policy_name == "surrogate_linear":
        if pred >= 0 and features.get("feasible_accept", 0.0) < 0.5:
            return False, pred, "surrogate_feasibility_guard"
        return pred >= 0, pred, "surrogate"
    if policy_name == "cascade_surrogate_rollout":
        available = feas.available_count(fleet, str(load["origin_state"]), float(load["hour"]))
        should_escalate = abs(pred) <= cascade_band_dollars or available <= 2
        if should_escalate:
            accept, incremental, _, _ = rollout.rollout_accepts(
                load, fleet, lanes, scenario, state_values, decision_index + rollout_seed_offset
            )
            return accept, incremental, "rollout"
        if pred >= 0 and features.get("feasible_accept", 0.0) < 0.5:
            return False, pred, "surrogate_feasibility_guard"
        return pred >= 0, pred, "surrogate"
    raise ValueError(f"Unknown policy {policy_name}")


def simulate_policy(
    policy_name: str,
    loads: list[dict[str, object]],
    starting_fleet: dict[str, list[object]],
    lanes: list[dict[str, str]],
    scenario: base.Scenario,
    state_values: dict[str, float],
    model: LinearModel,
    cascade_band_dollars: float = CASCADE_BAND_DOLLARS,
    rollout_seed_offset: int = EVAL_SEED,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    fleet = copy_fleet(starting_fleet)
    latencies: list[float] = []
    accepted = 0
    rejected = 0
    no_truck = 0
    infeasible = 0
    pickup_window_miss = 0
    delivery_window_miss = 0
    profit = 0.0
    service_failure_penalty_cost = 0.0
    revenue = 0.0
    direct_cost = 0.0
    loaded_miles = 0.0
    deadhead_miles = 0.0
    yard_delay_hours = 0.0
    hos_rest_hours = 0.0
    busy_hours = 0.0
    stage_counts: Counter[str] = Counter()
    decisions: list[dict[str, object]] = []

    for idx, load in enumerate(loads):
        hour = float(load["hour"])
        start = time.perf_counter_ns()
        wants_accept, score, stage = choose_action(
            policy_name,
            load,
            fleet,
            lanes,
            scenario,
            state_values,
            model,
            idx,
            cascade_band_dollars,
            rollout_seed_offset,
        )
        latencies.append((time.perf_counter_ns() - start) / 1_000_000)
        stage_counts[stage] += 1

        outcome = "reject"
        if wants_accept:
            assignment = feas.apply_accept(fleet, load, hour)
            if not assignment.accepted:
                penalty = base.service_failure_penalty_dollars(scenario)
                profit -= penalty
                service_failure_penalty_cost += penalty
                if assignment.outcome == "no_truck":
                    no_truck += 1
                else:
                    infeasible += 1
                    if assignment.outcome == "pickup_window_miss":
                        pickup_window_miss += 1
                    elif assignment.outcome == "delivery_window_miss":
                        delivery_window_miss += 1
                outcome = assignment.outcome
            else:
                accepted += 1
                profit += assignment.profit
                revenue += float(load["price"])
                direct_cost += float(load["direct_cost"])
                loaded_miles += float(load["distance_miles"])
                deadhead_miles += assignment.deadhead_miles
                yard_delay_hours += assignment.yard_delay_hours
                hos_rest_hours += assignment.hos_rest_hours
                busy_hours += assignment.busy_hours
                outcome = "accept"
        else:
            rejected += 1

        if len(decisions) < DECISION_SAMPLE_LIMIT:
            margin = float(load["price"]) - float(load["direct_cost"])
            decisions.append(
                {
                    "policy": policy_name,
                    "load_id": load["load_id"],
                    "hour": load["hour"],
                    "origin": load["origin_name"],
                    "destination_city": load["destination_city"],
                    "destination_state": load["destination_name"],
                    "margin": f"{margin:.2f}",
                    "pickup_latest": f"{float(load.get('pickup_latest', 0.0)):.2f}",
                    "delivery_latest": f"{float(load.get('delivery_latest', 0.0)):.2f}",
                    "pickup_deadhead_miles": f"{float(load.get('pickup_deadhead_miles', 0.0)):.2f}",
                    "pickup_yard_delay_hours": f"{float(load.get('pickup_yard_delay_hours', 0.0)):.2f}",
                    "dropoff_yard_delay_hours": f"{float(load.get('dropoff_yard_delay_hours', 0.0)):.2f}",
                    "score": f"{score:.2f}",
                    "stage": stage,
                    "wants_accept": wants_accept,
                    "outcome": outcome,
                    "latency_ms": f"{latencies[-1]:.6f}",
                }
                | (
                    {
                        "service_failure_penalty_dollars": f"{base.service_failure_penalty_dollars(scenario):.2f}"
                        if wants_accept and outcome != "accept"
                        else "0.00"
                    }
                    if base.tracks_service_failure_penalty(scenario)
                    else {}
                )
            )

    final_trucks = Counter({state: len(times) for state, times in fleet.items()})
    terminal_value = base.terminal_fleet_value(fleet, scenario, state_values)
    profit += terminal_value
    summary = {
        "policy": policy_name,
        "cascade_band_dollars": f"{cascade_band_dollars:.2f}"
        if policy_name == "cascade_surrogate_rollout"
        else "",
        "loads_seen": len(loads),
        "accepted": accepted,
        "rejected": rejected,
        "no_truck": no_truck,
        "infeasible": infeasible,
        "pickup_window_miss": pickup_window_miss,
        "delivery_window_miss": delivery_window_miss,
        "accept_rate": f"{accepted / len(loads):.4f}",
        "profit": f"{profit:.2f}",
        "revenue": f"{revenue:.2f}",
        "direct_cost": f"{direct_cost:.2f}",
        "loaded_miles": f"{loaded_miles:.2f}",
        "deadhead_miles": f"{deadhead_miles:.2f}",
        "yard_delay_hours": f"{yard_delay_hours:.2f}",
        "hos_rest_hours": f"{hos_rest_hours:.2f}",
        "profit_per_loaded_mile": f"{profit / loaded_miles if loaded_miles else 0.0:.4f}",
        "utilization": f"{busy_hours / (scenario.fleet_size * scenario.horizon_hours):.4f}",
        "mean_latency_ms": f"{statistics.mean(latencies):.6f}",
        "p50_latency_ms": f"{statistics.median(latencies):.6f}",
        "p95_latency_ms": f"{percentile(latencies, 0.95):.6f}",
        "surrogate_stage_share": f"{stage_counts['surrogate'] / len(loads):.4f}",
        "rollout_stage_share": f"{stage_counts['rollout'] / len(loads):.4f}",
        "final_top_states": "; ".join(
            f"{state}:{count}" for state, count in final_trucks.most_common(6)
        ),
    }
    if base.tracks_service_failure_penalty(scenario):
        summary["service_failure_penalty_cost"] = f"{service_failure_penalty_cost:.2f}"
    if base.tracks_terminal_value(scenario):
        summary["terminal_fleet_value"] = f"{terminal_value:.2f}"
    return summary, decisions


def write_report(
    summary_rows: list[dict[str, object]],
    frontier_rows: list[dict[str, object]],
    static_metrics: dict[str, float],
    train_label_count: int,
    eval_label_count: int,
    elapsed_seconds: float,
) -> None:
    rollout_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "rollout_teacher"
    )
    myopic_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "myopic_margin"
    )
    table = [
        "| Policy | Profit | Retention vs Rollout | Accepted | No Truck | Mean Latency ms | p95 Latency ms | Rollout Stage Share |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(summary_rows, key=lambda item: float(item["profit"]), reverse=True):
        profit = float(row["profit"])
        table.append(
            f"| {row['policy']} | ${profit:,.0f} | {profit / rollout_profit:.1%} | "
            f"{row['accepted']} | {row['no_truck']} | "
            f"{float(row['mean_latency_ms']):.3f} | {float(row['p95_latency_ms']):.3f} | "
            f"{float(row['rollout_stage_share']):.1%} |"
        )

    frontier_table = [
        "| Band +/- $ | Profit Retention | Rollout Share | Mean Latency ms | Profit |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in frontier_rows:
        frontier_table.append(
            f"| {float(row['cascade_band_dollars']):,.0f} | "
            f"{float(row['profit_retention_vs_rollout']):.1%} | "
            f"{float(row['rollout_stage_share']):.1%} | "
            f"{float(row['mean_latency_ms']):.3f} | "
            f"${float(row['profit']):,.0f} |"
        )

    surrogate_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "surrogate_linear"
    )
    cascade_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "cascade_surrogate_rollout"
    )
    rollout_latency = next(
        float(row["mean_latency_ms"]) for row in summary_rows if row["policy"] == "rollout_teacher"
    )
    cascade_latency = next(
        float(row["mean_latency_ms"]) for row in summary_rows if row["policy"] == "cascade_surrogate_rollout"
    )
    surrogate_latency = next(
        float(row["mean_latency_ms"]) for row in summary_rows if row["policy"] == "surrogate_linear"
    )

    content = f"""# Surrogate And Cascade Report

## Configuration

- Scenario: `{SCENARIO.name}`
- Train seed: {TRAIN_SEED}
- Eval seed: {EVAL_SEED}
- Train rollout labels: {train_label_count:,}
- Eval rollout labels: {eval_label_count:,}
- Rollout label target: `{PREDICTION_TARGET}`
- Linear target scale: ${TARGET_SCALE:,.0f}
- Cascade rollout escalation band: +/- ${CASCADE_BAND_DOLLARS:,.0f}
- Total script runtime: {elapsed_seconds:.2f} seconds

## Offline Label Fit

- Held-out rollout accept/reject agreement: {static_metrics['agreement']:.1%}
- Held-out incremental-value MAE: ${static_metrics['mae']:,.0f}
- Held-out p90 absolute error: ${static_metrics['p90_abs_error']:,.0f}

## Closed-Loop Policy Results

{chr(10).join(table)}

## Cascade Frontier

{chr(10).join(frontier_table)}

## Key Findings

- Rollout profit lift over myopic: ${rollout_profit - myopic_profit:,.0f}
- Linear surrogate profit retention versus rollout: {surrogate_profit / rollout_profit:.1%}
- Cascade profit retention versus rollout: {cascade_profit / rollout_profit:.1%}
- Mean latency: rollout {rollout_latency:.3f} ms, cascade {cascade_latency:.3f} ms, surrogate {surrogate_latency:.3f} ms.

## Interpretation

This is the first end-to-end value-distillation test. The model is deliberately simple, so the important result is not final accuracy. The important question is whether a cheap approximation and a selective rollout cascade can recover useful rollout behavior while reducing online latency.

Next step: replace the linear surrogate with a stronger dependency-light model or generate a larger rollout-label set for an MLP/gradient-boosted baseline.
"""
    REPORT_OUT.write_text(content, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    lanes = base.load_csv(base.LANES)
    state_values = base.build_state_values(lanes, SCENARIO)

    train_labels, _, _ = generate_rollout_labels(lanes, SCENARIO, TRAIN_SEED, state_values)
    eval_labels, _, _ = generate_rollout_labels(lanes, SCENARIO, EVAL_SEED, state_values)
    write_csv(TRAIN_LABELS_OUT, train_labels)
    write_csv(EVAL_LABELS_OUT, eval_labels)

    model = train_linear_model(train_labels)
    write_weights(model)
    static_metrics = evaluate_static_labels(model, eval_labels)

    eval_loads = generate_loads_with_seed(lanes, SCENARIO, EVAL_SEED)
    starting_fleet = initial_fleet_with_seed(lanes, SCENARIO, EVAL_SEED)
    summary_rows: list[dict[str, object]] = []
    decision_rows: list[dict[str, object]] = []
    for policy_name in [
        "reject_all",
        "accept_all_feasible",
        "myopic_margin",
        "bid_price",
        "surrogate_linear",
        "cascade_surrogate_rollout",
        "rollout_teacher",
    ]:
        summary, decisions = simulate_policy(
            policy_name, eval_loads, starting_fleet, lanes, SCENARIO, state_values, model
        )
        summary_rows.append(summary)
        decision_rows.extend(decisions)

    rollout_profit = next(
        float(row["profit"]) for row in summary_rows if row["policy"] == "rollout_teacher"
    )
    frontier_rows: list[dict[str, object]] = []
    for band in CASCADE_FRONTIER_BANDS:
        summary, _ = simulate_policy(
            "cascade_surrogate_rollout",
            eval_loads,
            starting_fleet,
            lanes,
            SCENARIO,
            state_values,
            model,
            cascade_band_dollars=band,
        )
        profit = float(summary["profit"])
        frontier_rows.append(
            {
                "cascade_band_dollars": f"{band:.2f}",
                "profit": summary["profit"],
                "profit_retention_vs_rollout": f"{profit / rollout_profit:.6f}",
                "mean_latency_ms": summary["mean_latency_ms"],
                "p95_latency_ms": summary["p95_latency_ms"],
                "rollout_stage_share": summary["rollout_stage_share"],
                "surrogate_stage_share": summary["surrogate_stage_share"],
                "accepted": summary["accepted"],
                "no_truck": summary["no_truck"],
            }
        )

    elapsed = time.perf_counter() - start
    write_csv(SUMMARY_OUT, summary_rows)
    write_csv(DECISIONS_OUT, decision_rows)
    write_csv(FRONTIER_OUT, frontier_rows)
    write_report(
        summary_rows,
        frontier_rows,
        static_metrics,
        len(train_labels),
        len(eval_labels),
        elapsed,
    )

    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    for row in sorted(summary_rows, key=lambda item: float(item["profit"]), reverse=True):
        print(
            f"{row['policy']}: profit ${float(row['profit']):,.0f}, "
            f"mean latency {float(row['mean_latency_ms']):.3f} ms"
        )


if __name__ == "__main__":
    main()
