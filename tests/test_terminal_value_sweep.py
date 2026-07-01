import unittest

from scripts import run_terminal_value_sweep as sweep


class TerminalValueSweepTests(unittest.TestCase):
    def test_configured_scenarios_sets_only_requested_weight(self):
        config = {
            "scenarios": {
                "tight": {"terminal_value_weight": 0.0},
                "scarce": {"terminal_value_weight": 0.0},
            }
        }

        updated = sweep.configured_scenarios(config, ["tight"], 0.5)

        self.assertEqual(updated["scenarios"]["tight"]["terminal_value_weight"], 0.5)
        self.assertEqual(updated["scenarios"]["scarce"]["terminal_value_weight"], 0.0)
        self.assertEqual(config["scenarios"]["tight"]["terminal_value_weight"], 0.0)

    def test_comparison_rows_reports_gate(self):
        rows = [
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "accept_all_feasible",
                "cascade_band_dollars": "",
                "mean_profit": "90.00",
                "mean_terminal_fleet_value": "-10.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "myopic_margin",
                "cascade_band_dollars": "",
                "mean_profit": "91.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "bid_price",
                "cascade_band_dollars": "",
                "mean_profit": "92.00",
            },
            {
                "scenario": "freightbidbench_tight_capacity",
                "policy": "rollout_teacher",
                "cascade_band_dollars": "",
                "mean_profit": "100.00",
                "mean_terminal_fleet_value": "5.00",
            },
        ]

        [result] = sweep.comparison_rows(0.5, ["tight"], rows)

        self.assertEqual(result["accept_all_feasible_retention_gap_pp"], "10.00")
        self.assertEqual(result["accept_all_feasible_terminal_value"], "-10.00")
        self.assertEqual(result["rollout_terminal_value"], "5.00")
        self.assertTrue(result["gate_met"])


if __name__ == "__main__":
    unittest.main()
