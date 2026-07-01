import unittest

from scripts import run_surrogate_cascade as sc


def positive_margin_load() -> dict[str, object]:
    return {
        "load_id": 1,
        "hour": 0.0,
        "origin_state": "A",
        "origin_name": "A",
        "destination_state": "B",
        "destination_name": "B",
        "destination_city": "B",
        "availability": "Adequate",
        "price": 1500.0,
        "direct_cost": 1000.0,
        "base_cost_per_mile": 1.0,
        "distance_miles": 50.0,
        "travel_hours": 1.0,
        "linehaul_drive_hours": 1.0,
        "pickup_deadhead_hours": 0.0,
        "pickup_deadhead_miles": 0.0,
        "pickup_earliest": 0.0,
        "pickup_latest": 4.0,
        "delivery_earliest": 0.0,
        "delivery_latest": 12.0,
        "pickup_yard_delay_hours": 0.0,
        "dropoff_yard_delay_hours": 0.0,
        "faf_tons_2024": 1.0,
    }


class ServiceFailurePenaltyTests(unittest.TestCase):
    def test_failed_accept_subtracts_configured_penalty(self):
        scenario = sc.base.Scenario(
            "penalty_probe",
            horizon_hours=1,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            service_failure_penalty_dollars=250.0,
        )

        summary, decisions = sc.simulate_policy(
            "myopic_margin",
            [positive_margin_load()],
            {"A": []},
            [],
            scenario,
            {},
            sc.LinearModel([], [], [], [0.0]),
        )

        self.assertEqual(summary["accepted"], 0)
        self.assertEqual(summary["no_truck"], 1)
        self.assertEqual(summary["profit"], "-250.00")
        self.assertEqual(summary["service_failure_penalty_cost"], "250.00")
        self.assertEqual(decisions[0]["service_failure_penalty_dollars"], "250.00")

    def test_accept_all_feasible_rejects_before_penalty(self):
        scenario = sc.base.Scenario(
            "penalty_probe",
            horizon_hours=1,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            service_failure_penalty_dollars=250.0,
        )

        summary, _ = sc.simulate_policy(
            "accept_all_feasible",
            [positive_margin_load()],
            {"A": []},
            [],
            scenario,
            {},
            sc.LinearModel([], [], [], [0.0]),
        )

        self.assertEqual(summary["accepted"], 0)
        self.assertEqual(summary["rejected"], 1)
        self.assertEqual(summary["no_truck"], 0)
        self.assertEqual(summary["profit"], "0.00")
        self.assertEqual(summary["service_failure_penalty_cost"], "0.00")


class TerminalFleetValueTests(unittest.TestCase):
    def test_terminal_value_is_added_to_final_profit(self):
        scenario = sc.base.Scenario(
            "terminal_probe",
            horizon_hours=1,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            terminal_value_weight=1.0,
        )

        summary, _ = sc.simulate_policy(
            "accept_all_feasible",
            [positive_margin_load()],
            {"A": [sc.feas.TruckState("truck-1", "A", 0.0)]},
            [],
            scenario,
            {"A": -100.0, "B": 500.0},
            sc.LinearModel([], [], [], [0.0]),
        )

        self.assertEqual(summary["accepted"], 1)
        self.assertEqual(summary["terminal_fleet_value"], "500.00")
        self.assertEqual(summary["profit"], "1000.00")


class SurrogateFeatureTests(unittest.TestCase):
    def test_features_include_service_failure_risk_without_mutating_fleet(self):
        scenario = sc.base.Scenario(
            "feature_probe",
            horizon_hours=1,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            service_failure_penalty_dollars=250.0,
        )
        fleet = {"A": []}

        features = sc.extract_features(positive_margin_load(), fleet, scenario, {})

        self.assertEqual(features["feasible_accept"], 0.0)
        self.assertEqual(features["service_failure_risk"], 1.0)
        self.assertAlmostEqual(features["service_failure_penalty"], 0.05)
        self.assertEqual(fleet, {"A": []})

    def test_features_include_price_window_and_terminal_value(self):
        scenario = sc.base.Scenario(
            "feature_probe",
            horizon_hours=24,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            terminal_value_weight=0.25,
            demand_wave_schedule={
                "type": "price_premium_piecewise",
                "period_hours": 24,
                "default_price_multiplier": 1.0,
                "segments": [
                    {
                        "start_hour": 0,
                        "end_hour": 8,
                        "multiplier": 1.0,
                        "price_multiplier": 1.0,
                    },
                    {
                        "start_hour": 8,
                        "end_hour": 16,
                        "multiplier": 1.0,
                        "price_multiplier": 1.5,
                    },
                ],
            },
        )
        load = positive_margin_load() | {
            "hour": 9.0,
            "pickup_earliest": 9.0,
            "pickup_latest": 13.0,
            "delivery_earliest": 9.0,
            "delivery_latest": 21.0,
        }
        fleet = {"A": [sc.feas.TruckState("truck-1", "A", 0.0)]}

        features = sc.extract_features(load, fleet, scenario, {"A": -100.0, "B": 500.0})

        self.assertEqual(features["feasible_accept"], 1.0)
        self.assertEqual(features["service_failure_risk"], 0.0)
        self.assertAlmostEqual(features["price_wave_multiplier"], 1.5)
        self.assertAlmostEqual(features["price_window_premium"], 0.5)
        self.assertAlmostEqual(features["terminal_destination_value"], 125.0 / 5000.0)
        self.assertAlmostEqual(features["terminal_delta"], 150.0 / 5000.0)

    def test_surrogate_positive_prediction_is_guarded_when_infeasible(self):
        scenario = sc.base.Scenario(
            "feature_probe",
            horizon_hours=1,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            service_failure_penalty_dollars=250.0,
        )
        model = sc.LinearModel([], [], [], [1.0])

        accept, score, stage = sc.choose_action(
            "surrogate_linear",
            positive_margin_load(),
            {"A": []},
            [],
            scenario,
            {},
            model,
            0,
        )

        self.assertFalse(accept)
        self.assertGreater(score, 0.0)
        self.assertEqual(stage, "surrogate_feasibility_guard")


if __name__ == "__main__":
    unittest.main()
