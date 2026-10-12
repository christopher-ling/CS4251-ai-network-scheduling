import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_collective_contention.py"
SPEC = importlib.util.spec_from_file_location("collective_contention", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CollectiveContentionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "topology_npus": 64,
            "maximum_jobs": 16,
            "gpus_per_job": 4,
            "job_counts": [1, 2, 4, 8, 16],
            "iteration_demo_count": 1,
            "measurement_iterations": 3,
        }

    def test_strided_groups_are_disjoint_and_cover_topology(self):
        groups = MODULE.build_groups(16, 4, 64)
        self.assertEqual(groups["1"], [0, 16, 32, 48])
        self.assertEqual(groups["16"], [15, 31, 47, 63])
        ranks = [rank for members in groups.values() for rank in members]
        self.assertEqual(sorted(ranks), list(range(64)))

    def test_group_shape_must_match_topology(self):
        with self.assertRaises(ValueError):
            MODULE.build_groups(8, 4, 64)

    def test_contention_includes_matched_single_job_baseline(self):
        scenarios = MODULE.build_scenarios(self.config, {"contention"})
        self.assertEqual(
            [scenario["job_count"] for scenario in scenarios],
            [1, 2, 4, 8, 16],
        )
        self.assertEqual(scenarios[0]["phase"], "baseline")

    def test_all_scenarios_do_not_duplicate_single_job_baseline(self):
        scenarios = MODULE.build_scenarios(
            self.config, {"iteration", "baseline", "contention"}
        )
        self.assertEqual(
            [scenario["name"] for scenario in scenarios],
            [
                "training_iteration",
                "single_job_baseline",
                "concurrent_02_jobs",
                "concurrent_04_jobs",
                "concurrent_08_jobs",
                "concurrent_16_jobs",
            ],
        )

    def test_percentile_and_fairness_helpers(self):
        self.assertEqual(MODULE.nearest_rank_percentile([1, 2, 3, 4], 0.95), 4)
        self.assertAlmostEqual(MODULE.jain_fairness([1, 1, 1]), 1.0)
        self.assertLess(MODULE.jain_fairness([1, 1, 3]), 1.0)

    def test_trace_preview_explains_the_generated_operation_order(self):
        preview = MODULE.build_trace_preview(
            {"1": [0, 16, 32, 48]}, ["1"], 1, 100, 16777216
        )
        job = preview["jobs"][0]
        self.assertEqual(job["simulated_gpu_ranks"], [0, 16, 32, 48])
        self.assertEqual(
            [item["operation"] for item in job["operations_on_each_rank"]],
            ["compute", "AllReduce", "final compute"],
        )
        self.assertEqual(
            job["operations_on_each_rank"][1]["message_bytes_per_rank"],
            16777216,
        )

    def test_baseline_only_run_can_write_results_without_iteration_demo(self):
        row = {
            "case": "single_job_baseline",
            "iterations": 3,
            "jct_us": 6362.602,
            "compute_total_us": 400,
        }
        summary = {
            "job_count": 1,
            "mean_jct_us": 6362.602,
            "p95_jct_us": 6362.602,
            "mean_slowdown": 1.0,
            "max_slowdown": 1.0,
            "jain_fairness_completion_rate": 1.0,
        }
        config = {
            "topology_npus": 64,
            "gpus_per_job": 4,
            "bandwidth_GBps": 50.0,
            "message_bytes_per_rank": 16777216,
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "README.md"
            MODULE.write_results_markdown(output, config, [summary], [row])
            text = output.read_text()
        self.assertIn("3-iteration single-job baseline", text)
        self.assertNotIn("one-iteration trace completed", text)

    def test_fixed_input_validation_detects_mismatched_topology(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "network_64npu_ring.yml").write_text(
                "topology: [ Ring ]\nnpus_count: [ 16 ]\n"
                "bandwidth: [ 50.0 ]\nlatency: [ 500.0 ]\n"
            )
            (root / "system_ring.json").write_text(json.dumps({
                "all-reduce-implementation": ["ring"],
                "active-chunks-per-dimension": 4,
            }))
            full_config = {
                **self.config,
                "bandwidth_GBps": 50.0,
                "latency_ns": 500.0,
            }
            with self.assertRaises(ValueError):
                MODULE.validate_fixed_inputs(full_config, root)

    def test_fixed_input_validation_supports_example_filenames(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "network.yml").write_text(
                "topology: [ Ring ]\nnpus_count: [ 4 ]\n"
                "bandwidth: [ 50.0 ]\nlatency: [ 500.0 ]\n"
            )
            (root / "system.json").write_text(json.dumps({
                "all-reduce-implementation": ["ring"],
                "active-chunks-per-dimension": 4,
            }))
            config = {
                "topology_npus": 4,
                "bandwidth_GBps": 50.0,
                "latency_ns": 500.0,
                "network_configuration": "network.yml",
                "system_configuration": "system.json",
            }
            MODULE.validate_fixed_inputs(config, root)


if __name__ == "__main__":
    unittest.main()
