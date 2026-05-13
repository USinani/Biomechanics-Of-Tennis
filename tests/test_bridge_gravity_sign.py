import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


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


class TestBridgeGravitySign(unittest.TestCase):
    def test_default_compute_forward_dynamics_unchanged(self) -> None:
        sys.path.insert(0, str(REPO_ROOT))
        from example_two_link.matlab_v2_dynamics import compute_forward_dynamics
        from example_two_link.matlab_v2_params import default_matlab_v2_params

        params = default_matlab_v2_params()
        q = np.array([0.1, -0.2], dtype=float)
        qd = np.array([0.3, 0.0], dtype=float)
        tau = np.array([0.0, 0.0], dtype=float)

        qdd_implicit_default = compute_forward_dynamics(q, qd, tau, params)
        qdd_explicit_default = compute_forward_dynamics(q, qd, tau, params, gravity_sign="default")
        self.assertTrue(np.allclose(qdd_implicit_default, qdd_explicit_default, rtol=0.0, atol=0.0))

    def test_opt_in_mujoco_gravity_sign_flips_static_qdd(self) -> None:
        sys.path.insert(0, str(REPO_ROOT))
        from example_two_link.matlab_v2_dynamics import compute_forward_dynamics
        from example_two_link.matlab_v2_params import default_matlab_v2_params

        params = default_matlab_v2_params()
        q = np.array([0.0, 0.0], dtype=float)
        qd = np.array([0.0, 0.0], dtype=float)
        tau = np.array([0.0, 0.0], dtype=float)

        qdd_default = compute_forward_dynamics(q, qd, tau, params, gravity_sign="default")
        qdd_mujoco = compute_forward_dynamics(q, qd, tau, params, gravity_sign="mujoco")

        # With tau=0 and qdot=0, only gravity changes sign; expect exact negation.
        self.assertTrue(np.allclose(qdd_mujoco, -qdd_default, rtol=1e-12, atol=1e-12))

    def test_invalid_gravity_mode_rejected(self) -> None:
        sys.path.insert(0, str(REPO_ROOT))
        from example_two_link.matlab_v2_dynamics import compute_forward_dynamics
        from example_two_link.matlab_v2_params import default_matlab_v2_params

        params = default_matlab_v2_params()
        with self.assertRaises(ValueError):
            compute_forward_dynamics([0.0, 0.0], [0.0, 0.0], [0.0, 0.0], params, gravity_sign="nope")

    def test_benchmark_summary_records_bridge_gravity_sign(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_csv = Path(td) / "ts.csv"
            out_json = Path(td) / "summary.json"
            res = _run_benchmark(
                [
                    "--xml",
                    str(XML),
                    "--steps",
                    "2",
                    "--bridge-gravity-sign",
                    "mujoco",
                    "--out-csv",
                    str(out_csv),
                    "--out-json",
                    str(out_json),
                ]
            )
            self.assertEqual(res.returncode, 0, msg=f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}")
            summary = json.loads(out_json.read_text())
            self.assertEqual(summary.get("bridge_gravity_sign"), "mujoco")


if __name__ == "__main__":
    unittest.main()

