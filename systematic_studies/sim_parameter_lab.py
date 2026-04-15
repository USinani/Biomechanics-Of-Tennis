#!/usr/bin/env python3
"""
Interactive lab: change key simulation parameters from the terminal while the MuJoCo passive viewer runs.

Presets wrap curated MJCF (double pendulum with slide anchor, two-link arm, trunk+arm+wrist). The viewer
can show perturb arrows; use the standard MuJoCo viewer interaction mode to select and drag bodies where
the model allows it.
"""

from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import mujoco
import mujoco.viewer

ROOT = Path(__file__).resolve().parent.parent
LAB_XML = Path(__file__).resolve().parent / "models" / "double_pendulum_lab.xml"
TWO_LINK_XML = ROOT / "example_two_link" / "two_link_arm.xml"
TRUNK_XML = Path(__file__).resolve().parent / "models" / "trunk_arm_wrist.xml"


def clamp_joint(model: mujoco.MjModel, data: mujoco.MjData, joint_name: str) -> None:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if jid < 0:
        return
    if not model.jnt_limited[jid]:
        return
    adr = int(model.jnt_qposadr[jid])
    lo, hi = model.jnt_range[jid]
    data.qpos[adr] = min(max(float(data.qpos[adr]), float(lo)), float(hi))


def apply_gravity_scale(model: mujoco.MjModel, scale: float) -> None:
    g0 = -9.81
    model.opt.gravity[2] = g0 * scale


