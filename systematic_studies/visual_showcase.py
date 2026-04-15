#!/usr/bin/env python3
"""
Sequential MuJoCo passive-viewer scenes for live demos (double pendulum, two-link arm, trunk+wrist).

Headless sweeps stay separate; this script is for on-screen motion only.
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Callable

import mujoco
import mujoco.viewer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def run_viewer_scene(
    xml_path: Path,
    label: str,
    seconds: float,
    realtime: bool,
    setup: Callable[[mujoco.MjModel, mujoco.MjData], None],
    apply_ctrl: Callable[[mujoco.MjModel, mujoco.MjData, float], None],
    headless: bool,
) -> None:
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    setup(model, data)
    mujoco.mj_forward(model, data)

    if headless:
        for _ in range(max(1, int(0.2 / model.opt.timestep))):
            apply_ctrl(model, data, 0.0)
            mujoco.mj_step(model, data)
        return

    print(f"\n--- {label} ---\nClose the viewer window to continue to the next scene.\n")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running():
            t_sim = time.time() - start
            if seconds > 0 and t_sim >= seconds:
                break
            apply_ctrl(model, data, t_sim)
            mujoco.mj_step(model, data)
            viewer.sync()
            if realtime:
                time.sleep(model.opt.timestep)


def scene_pendulum_setup(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 2:
        data.qpos[0] = 0.55
        data.qpos[1] = -0.25
    if model.nv >= 2:
        data.qvel[0] = 0.4
        data.qvel[1] = 0.0


def scene_pendulum_ctrl(model: mujoco.MjModel, data: mujoco.MjData, _t: float) -> None:
    pass


def scene_two_link_setup(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 2:
        data.qpos[0] = 8.0
        data.qpos[1] = 50.0
    if model.nv >= 2:
        data.qvel[:] = 0.0
    if model.nu >= 2:
        data.ctrl[:] = 0.0


def scene_two_link_ctrl(model: mujoco.MjModel, data: mujoco.MjData, _t: float) -> None:
    if model.nu >= 2:
        data.ctrl[:] = 0.0


def scene_trunk_setup(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 4:
        data.qpos[0] = 0.0
        data.qpos[1] = -12.0
        data.qpos[2] = 40.0
        data.qpos[3] = 0.0
    if model.nv >= 4:
        data.qvel[:] = 0.0


def scene_trunk_ctrl(model: mujoco.MjModel, data: mujoco.MjData, t: float) -> None:
    if model.nu >= 4:
        data.ctrl[0] = 5.0 * math.sin(2.0 * math.pi * 0.35 * t)
        data.ctrl[1] = 7.0 * math.sin(2.0 * math.pi * 0.55 * t)
        data.ctrl[2] = 5.0 * math.sin(2.0 * math.pi * 0.55 * t + 0.35)
        data.ctrl[3] = 0.0


SCENES: dict[str, tuple[Path, str, Callable, Callable]] = {
    "pendulum": (
        ROOT / "example_double_pendulum" / "free_swing.xml",
        "Double pendulum (free swing)",
        scene_pendulum_setup,
        scene_pendulum_ctrl,
    ),
    "two_link": (
        ROOT / "example_two_link" / "two_link_arm.xml",
        "Two-link arm (passive, gravity)",
        scene_two_link_setup,
        scene_two_link_ctrl,
    ),
    "trunk": (
        ROOT / "systematic_studies" / "models" / "trunk_arm_wrist.xml",
        "Trunk yaw + arm + wrist (gentle scripted torques)",
        scene_trunk_setup,
        scene_trunk_ctrl,
    ),
}


def main() -> None:
    p = argparse.ArgumentParser(description="Sequential MuJoCo visual showcase.")
    p.add_argument(
        "--scene",
        choices=["all", *sorted(SCENES.keys())],
        default="all",
        help="Which scene to run, or all in order.",
    )
    p.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="Max seconds per scene (0 = until viewer closed).",
    )
    p.add_argument(
        "--no-realtime",
        action="store_true",
        help="Step as fast as possible (usually too fast to present).",
    )
    p.add_argument("--headless", action="store_true", help="Compile each model; no GUI.")
    args = p.parse_args()

    order = list(SCENES.keys()) if args.scene == "all" else [args.scene]
    realtime = not args.no_realtime

    for key in order:
        path, title, setup, ctrl = SCENES[key]
        if not path.is_file():
            print(f"Skip missing model: {path}", file=sys.stderr)
            continue
        run_viewer_scene(path, title, args.seconds, realtime, setup, ctrl, args.headless)

    if not args.headless and args.scene == "all":
        print(
            "\nOptional: interactive muscle double pendulum:\n"
            "  ./run.sh example_double_pendulum/muscle_control.py\n",
        )


if __name__ == "__main__":
    main()
