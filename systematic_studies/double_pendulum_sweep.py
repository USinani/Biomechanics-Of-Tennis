#!/usr/bin/env python3
"""Sweep initial double-pendulum angles (and optional elbow timing delay); log tip kinematics."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def tip_speed(model: mujoco.MjModel, data: mujoco.MjData, site_name: str = "tip") -> float:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    if sid < 0:
        raise ValueError(f"Site not found: {site_name}")
    jacp = np.zeros((3, model.nv), dtype=np.float64)
    mujoco.mj_jacSite(model, data, jacp, None, sid)
    v = jacp @ data.qvel
    return float(np.linalg.norm(v))


def tip_height(model: mujoco.MjModel, data: mujoco.MjData, site_name: str = "tip") -> float:
    sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site_name)
    return float(data.site_xpos[sid][2])


def run_one(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    q1: float,
    q2: float,
    qd1: float,
    qd2: float,
    steps: int,
    elbow_delay_steps: int,
) -> dict[str, float]:
    mujoco.mj_resetData(model, data)
    if model.nq >= 2:
        data.qpos[0] = q1
        data.qpos[1] = q2
    if model.nv >= 2:
        data.qvel[0] = qd1
        data.qvel[1] = qd2
    mujoco.mj_forward(model, data)

    max_speed = 0.0
    max_z = tip_height(model, data)
    t_peak = 0.0
    dt = model.opt.timestep

    for k in range(steps):
        if k < elbow_delay_steps:
            data.qvel[1] = 0.0
        mujoco.mj_step(model, data)
        sp = tip_speed(model, data)
        z = tip_height(model, data)
        if sp > max_speed:
            max_speed = sp
            t_peak = (k + 1) * dt
        max_z = max(max_z, z)

    return {
        "q1_0": q1,
        "q2_0": q2,
        "qd1_0": qd1,
        "qd2_0": qd2,
        "elbow_delay_steps": float(elbow_delay_steps),
        "t_peak_speed_s": t_peak,
        "max_tip_speed_m_s": max_speed,
        "max_tip_z_m": max_z,
    }


def parse_grid(s: str) -> np.ndarray:
    parts = [float(x) for x in s.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Expected start,stop,count as three comma-separated floats: {s}")
    start, stop, count = parts
    cnt = int(count)
    if cnt < 1:
        raise ValueError("count must be >= 1")
    return np.linspace(start, stop, cnt)


def main() -> None:
    p = argparse.ArgumentParser(description="Double pendulum angle / timing sweep (headless).")
    p.add_argument(
        "--xml",
        type=Path,
        default=ROOT / "example_double_pendulum" / "free_swing.xml",
        help="MJCF path.",
    )
    p.add_argument("--steps", type=int, default=800, help="Simulation steps per run.")
    p.add_argument(
        "--q1-grid",
        type=str,
        default="-0.5,0.5,5",
        help="q1 grid: start,stop,count (radians).",
    )
    p.add_argument(
        "--q2-grid",
        type=str,
        default="-0.3,0.3,4",
        help="q2 grid: start,stop,count (radians).",
    )
    p.add_argument("--qd1", type=float, default=0.0)
    p.add_argument("--qd2", type=float, default=0.0)
    p.add_argument(
        "--elbow-delay-steps",
        type=int,
        nargs="*",
        default=[0, 50],
        help="Hold elbow angular velocity to zero for this many steps (timing knob).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "double_pendulum_sweep.csv",
    )
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)

    q1s = parse_grid(args.q1_grid)
    q2s = parse_grid(args.q2_grid)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "q1_0",
        "q2_0",
        "qd1_0",
        "qd2_0",
        "elbow_delay_steps",
        "t_peak_speed_s",
        "max_tip_speed_m_s",
        "max_tip_z_m",
    ]
    rows: list[dict[str, float]] = []
    for d in args.elbow_delay_steps:
        for q1 in q1s:
            for q2 in q2s:
                rows.append(
                    run_one(model, data, float(q1), float(q2), args.qd1, args.qd2, args.steps, int(d))
                )

    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
