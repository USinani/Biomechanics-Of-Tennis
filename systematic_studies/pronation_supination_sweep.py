#!/usr/bin/env python3
"""Sweep fixed wrist (pronation/supination) offset; measure hand and racket-tip speed proxies."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def site_speed_fd_update(
    data: mujoco.MjData,
    site_id: int,
    x_prev: np.ndarray,
    dt: float,
) -> float:
    x = data.site_xpos[site_id].copy()
    v = float(np.linalg.norm((x - x_prev) / dt))
    x_prev[:] = x
    return v


def run_one(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    wrist_deg: float,
    steps: int,
    tau_amp: float,
    tau_f_hz: float,
    tau_phase_deg: float,
    passive: bool,
    warmup_steps: int,
) -> dict[str, float]:
    mujoco.mj_resetData(model, data)
    if model.nq >= 4:
        data.qpos[0] = 0.0
        data.qpos[1] = -15.0
        data.qpos[2] = 45.0
        data.qpos[3] = wrist_deg
    if model.nv >= 4:
        data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)
    hid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "hand")
    tid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "racket_tip")
    xh = data.site_xpos[hid].copy()
    xt = data.site_xpos[tid].copy()

    phase = math.radians(tau_phase_deg)
    max_hand = 0.0
    max_tip = 0.0

    for k in range(steps):
        t = k * model.opt.timestep
        if passive or model.nu < 4:
            data.ctrl[:] = 0.0
        else:
            tau_s = tau_amp * math.sin(2.0 * math.pi * tau_f_hz * t)
            tau_e = tau_amp * math.sin(2.0 * math.pi * tau_f_hz * t + phase)
            data.ctrl[0] = 0.0
            data.ctrl[1] = tau_s
            data.ctrl[2] = tau_e
            data.ctrl[3] = 0.0
        mujoco.mj_step(model, data)
        if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
            break
        dt = float(model.opt.timestep)
        vh = site_speed_fd_update(data, hid, xh, dt)
        vt = site_speed_fd_update(data, tid, xt, dt)
        if k >= warmup_steps:
            if np.isfinite(vh):
                max_hand = max(max_hand, vh)
            if np.isfinite(vt):
                max_tip = max(max_tip, vt)

    return {
        "wrist_deg": wrist_deg,
        "max_hand_speed_m_s": max_hand,
        "max_racket_tip_speed_m_s": max_tip,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Pronation/supination offset sweep (headless).")
    p.add_argument(
        "--xml",
        type=Path,
        default=ROOT / "systematic_studies" / "models" / "trunk_arm_wrist.xml",
    )
    p.add_argument("--steps", type=int, default=600)
    p.add_argument(
        "--warmup-steps",
        type=int,
        default=40,
        help="Skip max-speed accumulation for this many steps (filters startup spikes).",
    )
    p.add_argument(
        "--wrist-deg",
        type=float,
        nargs="+",
        default=[-60.0, -30.0, 0.0, 30.0, 60.0],
        help="Initial wrist_ps angles (degrees) to sweep.",
    )
    p.add_argument(
        "--tau-amp",
        type=float,
        default=6.0,
        help="Shoulder/elbow sine amplitude (Nm); lower if simulation diverges.",
    )
    p.add_argument("--tau-f-hz", type=float, default=0.7)
    p.add_argument("--tau-phase-deg", type=float, default=25.0)
    p.add_argument(
        "--active-torque",
        action="store_true",
        help="Apply shoulder/elbow sine torques (default is passive / gravity-only for stable sweeps).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "pronation_supination_sweep.csv",
    )
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for w in args.wrist_deg:
        rows.append(
            run_one(
                model,
                data,
                float(w),
                args.steps,
                args.tau_amp,
                args.tau_f_hz,
                args.tau_phase_deg,
                passive=not args.active_torque,
                warmup_steps=args.warmup_steps,
            )
        )

    fieldnames = list(rows[0].keys())
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    best_tip = max(rows, key=lambda r: r["max_racket_tip_speed_m_s"])
    print(f"Wrote {len(rows)} rows to {args.out}")
    print(f"Max racket-tip speed proxy: wrist_deg={best_tip['wrist_deg']}, v={best_tip['max_racket_tip_speed_m_s']:.4f} m/s")


if __name__ == "__main__":
    main()
