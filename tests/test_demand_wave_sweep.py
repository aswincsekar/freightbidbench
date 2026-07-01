import unittest

from scripts import run_demand_wave_sweep as sweep


class DemandWaveSweepTests(unittest.TestCase):
    def test_global_wave_schedule_uses_equal_low_high_segments(self):
        schedule = sweep.wave_schedule(0.25, mode="global")

        self.assertEqual(schedule["period_hours"], 24)
        multipliers = [segment["multiplier"] for segment in schedule["segments"]]
        self.assertEqual(multipliers, [0.75, 1.25, 0.75, 1.25])

    def test_market_wave_schedule_shifts_texas_origin_destination(self):
        schedule = sweep.wave_schedule(0.25, mode="market")

        self.assertEqual(schedule["type"], "market_origin_destination_piecewise")
        self.assertEqual(schedule["market_state"], "48")
        first_segment = schedule["segments"][0]
        second_segment = schedule["segments"][1]
        self.assertEqual(first_segment["origin_state_multipliers"], {"48": 0.75})
        self.assertEqual(first_segment["destination_state_multipliers"], {"48": 1.25})
        self.assertEqual(second_segment["origin_state_multipliers"], {"48": 1.25})
        self.assertEqual(second_segment["destination_state_multipliers"], {"48": 0.75})

    def test_combined_wave_schedule_changes_count_and_lanes(self):
        schedule = sweep.wave_schedule(0.25, mode="combined")

        first_segment = schedule["segments"][0]
        self.assertEqual(schedule["type"], "count_and_market_piecewise")
        self.assertEqual(first_segment["multiplier"], 0.75)
        self.assertEqual(first_segment["origin_state_multipliers"], {"48": 0.75})
        self.assertEqual(first_segment["destination_state_multipliers"], {"48": 1.25})

    def test_price_wave_schedule_adds_daily_price_premium(self):
        schedule = sweep.wave_schedule(0.25, mode="price")

        self.assertEqual(schedule["type"], "price_premium_piecewise")
        self.assertEqual(schedule["default_price_multiplier"], 1.0)
        price_multipliers = [
            segment["price_multiplier"] for segment in schedule["segments"]
        ]
        self.assertEqual(price_multipliers, [1.0, 1.25, 1.0])

    def test_zero_amplitude_removes_schedule(self):
        self.assertIsNone(sweep.wave_schedule(0.0))

    def test_comparison_rows_reports_best_simple_gate(self):
        rows = [
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "accept_all_feasible",
                "cascade_band_dollars": "",
                "mean_profit": "85.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "myopic_margin",
                "cascade_band_dollars": "",
                "mean_profit": "88.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "bid_price",
                "cascade_band_dollars": "",
                "mean_profit": "87.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "rollout_teacher",
                "cascade_band_dollars": "",
                "mean_profit": "100.00",
            },
        ]

        [result] = sweep.comparison_rows(0.5, ["tight"], rows)

        self.assertEqual(result["wave_mode"], "market")
        self.assertEqual(result["best_simple_policy"], "myopic_margin")
        self.assertEqual(result["best_simple_retention_vs_rollout"], "0.880000")
        self.assertEqual(result["best_simple_gap_pp"], "12.00")
        self.assertTrue(result["gate_met"])


if __name__ == "__main__":
    unittest.main()
