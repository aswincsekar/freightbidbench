import unittest

from scripts import freight_feasibility as feas


class FeasibilityTests(unittest.TestCase):
    def test_hos_rest_is_inserted_after_drive_limit(self):
        time, drive_used, duty_used, rest_hours = feas.add_drive(0.0, 12.0, 0.0, 0.0)

        self.assertAlmostEqual(time, 22.0)
        self.assertAlmostEqual(drive_used, 1.0)
        self.assertAlmostEqual(duty_used, 1.0)
        self.assertAlmostEqual(rest_hours, 10.0)

    def test_accept_moves_truck_and_charges_feasibility_costs(self):
        fleet = {
            "CA": [feas.TruckState("truck-1", "CA", 0.0)],
            "TX": [],
        }
        load = {
            "origin_state": "CA",
            "destination_state": "TX",
            "price": 2000.0,
            "direct_cost": 1000.0,
            "base_cost_per_mile": 3.0,
            "pickup_deadhead_hours": 1.0,
            "pickup_deadhead_miles": 38.0,
            "linehaul_drive_hours": 2.0,
            "pickup_earliest": 1.0,
            "pickup_latest": 4.0,
            "delivery_earliest": 4.0,
            "delivery_latest": 8.0,
            "pickup_yard_delay_hours": 0.0,
            "dropoff_yard_delay_hours": 0.0,
        }

        result = feas.apply_accept(fleet, load, decision_hour=0.0)

        self.assertTrue(result.accepted)
        self.assertEqual(result.outcome, "accept")
        self.assertEqual(len(fleet["CA"]), 0)
        self.assertEqual(len(fleet["TX"]), 1)
        self.assertEqual(fleet["TX"][0].truck_id, "truck-1")
        self.assertAlmostEqual(result.deadhead_miles, 38.0)
        self.assertLess(result.profit, 1000.0)

    def test_pickup_window_miss_is_reported(self):
        fleet = {"CA": [feas.TruckState("truck-1", "CA", 0.0)]}
        load = {
            "origin_state": "CA",
            "destination_state": "TX",
            "price": 2000.0,
            "direct_cost": 1000.0,
            "pickup_deadhead_hours": 1.0,
            "pickup_deadhead_miles": 38.0,
            "linehaul_drive_hours": 2.0,
            "pickup_earliest": 0.0,
            "pickup_latest": 0.5,
            "delivery_earliest": 3.0,
            "delivery_latest": 10.0,
            "pickup_yard_delay_hours": 0.0,
            "dropoff_yard_delay_hours": 0.0,
        }

        result = feas.apply_accept(fleet, load, decision_hour=0.0)

        self.assertFalse(result.accepted)
        self.assertEqual(result.outcome, "pickup_window_miss")
        self.assertEqual(len(fleet["CA"]), 1)


if __name__ == "__main__":
    unittest.main()
