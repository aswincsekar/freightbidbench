import csv
import tempfile
import unittest
from pathlib import Path

from scripts import assemble_v03_paper_tables as tables


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class AssembleV03PaperTablesTests(unittest.TestCase):
    def test_methods_table_selects_low_latency_cascade_above_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "methods"
            write_csv(
                run_dir / "freightbidbench_policy_summary.csv",
                [
                    {
                        "scenario": "freightbidbench_tight_capacity",
                        "policy": "accept_all_feasible",
                        "cascade_band_dollars": "",
                        "mean_profit": "80.00",
                        "mean_profit_retention_vs_rollout": "0.800000",
                        "mean_latency_ms": "0.01",
                    },
                    {
                        "scenario": "freightbidbench_tight_capacity",
                        "policy": "surrogate_linear",
                        "cascade_band_dollars": "",
                        "mean_profit": "90.00",
                        "mean_profit_retention_vs_rollout": "0.900000",
                        "mean_latency_ms": "0.03",
                    },
                    {
                        "scenario": "freightbidbench_tight_capacity",
                        "policy": "cascade_surrogate_rollout",
                        "cascade_band_dollars": "0.00",
                        "mean_profit": "98.00",
                        "mean_profit_retention_vs_rollout": "0.980000",
                        "mean_latency_ms": "8.00",
                    },
                    {
                        "scenario": "freightbidbench_tight_capacity",
                        "policy": "cascade_surrogate_rollout",
                        "cascade_band_dollars": "500.00",
                        "mean_profit": "99.00",
                        "mean_profit_retention_vs_rollout": "0.990000",
                        "mean_latency_ms": "12.00",
                    },
                    {
                        "scenario": "freightbidbench_tight_capacity",
                        "policy": "rollout_teacher",
                        "cascade_band_dollars": "",
                        "mean_profit": "100.00",
                        "mean_profit_retention_vs_rollout": "1.000000",
                        "mean_latency_ms": "30.00",
                    },
                ],
            )

            [row] = tables.methods_rows(run_dir)

            self.assertEqual(row["scenario"], "tight")
            self.assertEqual(row["best_simple_policy"], "accept_all_feasible")
            self.assertEqual(row["cascade_band_dollars"], "0.00")
            self.assertEqual(row["cascade_retention_vs_rollout"], "0.980000")


if __name__ == "__main__":
    unittest.main()
