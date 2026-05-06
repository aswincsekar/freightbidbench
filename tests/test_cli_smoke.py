import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FreightBidBenchCliTests(unittest.TestCase):
    def test_tiny_benchmark_run_writes_manifest_and_summaries(self):
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
            summary_path = output_dir / "freightbidbench_policy_summary.csv"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(summary_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["benchmark_version"], "freightbidbench-v0.2")
            self.assertEqual(manifest["label_limit"], 5)
            self.assertEqual(manifest["eval_load_limit"], 10)
            self.assertEqual(manifest["row_counts"]["static_fit"], 1)
            self.assertGreater(manifest["row_counts"]["policy_runs"], 0)


if __name__ == "__main__":
    unittest.main()
