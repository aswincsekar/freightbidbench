import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FreightBidBenchCliTests(unittest.TestCase):
    def test_tiny_benchmark_run_writes_manifest_and_summaries(self):
        expected_path = ROOT / "tests" / "golden" / "tiny_smoke_expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "freightbidbench_smoke"
            command = [
                sys.executable,
                "scripts/run_freightbidbench.py",
                "--preset",
                "smoke",
                "--seed-count",
                "1",
                "--label-limit",
                "5",
                "--eval-load-limit",
                "10",
                "--cascade-bands",
                "0",
                "--output-dir",
                str(output_dir),
            ]
            subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)

            manifest_path = output_dir / "freightbidbench_manifest.json"
            runs_path = output_dir / "freightbidbench_policy_runs.csv"
            summary_path = output_dir / "freightbidbench_policy_summary.csv"
            frontier_path = output_dir / "freightbidbench_frontier_summary.csv"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(runs_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(frontier_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected_manifest = expected["manifest"]
            for key in [
                "benchmark_version",
                "scenario_config_version",
                "policy_set_version",
                "scenario_config_path",
                "preset",
                "seed_pairs",
                "policies",
                "cascade_policy",
                "evaluated_policies",
                "cascade_bands_dollars",
                "label_limit",
                "eval_load_limit",
                "row_counts",
            ]:
                self.assertEqual(manifest[key], expected_manifest[key])
            self.assertEqual(
                sorted(manifest["scenarios"]),
                expected_manifest["scenario_keys"],
            )
            self.assertEqual(
                manifest["feasibility_layer"]["disabled_features"],
                expected_manifest["disabled_features"],
            )

            with runs_path.open(newline="", encoding="utf-8") as file:
                run_rows = [
                    {
                        "policy": row["policy"],
                        "cascade_band_dollars": row["cascade_band_dollars"],
                    }
                    for row in csv.DictReader(file)
                ]
            self.assertEqual(run_rows, expected["policy_run_rows"])

            with summary_path.open(newline="", encoding="utf-8") as file:
                summary_rows = [
                    {
                        "policy": row["policy"],
                        "cascade_band_dollars": row["cascade_band_dollars"],
                    }
                    for row in csv.DictReader(file)
                ]
            self.assertEqual(summary_rows, expected["policy_summary_rows"])

            with frontier_path.open(newline="", encoding="utf-8") as file:
                frontier_rows = list(csv.DictReader(file))
            self.assertEqual(len(frontier_rows), 1)
            self.assertEqual(frontier_rows[0]["policy"], "cascade_surrogate_rollout")
            self.assertEqual(frontier_rows[0]["cascade_band_dollars"], "0.00")

    def test_explicit_zero_seed_count_is_rejected(self):
        command = [
            sys.executable,
            "scripts/run_freightbidbench.py",
            "--preset",
            "smoke",
            "--seed-count",
            "0",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--seed-count must be positive", completed.stderr)

    def test_explicit_zero_label_limit_is_rejected(self):
        command = [
            sys.executable,
            "scripts/run_freightbidbench.py",
            "--preset",
            "smoke",
            "--label-limit",
            "0",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--label-limit must be positive", completed.stderr)


if __name__ == "__main__":
    unittest.main()
