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


class TestSwingBenchmarkMuJoCoIntegratorOverride(unittest.TestCase):
    def test_default_xml_integrator_reports_implicitfast(self) -> None:
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
                    "xml",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertIn("mujoco_integrator_requested", summary)
            self.assertIn("mujoco_integrator_effective", summary)
            self.assertEqual(summary["mujoco_integrator_requested"], "xml")
            # The canonical two-link XML specifies implicitfast.
            self.assertEqual(summary["mujoco_integrator_effective"], "implicitfast")

    def test_rk4_override_reports_rk4(self) -> None:
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
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_integrator_requested"], "rk4")
            self.assertEqual(summary["mujoco_integrator_effective"], "rk4")

    def test_invalid_value_rejected_by_argparse(self) -> None:
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
                    "nope",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("invalid choice", (res.stderr or "").lower())

    def test_bridge_integrator_independent_from_mujoco_integrator(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--bridge-integrator",
                    "rk4",
                    "--mujoco-integrator",
                    "xml",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary["mujoco_integrator_effective"], "implicitfast")

