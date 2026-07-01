import unittest

from scripts import freight_feasibility as feas
from scripts import run_hindsight_bound as hb


def make_load(
    load_id: int,
    hour: float,
    origin: str,
    destination: str,
    profit: float,
    linehaul_hours: float = 1.0,
) -> dict[str, object]:
    return {
        "load_id": load_id,
        "hour": hour,
        "origin_state": origin,
        "destination_state": destination,
        "price": 1000.0 + profit,
        "direct_cost": 1000.0,
        "base_cost_per_mile": 1.0,
        "distance_miles": 50.0,
        "pickup_deadhead_hours": 0.0,
        "pickup_deadhead_miles": 0.0,
        "linehaul_drive_hours": linehaul_hours,
        "travel_hours": linehaul_hours,
        "pickup_earliest": hour,
        "pickup_latest": hour + 8.0,
        "delivery_earliest": hour,
        "delivery_latest": hour + 24.0,
        "pickup_yard_delay_hours": 0.0,
        "dropoff_yard_delay_hours": 0.0,
    }


class HindsightBoundTests(unittest.TestCase):
    def tearDown(self):
        feas.reset_config()

    def test_exact_hindsight_rejects_early_profit_for_better_later_load(self):
        fleet = {"A": [feas.TruckState("truck-1", "A", 0.0)]}
        loads = [
            make_load(1, 0.0, "A", "B", 100.0),
            make_load(2, 1.0, "A", "C", 500.0),
        ]

        solution = hb.exact_hindsight_bound(loads, fleet)

        self.assertAlmostEqual(solution.profit, 500.0)
        self.assertEqual(solution.accepted_load_ids, (2,))

    def test_exact_hindsight_accepts_compatible_sequence(self):
        fleet = {"A": [feas.TruckState("truck-1", "A", 0.0)]}
        loads = [
            make_load(1, 0.0, "A", "B", 100.0),
            make_load(2, 4.0, "B", "C", 500.0),
        ]

        solution = hb.exact_hindsight_bound(loads, fleet)

        self.assertAlmostEqual(solution.profit, 600.0)
        self.assertEqual(solution.accepted_load_ids, (1, 2))


if __name__ == "__main__":
    unittest.main()
