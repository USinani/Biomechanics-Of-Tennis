import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "systematic_studies" / "swing_benchmark_mujoco_vs_bridge.py"
XML = REPO_ROOT / "example_two_link" / "two_link_arm.xml"


def _run_benchmark(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class TestSwingBenchmarkMuJoCoJointLimitsOverride(unittest.TestCase):
    def _assert_joint_limit_provenance(self, summary: dict) -> None:
        self.assertIn("mujoco_joint_limits", summary)
        self.assertIn("mujoco_jnt_limited_original", summary)
        self.assertIn("mujoco_jnt_limited_effective", summary)
        self.assertIn("mujoco_jnt_range", summary)
        jr = summary["mujoco_jnt_range"]
        self.assertEqual(len(jr), 2)
        for pair in jr:
            self.assertEqual(len(pair), 2)
            self.assertIsInstance(pair[0], (int, float))
            self.assertIsInstance(pair[1], (int, float))

    def test_default_xml_preserves_original_limit_flags(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_joint_limits"], "xml")
            self._assert_joint_limit_provenance(summary)
            orig = summary["mujoco_jnt_limited_original"]
            eff = summary["mujoco_jnt_limited_effective"]
            self.assertEqual(orig, eff)
            self.assertTrue(all(int(x) != 0 for x in orig), msg="Expected XML limits active for two-link arm.")

    def test_explicit_xml_preserves_original_limit_flags(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-joint-limits",
                    "xml",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_joint_limits"], "xml")
            self._assert_joint_limit_provenance(summary)
            self.assertEqual(summary["mujoco_jnt_limited_original"], summary["mujoco_jnt_limited_effective"])

    def test_disabled_sets_effective_limit_flags_to_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-joint-limits",
                    "disabled",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_joint_limits"], "disabled")
            self._assert_joint_limit_provenance(summary)
            self.assertTrue(any(int(x) != 0 for x in summary["mujoco_jnt_limited_original"]))
            self.assertEqual(summary["mujoco_jnt_limited_effective"], [0, 0])

    def test_invalid_mode_rejected_by_argparse(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-joint-limits",
                    "nope",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("invalid choice", (res.stderr or "").lower())


if __name__ == "__main__":
    unittest.main()
