import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_sections_1_to_3.py"
SPEC = importlib.util.spec_from_file_location("sections_1_to_3", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SectionsOneToThreeTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "topology_npus": 64,
            "maximum_jobs": 16,
            "gpus_per_job": 4,
            "job_counts": [1, 2, 4, 8, 16],
            "section_1_iterations": 1,
            "sections_2_and_3_iterations": 3,
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

    def test_section_three_includes_matched_single_job_baseline(self):
        scenarios = MODULE.build_scenarios(self.config, {3})
        self.assertEqual(
            [scenario["job_count"] for scenario in scenarios],
            [1, 2, 4, 8, 16],
        )
        self.assertEqual(scenarios[0]["section"], 2)

    def test_all_sections_do_not_duplicate_single_job_baseline(self):
        scenarios = MODULE.build_scenarios(self.config, {1, 2, 3})
        self.assertEqual(
            [scenario["name"] for scenario in scenarios],
            [
                "section1_one_iteration",
                "section2_single_job_baseline",
                "section3_02_jobs",
                "section3_04_jobs",
                "section3_08_jobs",
                "section3_16_jobs",
            ],
        )

    def test_percentile_and_fairness_helpers(self):
        self.assertEqual(MODULE.nearest_rank_percentile([1, 2, 3, 4], 0.95), 4)
        self.assertAlmostEqual(MODULE.jain_fairness([1, 1, 1]), 1.0)
        self.assertLess(MODULE.jain_fairness([1, 1, 3]), 1.0)

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


if __name__ == "__main__":
    unittest.main()
