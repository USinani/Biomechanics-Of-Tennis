#!/usr/bin/env python3
"""Play MATLAB-bridge driven two-link motion in MuJoCo (no RL dependency)."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

from example_two_link.matlab_v2_dynamics import compute_inverse_dynamics
from example_two_link.matlab_v2_params import default_matlab_v2_params


def load_trajectory_csv(path: Path) -> list[dict[str, float]]:
    out: list[dict[str, float]] = []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append({k: float(v) for k, v in row.items() if v not in ("", None)})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, default=Path("example_two_link/view_matlab_model.xml"))
    parser.add_argument("--trajectory-csv", type=Path, default=None, help="Optional CSV with q1,q2,qd1,qd2.")
    parser.add_argument("--duration", type=float, default=8.0, help="Duration for generated motion.")
    args = parser.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    params = default_matlab_v2_params()

    ctrl_dt = max(1.0 / 60.0, model.opt.timestep)
    t0 = time.time()

    traj = load_trajectory_csv(args.trajectory_csv) if args.trajectory_csv else None
    idx = 0

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            if traj:
                row = traj[idx % len(traj)]
                q = np.array([row.get("q1", 0.0), row.get("q2", 0.0)], dtype=float)
                qd = np.array([row.get("qd1", 0.0), row.get("qd2", 0.0)], dtype=float)
                data.qpos[:2] = q
                data.qvel[:2] = qd
                mujoco.mj_forward(model, data)
                idx += 1
            else:
                t = time.time() - t0
                if t > args.duration:
                    t0 = time.time()
                    t = 0.0
                q = np.array([0.35 * np.sin(1.2 * t), 0.65 + 0.25 * np.sin(1.8 * t + 0.5)], dtype=float)
                qd = np.array([0.42 * np.cos(1.2 * t), 0.45 * np.cos(1.8 * t + 0.5)], dtype=float)
                qdd = np.array([-0.50 * np.sin(1.2 * t), -0.81 * np.sin(1.8 * t + 0.5)], dtype=float)
                tau = compute_inverse_dynamics(q, qd, qdd, params)
                data.qpos[:2] = q
                data.qvel[:2] = qd
                data.ctrl[:2] = tau
                mujoco.mj_step(model, data)

            viewer.sync()
            time.sleep(ctrl_dt)


if __name__ == "__main__":
    main()

