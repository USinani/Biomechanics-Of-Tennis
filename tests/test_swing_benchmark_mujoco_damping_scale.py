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


class TestSwingBenchmarkMuJoCoDampingScale(unittest.TestCase):
    def test_default_scale_preserves_xml_damping(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-damping-scale",
                    "1.0",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_damping_scale"], 1.0)
            orig = summary["mujoco_dof_damping_original"]
            eff = summary["mujoco_dof_damping_effective"]
            self.assertEqual(orig, eff)
            self.assertTrue(any(float(x) != 0.0 for x in eff), msg="Expected nonzero XML damping for this model.")

    def test_scale_zero_sets_effective_damping_to_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-damping-scale",
                    "0.0",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_damping_scale"], 0.0)
            eff = summary["mujoco_dof_damping_effective"]
            self.assertTrue(all(float(x) == 0.0 for x in eff))

    def test_negative_scale_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-damping-scale",
                    "-1.0",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertNotEqual(res.returncode, 0)
            # ValueError bubbles up to stderr.
            self.assertIn("mujoco-damping-scale", (res.stderr or "").lower())

    def test_integrator_override_can_coexist_with_damping_scale(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--mujoco-integrator",
                    "rk4",
                    "--mujoco-damping-scale",
                    "0.0",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_integrator_effective"], "rk4")
            self.assertTrue(all(float(x) == 0.0 for x in summary["mujoco_dof_damping_effective"]))


if __name__ == "__main__":
    unittest.main()

