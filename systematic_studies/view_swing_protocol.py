#!/usr/bin/env python3
"""
Visual-only replay of the same open-loop torque law as `swing_benchmark_mujoco_vs_bridge.py`.

Use the headless benchmark for CSV/JSON metrics; use this script to show the MuJoCo motion.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from systematic_studies.swing_torque_schedule import swing_torques  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="View two-link swing with benchmark torque schedule.")
    p.add_argument(
        "--xml",
        type=Path,
        default=ROOT / "example_two_link" / "two_link_arm.xml",
    )
    p.add_argument("--q1-deg", type=float, default=5.0)
    p.add_argument("--q2-deg", type=float, default=55.0)
    p.add_argument("--qd1", type=float, default=0.0)
    p.add_argument("--qd2", type=float, default=0.0)
    p.add_argument(
        "--tau-amp",
        type=float,
        default=0.0,
        help="Nm sine amplitude (same law as swing_benchmark). Default 0 = passive gravity (stable). Try ~1.0 for a gentle driven swing.",
    )
    p.add_argument("--tau-f-hz", type=float, default=0.8)
    p.add_argument("--tau-phase-deg", type=float, default=30.0)
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="0 = run until viewer closed.",
    )
    p.add_argument("--no-realtime", action="store_true")
    p.add_argument("--headless", action="store_true")
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    phase_rad = math.radians(args.tau_phase_deg)

    mujoco.mj_resetData(model, data)
    if model.nq >= 2:
        data.qpos[0] = args.q1_deg
        data.qpos[1] = args.q2_deg
    if model.nv >= 2:
        data.qvel[0] = args.qd1
        data.qvel[1] = args.qd2
    mujoco.mj_forward(model, data)

    dt = float(model.opt.timestep)

    if args.headless:
        t_phys = 0.0
        for _ in range(max(1, int(0.3 / dt))):
            tau0, tau1 = swing_torques(t_phys, args.tau_amp, args.tau_f_hz, phase_rad)
            if model.nu >= 2:
                data.ctrl[0] = tau0
                data.ctrl[1] = tau1
            mujoco.mj_step(model, data)
            t_phys += dt
        return

    realtime = not args.no_realtime
    print(
        "MuJoCo swing (torque schedule matches swing_benchmark_mujoco_vs_bridge.py).\n"
        "Torques use simulation time (stable with --no-realtime).\n"
        f"tau_amp={args.tau_amp} (0 = passive gravity).\n"
        "Close the window to exit.\n"
    )
    with mujoco.viewer.launch_passive(model, data) as viewer:
        mujoco.mjv_defaultFreeCamera(model, viewer.cam)
        viewer.sync()

        t_phys = 0.0
        start = time.time()
        while viewer.is_running():
            if args.seconds > 0 and t_phys >= args.seconds:
                break
            tau0, tau1 = swing_torques(t_phys, args.tau_amp, args.tau_f_hz, phase_rad)
            if model.nu >= 2:
                data.ctrl[0] = tau0
                data.ctrl[1] = tau1
            mujoco.mj_step(model, data)
            t_phys += dt

            if not (
                math.isfinite(float(data.qpos[0]))
                and math.isfinite(float(data.qpos[1]))
                and math.isfinite(float(data.qvel[0]))
                and math.isfinite(float(data.qvel[1]))
            ):
                print(
                    "Simulation became non-finite; reset with smaller --tau-amp or passive (0).",
                    file=sys.stderr,
                )
                mujoco.mj_resetData(model, data)
                if model.nq >= 2:
                    data.qpos[0] = args.q1_deg
                    data.qpos[1] = args.q2_deg
                if model.nv >= 2:
                    data.qvel[0] = args.qd1
                    data.qvel[1] = args.qd2
                t_phys = 0.0
                mujoco.mj_forward(model, data)

            viewer.sync()
            if realtime:
                time.sleep(dt)
            # Wall-clock safety cap if stepping without realtime (avoid infinite spin)
            if not realtime and (time.time() - start) > 120.0:
                break


if __name__ == "__main__":
    main()
