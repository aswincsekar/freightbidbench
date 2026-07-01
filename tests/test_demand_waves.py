import unittest

from scripts import run_closed_loop_baselines as base


class DemandWaveTests(unittest.TestCase):
    def test_piecewise_schedule_repeats_by_period(self):
        scenario = base.Scenario(
            "wave_probe",
            horizon_hours=24,
            loads_per_hour=10,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            demand_wave_schedule={
                "period_hours": 24,
                "default_multiplier": 1.0,
                "segments": [
                    {"start_hour": 0, "end_hour": 6, "multiplier": 0.5},
                    {"start_hour": 6, "end_hour": 12, "multiplier": 1.5},
                ],
            },
        )

        self.assertAlmostEqual(base.demand_wave_multiplier(scenario, 2.0), 0.5)
        self.assertAlmostEqual(base.demand_wave_multiplier(scenario, 8.0), 1.5)
        self.assertAlmostEqual(base.demand_wave_multiplier(scenario, 14.0), 1.0)
        self.assertAlmostEqual(base.demand_wave_multiplier(scenario, 26.0), 0.5)
        self.assertAlmostEqual(base.expected_loads_per_hour(scenario, 8.0), 15.0)

    def test_missing_schedule_keeps_flat_load_rate(self):
        scenario = base.Scenario(
            "flat_probe",
            horizon_hours=24,
            loads_per_hour=10,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
        )

        self.assertAlmostEqual(base.demand_wave_multiplier(scenario, 8.0), 1.0)
        self.assertAlmostEqual(base.expected_loads_per_hour(scenario, 8.0), 10.0)

    def test_lane_wave_applies_origin_and_destination_multipliers(self):
        scenario = base.Scenario(
            "lane_wave_probe",
            horizon_hours=24,
            loads_per_hour=10,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            demand_wave_schedule={
                "period_hours": 24,
                "default_multiplier": 1.0,
                "segments": [
                    {
                        "start_hour": 0,
                        "end_hour": 12,
                        "multiplier": 1.0,
                        "origin_state_multipliers": {"48": 0.5},
                        "destination_state_multipliers": {"06": 2.0},
                    },
                ],
            },
        )

        texas_to_california = {"origin_state": "48", "destination_state": "06"}
        texas_to_new_york = {"origin_state": "48", "destination_state": "36"}
        self.assertAlmostEqual(
            base.lane_demand_wave_multiplier(scenario, texas_to_california, 3.0),
            1.0,
        )
        self.assertAlmostEqual(
            base.lane_demand_wave_multiplier(scenario, texas_to_new_york, 3.0),
            0.5,
        )
        self.assertAlmostEqual(
            base.lane_demand_wave_multiplier(scenario, texas_to_new_york, 15.0),
            1.0,
        )

    def test_price_wave_applies_segment_and_lane_multipliers(self):
        scenario = base.Scenario(
            "price_wave_probe",
            horizon_hours=24,
            loads_per_hour=10,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            demand_wave_schedule={
                "period_hours": 24,
                "default_price_multiplier": 1.0,
                "segments": [
                    {
                        "start_hour": 6,
                        "end_hour": 12,
                        "multiplier": 1.0,
                        "price_multiplier": 1.2,
                        "origin_price_multipliers": {"48": 1.5},
                        "destination_price_multipliers": {"06": 0.5},
                    },
                ],
            },
        )

        texas_to_california = {"origin_state": "48", "destination_state": "06"}
        texas_to_new_york = {"origin_state": "48", "destination_state": "36"}
        self.assertAlmostEqual(
            base.demand_wave_price_multiplier(scenario, texas_to_california, 8.0),
            0.9,
        )
        self.assertAlmostEqual(
            base.demand_wave_price_multiplier(scenario, texas_to_new_york, 8.0),
            1.8,
        )
        self.assertAlmostEqual(
            base.demand_wave_price_multiplier(scenario, texas_to_new_york, 14.0),
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
