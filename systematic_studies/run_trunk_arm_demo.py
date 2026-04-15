#!/usr/bin/env python3
"""Viewer demo: trunk yaw + two-link arm + wrist (pronation/supination)."""

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


def main() -> None:
    p = argparse.ArgumentParser(description="Trunk + arm + wrist MuJoCo viewer demo.")
    p.add_argument(
        "--xml",
        type=Path,
        default=ROOT / "systematic_studies" / "models" / "trunk_arm_wrist.xml",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="0 = run until window closed.",
    )
    p.add_argument("--realtime", action="store_true")
    p.add_argument(
        "--scripted-trunk",
        action="store_true",
        help="Apply small sinusoidal trunk torque; shoulder/elbow passive unless --scripted-arm.",
    )
    p.add_argument(
        "--scripted-arm",
        action="store_true",
        help="Add shoulder/elbow sine torques (with --scripted-trunk or alone).",
    )
    p.add_argument("--headless", action="store_true")
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)

    if args.headless:
        n = int(0.5 / model.opt.timestep) if args.seconds <= 0 else int(args.seconds / model.opt.timestep)
        for _ in range(max(1, n)):
            mujoco.mj_step(model, data)
        return

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running():
            if args.seconds > 0 and time.time() - start >= args.seconds:
                break
            t = time.time() - start
            if model.nu >= 4:
                data.ctrl[:] = 0.0
                if args.scripted_trunk:
                    data.ctrl[0] = 15.0 * math.sin(2.0 * math.pi * 0.4 * t)
                if args.scripted_arm:
                    data.ctrl[1] = 18.0 * math.sin(2.0 * math.pi * 1.0 * t)
                    data.ctrl[2] = 12.0 * math.sin(2.0 * math.pi * 1.0 * t + 0.4)
            mujoco.mj_step(model, data)
            viewer.sync()
            if args.realtime:
                time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()
