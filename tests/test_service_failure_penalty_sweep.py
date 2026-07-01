import unittest

from scripts import run_service_failure_penalty_sweep as sweep


class ServiceFailurePenaltySweepTests(unittest.TestCase):
    def test_configured_scenarios_sets_only_requested_penalty(self):
        config = {
            "scenarios": {
                "tight": {"service_failure_penalty_dollars": 0.0},
                "scarce": {"service_failure_penalty_dollars": 0.0},
            }
        }

        updated = sweep.configured_scenarios(config, ["tight"], 250.0)

        self.assertEqual(
            updated["scenarios"]["tight"]["service_failure_penalty_dollars"],
            250.0,
        )
        self.assertEqual(
            updated["scenarios"]["scarce"]["service_failure_penalty_dollars"],
            0.0,
        )
        self.assertEqual(
            config["scenarios"]["tight"]["service_failure_penalty_dollars"],
            0.0,
        )

    def test_comparison_rows_reports_ordering_gate(self):
        rows = [
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "accept_all_feasible",
                "cascade_band_dollars": "",
                "mean_profit": "100.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "myopic_margin",
                "cascade_band_dollars": "",
                "mean_profit": "90.00",
                "mean_service_failure_penalty_cost": "20.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "bid_price",
                "cascade_band_dollars": "",
                "mean_profit": "80.00",
                "mean_service_failure_penalty_cost": "30.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "rollout_teacher",
                "cascade_band_dollars": "",
                "mean_profit": "110.00",
            },
        ]

        [result] = sweep.comparison_rows(250.0, ["tight"], rows)

        self.assertEqual(result["myopic_gap_vs_accept_all_feasible"], "-10.00")
        self.assertEqual(result["bid_price_gap_vs_accept_all_feasible"], "-20.00")
        self.assertEqual(result["myopic_service_failure_penalty_cost"], "20.00")
        self.assertTrue(result["ordering_met"])


if __name__ == "__main__":
    unittest.main()
