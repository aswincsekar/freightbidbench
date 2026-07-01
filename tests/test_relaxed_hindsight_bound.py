import unittest

from scripts import freight_feasibility as feas
from scripts import run_closed_loop_baselines as base
from scripts import run_hindsight_bound as exact
from scripts import run_relaxed_hindsight_bound as relaxed
from tests.test_hindsight_bound import make_load


class RelaxedHindsightBoundTests(unittest.TestCase):
    def tearDown(self):
        feas.reset_config()

    def test_fractional_knapsack_allows_fractional_final_load(self):
        terms = [
            relaxed.LoadTerm(1, 0.0, "A", "B", 100.0, 10.0, 10.0),
            relaxed.LoadTerm(2, 0.0, "A", "B", 80.0, 10.0, 10.0),
        ]

        self.assertAlmostEqual(relaxed.fractional_knapsack_profit(terms, 15.0), 140.0)

    def test_relaxed_bound_sits_above_exact_small_stream(self):
        scenario = base.Scenario(
            "probe",
            horizon_hours=4,
            loads_per_hour=1,
            fleet_size=1,
            base_cost_per_mile=1.0,
            fixed_load_cost=0.0,
            value_scale_dollars=0.0,
            terminal_value_weight=0.0,
        )
        loads = [
            make_load(1, 0.0, "A", "B", 100.0, linehaul_hours=3.0),
            make_load(2, 1.0, "A", "C", 500.0, linehaul_hours=1.0),
        ]
        fleet = {"A": [feas.TruckState("truck-1", "A", 0.0)]}
        exact_solution = exact.exact_hindsight_bound(loads, fleet, scenario, {})
        terms = relaxed.positive_terms(loads)
        capacity = scenario.fleet_size * (
            scenario.horizon_hours
            + max(term.fresh_truck_busy_hours for term in terms)
        )
        relaxed_bound = relaxed.fractional_knapsack_profit(terms, capacity)

        self.assertGreaterEqual(relaxed_bound, exact_solution.profit)


if __name__ == "__main__":
    unittest.main()
