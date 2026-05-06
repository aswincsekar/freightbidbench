#!/usr/bin/env python3
"""Feasibility layer for FreightBidBench.

The v0.2 benchmark keeps the public-calibrated state-level network, but it
tracks individual truck state for assignment feasibility:

- pickup reach time inside the origin market,
- pickup and delivery appointment windows,
- simplified U.S. property-carrying HOS clocks,
- stochastic shipper/receiver yard delays.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


MAX_DRIVE_HOURS = 11.0
MAX_DUTY_HOURS = 14.0
RESET_HOURS = 10.0
LOCAL_DEADHEAD_SPEED_MPH = 38.0
PICKUP_BASE_SERVICE_HOURS = 1.0
DROPOFF_BASE_SERVICE_HOURS = 1.0
YARD_DELAY_COST_PER_HOUR = 65.0
DEADHEAD_COST_FACTOR = 0.90


@dataclass(frozen=True)
class FeasibilityConfig:
    enable_pickup_reach: bool = True
    enable_time_windows: bool = True
    enable_hos: bool = True
    enable_yard_delays: bool = True


@dataclass
class TruckState:
    truck_id: str
    state: str
    available_time: float
    drive_used_hours: float = 0.0
    duty_used_hours: float = 0.0


@dataclass
class AssignmentResult:
    accepted: bool
    outcome: str
    profit: float = 0.0
    truck_id: str = ""
    final_state: str = ""
    final_available_time: float = 0.0
    deadhead_miles: float = 0.0
    yard_delay_hours: float = 0.0
    hos_rest_hours: float = 0.0
    busy_hours: float = 0.0
    pickup_start: float = 0.0
    delivery_arrival: float = 0.0
    realized_cost: float = 0.0


@dataclass
class ScheduleResult:
    feasible: bool
    outcome: str
    final_available_time: float = 0.0
    drive_used_hours: float = 0.0
    duty_used_hours: float = 0.0
    hos_rest_hours: float = 0.0
    pickup_start: float = 0.0
    delivery_arrival: float = 0.0


DEFAULT_CONFIG = FeasibilityConfig()
ACTIVE_CONFIG = DEFAULT_CONFIG


def set_config(config: FeasibilityConfig) -> None:
    global ACTIVE_CONFIG
    ACTIVE_CONFIG = config


def reset_config() -> None:
    set_config(DEFAULT_CONFIG)


def get_config() -> FeasibilityConfig:
    return ACTIVE_CONFIG


def config_from_disabled(
    disable_pickup_reach: bool = False,
    disable_time_windows: bool = False,
    disable_hos: bool = False,
    disable_yard_delays: bool = False,
) -> FeasibilityConfig:
    return FeasibilityConfig(
        enable_pickup_reach=not disable_pickup_reach,
        enable_time_windows=not disable_time_windows,
        enable_hos=not disable_hos,
        enable_yard_delays=not disable_yard_delays,
    )


def config_to_dict(config: FeasibilityConfig | None = None) -> dict[str, object]:
    active = config or ACTIVE_CONFIG
    disabled = [
        name
        for name, enabled in [
            ("pickup_reach_time", active.enable_pickup_reach),
            ("pickup_delivery_windows", active.enable_time_windows),
            ("simplified_hos_11_14_10", active.enable_hos),
            ("stochastic_pickup_dropoff_yard_delays", active.enable_yard_delays),
        ]
        if not enabled
    ]
    return {
        "version": "v0.2",
        "enabled": True,
        "features": {
            "pickup_reach_time": active.enable_pickup_reach,
            "pickup_delivery_windows": active.enable_time_windows,
            "simplified_hos_11_14_10": active.enable_hos,
            "stochastic_pickup_dropoff_yard_delays": active.enable_yard_delays,
        },
        "disabled_features": disabled,
    }


def enabled_feature_names(config: FeasibilityConfig | None = None) -> list[str]:
    active = config or ACTIVE_CONFIG
    return [
        name
        for name, enabled in [
            ("pickup reach time", active.enable_pickup_reach),
            ("pickup/delivery windows", active.enable_time_windows),
            ("HOS clocks", active.enable_hos),
            ("stochastic yard delays", active.enable_yard_delays),
        ]
        if enabled
    ]


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def truck_available_time(truck: TruckState | float) -> float:
    if isinstance(truck, TruckState):
        return truck.available_time
    return float(truck)


def copy_fleet(
    fleet: dict[str, list[TruckState | float]]
) -> dict[str, list[TruckState | float]]:
    copied: dict[str, list[TruckState | float]] = {}
    for state, trucks in fleet.items():
        copied[state] = [
            TruckState(
                truck.truck_id,
                truck.state,
                truck.available_time,
                truck.drive_used_hours,
                truck.duty_used_hours,
            )
            if isinstance(truck, TruckState)
            else float(truck)
            for truck in trucks
        ]
    return copied


def coerce_truck(truck: TruckState | float, state: str, index: int) -> TruckState:
    if isinstance(truck, TruckState):
        return truck
    return TruckState(f"{state}-{index}", state, float(truck))


def available_count(
    fleet: dict[str, list[TruckState | float]],
    state: str,
    hour: float,
) -> int:
    return sum(
        1 for truck in fleet.get(state, []) if truck_available_time(truck) <= hour
    )


def sample_yard_delay(rng: random.Random) -> float:
    draw = rng.random()
    if draw < 0.70:
        return clamp(rng.gauss(0.25, 0.20), 0.0, 0.75)
    if draw < 0.94:
        return rng.uniform(0.75, 2.25)
    return rng.uniform(2.25, 5.50)


def decorate_load(
    load: dict[str, object],
    rng: random.Random,
    truck_speed_mph: float,
) -> dict[str, object]:
    """Add pickup reach, appointment window, and yard-delay fields to a load."""
    hour = float(load["hour"])
    distance = float(load["distance_miles"])
    linehaul_drive_hours = distance / truck_speed_mph

    pickup_lead_hours = clamp(rng.gauss(3.0, 1.15), 0.75, 7.0)
    pickup_window_hours = clamp(rng.gauss(4.0, 1.0), 2.0, 7.0)
    delivery_window_hours = clamp(rng.gauss(12.0, 2.75), 6.0, 18.0)
    pickup_earliest = hour + pickup_lead_hours
    pickup_latest = pickup_earliest + pickup_window_hours

    planned_pickup_service = PICKUP_BASE_SERVICE_HOURS + 0.35
    delivery_earliest = pickup_earliest + planned_pickup_service + 0.90 * linehaul_drive_hours
    delivery_latest = pickup_earliest + planned_pickup_service + linehaul_drive_hours + delivery_window_hours

    deadhead_cap = clamp(0.18 * distance + 30.0, 45.0, 220.0)
    pickup_deadhead_miles = 0.0
    if ACTIVE_CONFIG.enable_pickup_reach:
        pickup_deadhead_miles = clamp(
            rng.lognormvariate(math.log(38.0), 0.55),
            5.0,
            deadhead_cap,
        )
    pickup_yard_delay = 0.0
    dropoff_yard_delay = 0.0
    if ACTIVE_CONFIG.enable_yard_delays:
        pickup_yard_delay = sample_yard_delay(rng)
        dropoff_yard_delay = sample_yard_delay(rng)

    load.update(
        {
            "linehaul_drive_hours": linehaul_drive_hours,
            "pickup_deadhead_miles": pickup_deadhead_miles,
            "pickup_deadhead_hours": pickup_deadhead_miles / LOCAL_DEADHEAD_SPEED_MPH,
            "pickup_earliest": pickup_earliest,
            "pickup_latest": pickup_latest,
            "pickup_window_hours": pickup_window_hours,
            "delivery_earliest": delivery_earliest,
            "delivery_latest": delivery_latest,
            "delivery_window_hours": delivery_window_hours,
            "pickup_yard_delay_hours": pickup_yard_delay,
            "dropoff_yard_delay_hours": dropoff_yard_delay,
        }
    )
    return load


def maybe_reset_for_wait(
    time: float,
    target_time: float,
    drive_used: float,
    duty_used: float,
) -> tuple[float, float, float]:
    if not ACTIVE_CONFIG.enable_hos:
        return target_time, 0.0, 0.0
    if target_time <= time:
        return time, drive_used, duty_used
    wait = target_time - time
    if wait >= RESET_HOURS:
        return target_time, 0.0, 0.0
    return target_time, drive_used, duty_used


def add_drive(
    time: float,
    drive_hours: float,
    drive_used: float,
    duty_used: float,
) -> tuple[float, float, float, float]:
    if not ACTIVE_CONFIG.enable_hos:
        return time + max(0.0, drive_hours), 0.0, 0.0, 0.0
    remaining = max(0.0, drive_hours)
    rest_hours = 0.0
    while remaining > 1e-9:
        drive_capacity = MAX_DRIVE_HOURS - drive_used
        duty_capacity = MAX_DUTY_HOURS - duty_used
        if drive_capacity <= 1e-9 or duty_capacity <= 1e-9:
            time += RESET_HOURS
            rest_hours += RESET_HOURS
            drive_used = 0.0
            duty_used = 0.0
            continue
        segment = min(remaining, drive_capacity, duty_capacity)
        time += segment
        drive_used += segment
        duty_used += segment
        remaining -= segment
    return time, drive_used, duty_used, rest_hours


def add_on_duty(
    time: float,
    hours: float,
    drive_used: float,
    duty_used: float,
) -> tuple[float, float, float, float]:
    if not ACTIVE_CONFIG.enable_hos:
        return time + max(0.0, hours), 0.0, 0.0, 0.0
    remaining = max(0.0, hours)
    rest_hours = 0.0
    while remaining > 1e-9:
        duty_capacity = MAX_DUTY_HOURS - duty_used
        if duty_capacity <= 1e-9:
            time += RESET_HOURS
            rest_hours += RESET_HOURS
            drive_used = 0.0
            duty_used = 0.0
            continue
        segment = min(remaining, duty_capacity)
        time += segment
        duty_used += segment
        remaining -= segment
    return time, drive_used, duty_used, rest_hours


def plan_schedule(
    truck: TruckState,
    load: dict[str, object],
    decision_hour: float,
) -> ScheduleResult:
    time = max(decision_hour, truck.available_time)
    drive_used = truck.drive_used_hours
    duty_used = truck.duty_used_hours
    rest_hours = 0.0

    time, drive_used, duty_used, added_rest = add_drive(
        time, float(load.get("pickup_deadhead_hours", 0.0)), drive_used, duty_used
    )
    rest_hours += added_rest

    pickup_earliest = float(load.get("pickup_earliest", decision_hour))
    pickup_latest = float(load.get("pickup_latest", pickup_earliest + 4.0))
    if ACTIVE_CONFIG.enable_time_windows and time > pickup_latest:
        return ScheduleResult(False, "pickup_window_miss")
    if ACTIVE_CONFIG.enable_time_windows:
        time, drive_used, duty_used = maybe_reset_for_wait(
            time, pickup_earliest, drive_used, duty_used
        )
    pickup_start = time

    pickup_service = PICKUP_BASE_SERVICE_HOURS + float(load.get("pickup_yard_delay_hours", 0.0))
    time, drive_used, duty_used, added_rest = add_on_duty(
        time, pickup_service, drive_used, duty_used
    )
    rest_hours += added_rest

    time, drive_used, duty_used, added_rest = add_drive(
        time, float(load.get("linehaul_drive_hours", load.get("travel_hours", 0.0))),
        drive_used,
        duty_used,
    )
    rest_hours += added_rest
    delivery_arrival = time

    delivery_earliest = float(load.get("delivery_earliest", delivery_arrival))
    delivery_latest = float(load.get("delivery_latest", delivery_arrival + 12.0))
    if ACTIVE_CONFIG.enable_time_windows and delivery_arrival > delivery_latest:
        return ScheduleResult(False, "delivery_window_miss")
    if ACTIVE_CONFIG.enable_time_windows:
        time, drive_used, duty_used = maybe_reset_for_wait(
            time, delivery_earliest, drive_used, duty_used
        )

    dropoff_service = DROPOFF_BASE_SERVICE_HOURS + float(load.get("dropoff_yard_delay_hours", 0.0))
    time, drive_used, duty_used, added_rest = add_on_duty(
        time, dropoff_service, drive_used, duty_used
    )
    rest_hours += added_rest

    return ScheduleResult(
        True,
        "accept",
        final_available_time=time,
        drive_used_hours=drive_used,
        duty_used_hours=duty_used,
        hos_rest_hours=rest_hours,
        pickup_start=pickup_start,
        delivery_arrival=delivery_arrival,
    )


def realized_profit(load: dict[str, object]) -> tuple[float, float]:
    base_cost_per_mile = float(load.get("base_cost_per_mile", 3.0))
    deadhead_miles = (
        float(load.get("pickup_deadhead_miles", 0.0))
        if ACTIVE_CONFIG.enable_pickup_reach
        else 0.0
    )
    yard_delay = 0.0
    if ACTIVE_CONFIG.enable_yard_delays:
        yard_delay = float(load.get("pickup_yard_delay_hours", 0.0)) + float(
            load.get("dropoff_yard_delay_hours", 0.0)
        )
    extra_cost = (
        deadhead_miles * base_cost_per_mile * DEADHEAD_COST_FACTOR
        + yard_delay * YARD_DELAY_COST_PER_HOUR
    )
    profit = float(load["price"]) - float(load["direct_cost"]) - extra_cost
    return profit, extra_cost


def apply_accept(
    fleet: dict[str, list[TruckState | float]],
    load: dict[str, object],
    decision_hour: float,
) -> AssignmentResult:
    origin = str(load["origin_state"])
    destination = str(load["destination_state"])
    candidates = fleet.get(origin, [])
    if not candidates:
        return AssignmentResult(False, "no_truck")

    best: tuple[float, int, TruckState, ScheduleResult] | None = None
    infeasible_outcome = "infeasible"
    for idx, raw_truck in enumerate(candidates):
        truck = coerce_truck(raw_truck, origin, idx)
        if (
            ACTIVE_CONFIG.enable_time_windows
            and truck.available_time > float(load.get("pickup_latest", decision_hour + 4.0))
        ):
            infeasible_outcome = "pickup_window_miss"
            continue
        schedule = plan_schedule(truck, load, decision_hour)
        if not schedule.feasible:
            infeasible_outcome = schedule.outcome
            continue
        rank = schedule.final_available_time
        if best is None or rank < best[0]:
            best = (rank, idx, truck, schedule)

    if best is None:
        return AssignmentResult(False, infeasible_outcome)

    _, idx, truck, schedule = best
    updated = TruckState(
        truck.truck_id,
        destination,
        schedule.final_available_time,
        schedule.drive_used_hours,
        schedule.duty_used_hours,
    )
    candidates.pop(idx)
    fleet.setdefault(destination, []).append(updated)

    profit, extra_cost = realized_profit(load)
    deadhead_miles = (
        float(load.get("pickup_deadhead_miles", 0.0))
        if ACTIVE_CONFIG.enable_pickup_reach
        else 0.0
    )
    yard_delay = 0.0
    if ACTIVE_CONFIG.enable_yard_delays:
        yard_delay = float(load.get("pickup_yard_delay_hours", 0.0)) + float(
            load.get("dropoff_yard_delay_hours", 0.0)
        )
    return AssignmentResult(
        True,
        "accept",
        profit=profit,
        truck_id=truck.truck_id,
        final_state=destination,
        final_available_time=schedule.final_available_time,
        deadhead_miles=deadhead_miles,
        yard_delay_hours=yard_delay,
        hos_rest_hours=schedule.hos_rest_hours,
        busy_hours=schedule.final_available_time - max(decision_hour, truck.available_time),
        pickup_start=schedule.pickup_start,
        delivery_arrival=schedule.delivery_arrival,
        realized_cost=float(load["direct_cost"]) + extra_cost,
    )
