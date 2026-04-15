#!/usr/bin/env python3
"""
Same time window, same open-loop torques: MuJoCo two-link vs MATLAB_v2 Python bridge.

Compares joint angles/velocities and a planar hand-speed proxy. See systematic_studies/README.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from example_two_link.matlab_v2_dynamics import compute_forward_dynamics  # noqa: E402
from example_two_link.matlab_v2_params import (  # noqa: E402
    default_matlab_v2_params,
    params_from_mujoco_xml,
)
from systematic_studies.swing_torque_schedule import swing_torques  # noqa: E402


def xml_uses_degrees(xml_path: Path) -> bool:
    root = ET.parse(str(xml_path)).getroot()
    comp = root.find("compiler")
    if comp is None:
        return False
    ang = (comp.get("angle") or "radian").lower()
    return ang == "degree"


def qvel_mujoco_to_rad_per_s(_xml_path: Path, qvel: np.ndarray) -> np.ndarray:
    """MuJoCo runtime qvel is already in rad/s."""
    return np.array(qvel, dtype=float, copy=True)


def qvel_rad_per_s_to_mujoco_units(_xml_path: Path, qvel_rad_s: np.ndarray) -> np.ndarray:
    """MuJoCo runtime qvel uses rad/s regardless of compiler angle attribute."""
    return np.array(qvel_rad_s, dtype=float, copy=True)


def site_speed_fd_components(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    site_id: int,
    x_prev: np.ndarray,
    dt: float,
) -> tuple[float, float]:
    x = data.site_xpos[site_id].copy()
    v = (x - x_prev) / dt
    speed_3d = float(np.linalg.norm(v))
    speed_xz = float(math.hypot(v[0], v[2]))
    x_prev[:] = x
    return speed_3d, speed_xz


def site_speed_jacobian_components(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    site_id: int,
) -> tuple[float, float]:
    jacp = np.zeros((3, model.nv), dtype=float)
    jacr = np.zeros((3, model.nv), dtype=float)
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    v = jacp @ data.qvel
    speed_3d = float(np.linalg.norm(v))
    speed_xz = float(math.hypot(v[0], v[2]))
    return speed_3d, speed_xz


def count_spikes_from_velocity(vel: np.ndarray, dt: float, threshold: float) -> int:
    if vel.size < 2:
        return 0
    acc = np.diff(vel) / dt
    return int(np.count_nonzero(np.abs(acc) > threshold))


def count_jerk_outliers_from_velocity(vel: np.ndarray, dt: float, threshold: float) -> int:
    if vel.size < 3:
        return 0
    acc = np.diff(vel) / dt
    jerk = np.diff(acc) / dt
    return int(np.count_nonzero(np.abs(jerk) > threshold))


def hand_planar_speed(l1: float, l2: float, th: np.ndarray, thd: np.ndarray) -> float:
    """Hand speed in XZ plane (rad/s * m); th = [th1,th2] relative, same convention as FK below."""
    th1, th2 = th[0], th[1]
    d1, d2 = thd[0], thd[1]
    vx = -l1 * math.sin(th1) * d1 - l2 * math.sin(th1 + th2) * (d1 + d2)
    vz = l1 * math.cos(th1) * d1 + l2 * math.cos(th1 + th2) * (d1 + d2)
    return float(math.hypot(vx, vz))


def integrate_bridge_step(
    q: np.ndarray, qd: np.ndarray, tau: np.ndarray, dt: float, params
) -> tuple[np.ndarray, np.ndarray]:
    qdd = compute_forward_dynamics(q, qd, tau, params)
    qd_new = qd + qdd * dt
    q_new = q + qd_new * dt
    return q_new, qd_new


def main() -> None:
    p = argparse.ArgumentParser(description="Swing benchmark: MuJoCo vs MATLAB_v2 Python bridge.")
    p.add_argument(
        "--xml",
        type=Path,
        default=ROOT / "example_two_link" / "two_link_arm.xml",
    )
    p.add_argument("--steps", type=int, default=500)
    p.add_argument(
        "--param-source",
        choices=("matlab_default", "from_xml"),
        default="from_xml",
    )
    p.add_argument("--q1-deg", type=float, default=5.0, help="Initial shoulder angle in degrees (converted to rad for MuJoCo state).")
    p.add_argument("--q2-deg", type=float, default=55.0, help="Initial elbow angle in degrees (converted to rad for MuJoCo state).")
    p.add_argument("--qd1", type=float, default=0.0, help="Initial shoulder velocity (canonical rad/s).")
    p.add_argument("--qd2", type=float, default=0.0)
    p.add_argument(
        "--tau-amp",
        type=float,
        default=0.0,
        help="Sine torque amplitude (Nm). Default 0 = passive (gravity only); increase for driven swing.",
    )
    p.add_argument("--tau-f-hz", type=float, default=0.8, help="Torque oscillation frequency (Hz).")
    p.add_argument("--tau-phase-deg", type=float, default=30.0, help="Phase offset on elbow torque (deg).")
    p.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "swing_benchmark_timeseries.csv",
    )
    p.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "swing_benchmark_summary.json",
    )
    p.add_argument(
        "--expected-dt",
        type=float,
        default=None,
        help="Optional expected simulation timestep (s); fails fast on mismatch.",
    )
    p.add_argument(
        "--expected-duration",
        type=float,
        default=None,
        help="Optional expected total duration (s); fails fast on mismatch.",
    )
    p.add_argument("--velocity-spike-threshold-rad-s2", type=float, default=500.0)
    p.add_argument("--jerk-threshold-rad-s3", type=float, default=5.0e4)
    p.add_argument("--rmse-q-threshold-rad", type=float, default=0.75)
    p.add_argument("--rmse-qd-threshold-rad-s", type=float, default=10.0)
    args = p.parse_args()

    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    dt = float(model.opt.timestep)
    duration_s = (args.steps - 1) * dt if args.steps > 0 else 0.0
    if args.expected_dt is not None and not math.isclose(dt, args.expected_dt, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"Timestep mismatch: model dt={dt:.12g} != expected {args.expected_dt:.12g}")
    if args.expected_duration is not None and not math.isclose(duration_s, args.expected_duration, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(
            f"Duration mismatch: benchmark duration={duration_s:.12g} != expected {args.expected_duration:.12g}"
        )

    params = (
        default_matlab_v2_params()
        if args.param_source == "matlab_default"
        else params_from_mujoco_xml(args.xml)
    )
    l1, l2 = params.l1, params.l2

    hand_sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "hand")
    if hand_sid < 0:
        raise ValueError("Model must define site 'hand'.")

    deg_model = xml_uses_degrees(args.xml)

    mujoco.mj_resetData(model, data)
    q_init_rad = np.deg2rad([args.q1_deg, args.q2_deg], dtype=float)
    data.qpos[0] = q_init_rad[0]
    data.qpos[1] = q_init_rad[1]
    qd_init_model_units = qvel_rad_per_s_to_mujoco_units(args.xml, np.array([args.qd1, args.qd2], dtype=float))
    data.qvel[0] = qd_init_model_units[0]
    data.qvel[1] = qd_init_model_units[1]
    mujoco.mj_forward(model, data)
    x_hand_prev = data.site_xpos[hand_sid].copy()

    q_b = np.deg2rad([args.q1_deg, args.q2_deg], dtype=float)
    qd_b = np.array([args.qd1, args.qd2], dtype=float)

    err_q: list[float] = []
    err_qd: list[float] = []
    err_vhand: list[float] = []
    tau_clip_deltas: list[float] = []

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    phase = math.radians(args.tau_phase_deg)
    rows: list[dict[str, float]] = []
    ctrl_range = model.actuator_ctrlrange[:2, :] if model.nu >= 2 else None

    for k in range(args.steps):
        t = k * dt
        tau0, tau1 = swing_torques(t, args.tau_amp, args.tau_f_hz, phase)
        tau = np.array([tau0, tau1], dtype=float)
        clipped_tau = tau.copy()
        if ctrl_range is not None:
            clipped_tau = np.clip(tau, ctrl_range[:, 0], ctrl_range[:, 1])
        tau_clip_deltas.append(float(np.max(np.abs(clipped_tau - tau))))

        if model.nu >= 2:
            data.ctrl[0] = tau0
            data.ctrl[1] = tau1
        mujoco.mj_step(model, data)
        if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
            break

        q_b, qd_b = integrate_bridge_step(q_b, qd_b, tau, dt, params)

        mj_q_rad = np.array([data.qpos[0], data.qpos[1]], dtype=float)
        mj_q_deg = np.rad2deg(mj_q_rad) if deg_model else mj_q_rad.copy()
        mj_qd_raw = np.array([data.qvel[0], data.qvel[1]], dtype=float)
        mj_qd_rad_s = qvel_mujoco_to_rad_per_s(args.xml, mj_qd_raw)

        err_q.append(float(np.linalg.norm(mj_q_rad - q_b)))
        err_qd.append(float(np.linalg.norm(mj_qd_rad_s - qd_b)))

        v_mj_3d, v_mj_xz_fd = site_speed_fd_components(model, data, hand_sid, x_hand_prev, dt)
        v_mj_3d_jac, v_mj_xz_jac = site_speed_jacobian_components(model, data, hand_sid)
        v_br = hand_planar_speed(l1, l2, q_b, qd_b)
        err_vhand.append(abs(v_mj_xz_fd - v_br))

        rows.append(
            {
                "step": float(k),
                "time_s": t,
                "dt_s": dt,
                "duration_s": duration_s,
                "mj_q1_deg": mj_q_deg[0],
                "mj_q2_deg": mj_q_deg[1],
                "mujoco_q1_rad": mj_q_rad[0],
                "mujoco_q2_rad": mj_q_rad[1],
                "mj_qd1_raw": mj_qd_raw[0],
                "mj_qd2_raw": mj_qd_raw[1],
                "mj_qd1_rad_s": mj_qd_rad_s[0],
                "mj_qd2_rad_s": mj_qd_rad_s[1],
                "mujoco_qdot1_rad_s": mj_qd_rad_s[0],
                "mujoco_qdot2_rad_s": mj_qd_rad_s[1],
                "bridge_q1_rad": q_b[0],
                "bridge_q2_rad": q_b[1],
                "bridge_qd1": qd_b[0],
                "bridge_qd2": qd_b[1],
                "bridge_qdot1_rad_s": qd_b[0],
                "bridge_qdot2_rad_s": qd_b[1],
                "tau0": tau0,
                "tau1": tau1,
                "tau1_Nm": tau0,
                "tau2_Nm": tau1,
                "tau1_applied_Nm": clipped_tau[0],
                "tau2_applied_Nm": clipped_tau[1],
                "mj_hand_speed_norm_fd": v_mj_3d,
                "mujoco_ee_speed_fd_3d_m_s": v_mj_3d,
                "mujoco_ee_speed_fd_xz_m_s": v_mj_xz_fd,
                "mujoco_ee_speed_jac_3d_m_s": v_mj_3d_jac,
                "mujoco_ee_speed_jac_xz_m_s": v_mj_xz_jac,
                "bridge_hand_speed_xz": v_br,
                "bridge_ee_speed_xz_m_s": v_br,
            }
        )

    mj_qd1_series = np.array([r["mujoco_qdot1_rad_s"] for r in rows], dtype=float)
    mj_qd2_series = np.array([r["mujoco_qdot2_rad_s"] for r in rows], dtype=float)
    spike_count = count_spikes_from_velocity(mj_qd1_series, dt, args.velocity_spike_threshold_rad_s2) + count_spikes_from_velocity(
        mj_qd2_series, dt, args.velocity_spike_threshold_rad_s2
    )
    jerk_outliers = count_jerk_outliers_from_velocity(mj_qd1_series, dt, args.jerk_threshold_rad_s3) + count_jerk_outliers_from_velocity(
        mj_qd2_series, dt, args.jerk_threshold_rad_s3
    )
    rmse_q = float(np.sqrt(np.mean(np.square(err_q))))
    rmse_qd = float(np.sqrt(np.mean(np.square(err_qd))))
    parity_ready = (
        spike_count == 0
        and jerk_outliers == 0
        and rmse_q <= args.rmse_q_threshold_rad
        and rmse_qd <= args.rmse_qd_threshold_rad_s
    )
    summary = {
        "xml": str(args.xml),
        "param_source": args.param_source,
        "dt": dt,
        "duration_s": duration_s,
        "steps": args.steps,
        "rmse_q_rad": rmse_q,
        "rmse_qd": rmse_qd,
        "rmse_hand_speed_norm_fd": float(np.sqrt(np.mean(np.square(err_vhand)))),
        "max_tau_clip_delta_nm": float(max(tau_clip_deltas) if tau_clip_deltas else 0.0),
        "velocity_spike_count": spike_count,
        "velocity_jerk_outlier_count": jerk_outliers,
        "parity_ready_bridge_gate": parity_ready,
        "canonical_contract": {
            "time_s": "seconds",
            "mujoco_q*_rad": "radians",
            "mujoco_qdot*_rad_s": "rad/s",
            "bridge_q*_rad": "radians",
            "bridge_qdot*_rad_s": "rad/s",
            "tau*_Nm": "N*m",
        },
    }

    fieldnames = list(rows[0].keys()) if rows else []
    with args.out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    with args.out_json.open("w") as f:
        json.dump(summary, f, indent=2)

    print("Summary:", json.dumps(summary, indent=2))
    print(f"Wrote {args.out_csv} and {args.out_json}")


if __name__ == "__main__":
    main()