def reset_pendulum(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 3:
        data.qpos[0] = 1.5
        data.qpos[1] = 0.55
        data.qpos[2] = -0.25
    if model.nv >= 3:
        data.qvel[0] = 0.0
        data.qvel[1] = 0.4
        data.qvel[2] = 0.0
    for jn in ("anchor_height", "hinge1", "hinge2"):
        clamp_joint(model, data, jn)
    mujoco.mj_forward(model, data)


def reset_two_link(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 2:
        data.qpos[0] = 8.0
        data.qpos[1] = 50.0
    if model.nv >= 2:
        data.qvel[:] = 0.0
    if model.nu >= 2:
        data.ctrl[:] = 0.0
    for jn in ("shoulder_pitch", "elbow_pitch"):
        clamp_joint(model, data, jn)
    mujoco.mj_forward(model, data)


def reset_trunk(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    mujoco.mj_resetData(model, data)
    if model.nq >= 4:
        data.qpos[0] = 0.0
        data.qpos[1] = 15.0
        data.qpos[2] = 90.0
        data.qpos[3] = 0.0
    if model.nv >= 4:
        data.qvel[:] = 0.0
    if model.nu >= 4:
        data.ctrl[:] = 0.0
    for jn in ("trunk_yaw", "shoulder_pitch", "elbow_pitch", "wrist_ps"):
        clamp_joint(model, data, jn)
    mujoco.mj_forward(model, data)


def print_state_pendulum(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    if model.nq < 3:
        return
    z = float(data.qpos[0])
    h1 = float(data.qpos[1])
    h2 = float(data.qpos[2])
    print(
        f"anchor_z={z:.3f} m | hinge1={h1:.3f} rad ({h1 * 180 / 3.14159265:.1f} deg) | "
        f"hinge2={h2:.3f} rad | g_scale={-float(model.opt.gravity[2]) / 9.81:.3f}"
    )


def print_state_two_link(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    if model.nq < 2:
        return
    print(
        f"shoulder={float(data.qpos[0]):.2f} deg | elbow={float(data.qpos[1]):.2f} deg | "
        f"g_scale={-float(model.opt.gravity[2]) / 9.81:.3f}"
    )


def print_state_trunk(model: mujoco.MjModel, data: mujoco.MjData) -> None:
    if model.nq < 4:
        return
    print(
        f"trunk={float(data.qpos[0]):.2f} | sh={float(data.qpos[1]):.2f} | "
        f"elbow={float(data.qpos[2]):.2f} | wrist={float(data.qpos[3]):.2f} (deg) | "
        f"g_scale={-float(model.opt.gravity[2]) / 9.81:.3f}"
    )


def print_help(preset: str) -> None:
    lines = [
        "Commands (type a key + Enter in this terminal):",
        "  p     print state",
        "  r     reset to preset initial pose",
        "  0     zero all generalized velocities",
        "  g / G multiply / divide gravity magnitude by 1.05",
        "  q     quit simulation loop (close viewer window to exit fully)",
        "",
    ]
    if preset == "pendulum":
        lines += [
            "Double pendulum + slide anchor:",
            "  w / s     anchor height  + / -  (meters, step from --step-anchor)",
            "  W / S     anchor  large step (2x)",
            "  a / d     hinge1 angle + / - (rad, --step-angle-rad)",
            "  z / x     hinge2 angle + / - (rad)",
        ]
    elif preset == "two_link":
        lines += [
            "Two-link arm (qpos in degrees per MJCF):",
            "  w / s     shoulder + / - (--step-angle-deg)",
            "  a / d     elbow + / -",
        ]
    else:
        lines += [
            "Trunk + arm + wrist (degrees):",
            "  t / T     trunk yaw + / -",
            "  s / S     shoulder + / -",
            "  e / E     elbow + / -",
            "  n / N     wrist pron/sup + / -",
        ]
    print("\n".join(lines))


def stdin_reader(cmd_q: queue.Queue[str], stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            line = sys.stdin.readline()
        except EOFError:
            break
        if line is None:
            break
        s = line.strip()
        if s:
            cmd_q.put(s)
    stop.set()


def handle_command(
    preset: str,
    c: str,
    model: mujoco.MjModel,
    data: mujoco.MjData,
    step_anchor: float,
    step_rad: float,
    step_deg: float,
    reset_fn: Callable[[mujoco.MjModel, mujoco.MjData], None],
    gravity_scale_holder: list[float],
) -> bool:
    """Returns False if user requested quit."""
    g = gravity_scale_holder

    def bump_gravity(factor: float) -> None:
        g[0] = min(max(g[0] * factor, 0.05), 3.0)
        apply_gravity_scale(model, g[0])

    if c == "q":
        return False
    if c == "p":
        if preset == "pendulum":
            print_state_pendulum(model, data)
        elif preset == "two_link":
            print_state_two_link(model, data)
        else:
            print_state_trunk(model, data)
        return True
    if c == "r":
        reset_fn(model, data)
        apply_gravity_scale(model, g[0])
        print("reset")
        return True
    if c == "0":
        data.qvel[:] = 0.0
        print("qvel zeroed")
        return True
    if c == "g":
        bump_gravity(1.05)
        print(f"gravity scale={g[0]:.3f}")
        return True
    if c == "G":
        bump_gravity(1.0 / 1.05)
        print(f"gravity scale={g[0]:.3f}")
        return True
    if c == "h" or c == "?":
        print_help(preset)
        return True

    if preset == "pendulum":
        da = step_rad
        dm = step_anchor
        if c == "W":
            dm *= 2.0
            data.qpos[0] += dm
        elif c == "S":
            dm *= 2.0
            data.qpos[0] -= dm
        elif c == "w":
            data.qpos[0] += dm
        elif c == "s":
            data.qpos[0] -= dm
        elif c == "a":
            data.qpos[1] += da
        elif c == "d":
            data.qpos[1] -= da
        elif c == "z":
            data.qpos[2] += da
        elif c == "x":
            data.qpos[2] -= da
        else:
            print(f"unknown key: {c!r} (h for help)")
            return True
        clamp_joint(model, data, "anchor_height")
        mujoco.mj_forward(model, data)
        print_state_pendulum(model, data)
        return True

    if preset == "two_link":
        dd = step_deg
        if c == "w":
            data.qpos[0] += dd
        elif c == "s":
            data.qpos[0] -= dd
        elif c == "a":
            data.qpos[1] += dd
        elif c == "d":
            data.qpos[1] -= dd
        else:
            print(f"unknown key: {c!r} (h for help)")
            return True
        clamp_joint(model, data, "shoulder_pitch")
        clamp_joint(model, data, "elbow_pitch")
        mujoco.mj_forward(model, data)
        print_state_two_link(model, data)
        return True

    dd = step_deg
    if c == "t":
        data.qpos[0] += dd
    elif c == "T":
        data.qpos[0] -= dd
    elif c == "s":
        data.qpos[1] += dd
    elif c == "S":
        data.qpos[1] -= dd
    elif c == "e":
        data.qpos[2] += dd
    elif c == "E":
        data.qpos[2] -= dd
    elif c == "n":
        data.qpos[3] += dd
    elif c == "N":
        data.qpos[3] -= dd
    else:
        print(f"unknown key: {c!r} (h for help)")
        return True
    for jn in ("trunk_yaw", "shoulder_pitch", "elbow_pitch", "wrist_ps"):
        clamp_joint(model, data, jn)
    mujoco.mj_forward(model, data)
    print_state_trunk(model, data)
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Terminal-driven parameter lab with MuJoCo passive viewer.")
    p.add_argument(
        "--preset",
        choices=("pendulum", "two_link", "trunk"),
        default="pendulum",
        help="Which MJCF and key map to use.",
    )
    p.add_argument(
        "--xml",
        type=Path,
        default=None,
        help="Override MJCF path (advanced; key map still follows --preset).",
    )
    p.add_argument(
        "--no-realtime",
        action="store_true",
        help="Do not sleep between steps (run as fast as possible). Default is wall-clock friendly.",
    )
    p.add_argument("--headless", action="store_true", help="Load model and step once (smoke test).")
    p.add_argument("--step-anchor", type=float, default=0.05, help="Pendulum: anchor slide step (m).")
    p.add_argument("--step-angle-rad", type=float, default=0.08, help="Pendulum: hinge step (rad).")
    p.add_argument("--step-angle-deg", type=float, default=4.0, help="Arm presets: joint step (deg).")
    p.add_argument(
        "--no-pert-vis",
        action="store_true",
        help="Do not enable perturbation visualization flags in the viewer.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    xml_path: Path
    if args.xml is not None:
        xml_path = args.xml.expanduser().resolve()
    elif args.preset == "pendulum":
        xml_path = LAB_XML
    elif args.preset == "two_link":
        xml_path = TWO_LINK_XML
    else:
        xml_path = TRUNK_XML

    if not xml_path.is_file():
        print(f"MJCF not found: {xml_path}", file=sys.stderr)
        sys.exit(1)

    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    reset_fn: Callable[[mujoco.MjModel, mujoco.MjData], None]
    if args.preset == "pendulum":
        reset_fn = reset_pendulum
    elif args.preset == "two_link":
        reset_fn = reset_two_link
    else:
        reset_fn = reset_trunk

    gravity_scale: list[float] = [1.0]
    apply_gravity_scale(model, gravity_scale[0])
    reset_fn(model, data)

    if args.headless:
        mujoco.mj_step(model, data)
        return

    cmd_q: queue.Queue[str] = queue.Queue()
    stop = threading.Event()
    reader = threading.Thread(target=stdin_reader, args=(cmd_q, stop), daemon=True)
    reader.start()

    print(f"sim_parameter_lab  preset={args.preset}  xml={xml_path}")
    print_help(args.preset)

    pert_flag = int(mujoco.mjtVisFlag.mjVIS_PERTOBJ)
    pert_force = int(mujoco.mjtVisFlag.mjVIS_PERTFORCE)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        mujoco.mjv_defaultFreeCamera(model, viewer.cam)
        if not args.no_pert_vis:
            viewer.opt.flags[pert_flag] = 1
            viewer.opt.flags[pert_force] = 1

        while viewer.is_running() and not stop.is_set():
            while True:
                try:
                    line = cmd_q.get_nowait()
                except queue.Empty:
                    break
                token = line[0] if line else ""
                if not handle_command(
                    args.preset,
                    token,
                    model,
                    data,
                    args.step_anchor,
                    args.step_angle_rad,
                    args.step_angle_deg,
                    reset_fn,
                    gravity_scale,
                ):
                    stop.set()
                    break

            if model.nu > 0:
                data.ctrl[:] = 0.0
            mujoco.mj_step(model, data)
            viewer.sync()
            if not args.no_realtime:
                time.sleep(model.opt.timestep)

    stop.set()


if __name__ == "__main__":
    main()
