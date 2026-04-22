#!/usr/bin/env python3
"""
Racket / end-effector trajectory visualiser for the two-link planar arm.

Drives the arm under one of three protocols and logs the canonical state +
hand-site trajectory (rad / rad/s / N*m / m).

Protocols
  - passive: no torque, gravity only.
  - open_loop_lissajous: open-loop sinusoidal torques with a configurable
    elbow:shoulder frequency ratio (no closed-loop tracking).
  - figure8: PD-tracked joint trajectories with q1 ~ sin(omega*t) and
    q2 ~ sin(2*omega*t + pi/2). The 2:1 frequency ratio is the classical
    Lissajous condition for a figure-8 in workspace, so the hand trace in
    the X-Z plane reads as a clean infinity figure.

Outputs (under systematic_studies/outputs/):
  - racket_trajectory_timeseries.csv
  - racket_trajectory_summary.json (includes a figure8_detected flag)

Plot mode also writes (under systematic_studies/outputs/figures/):
  - racket_trajectory_xz.png
  - racket_trajectory_joint_vs_time.png

Viewer mode opens a passive MuJoCo viewer (macOS: requires mjpython, routed
through run.sh).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


DEFAULT_XML = ROOT / "example_two_link" / "two_link_arm.xml"
OUTPUTS_DIR = ROOT / "systematic_studies" / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
DEFAULT_CSV = OUTPUTS_DIR / "racket_trajectory_timeseries.csv"
DEFAULT_JSON = OUTPUTS_DIR / "racket_trajectory_summary.json"


def open_loop_lissajous_torques(
    t: float,
    a_shoulder: float,
    a_elbow: float,
    f_shoulder_hz: float,
    elbow_freq_ratio: float,
    elbow_phase_rad: float,
) -> tuple[float, float]:
    """Open-loop sinusoidal torques with a configurable elbow frequency ratio.

    Sensitive to model parameters: the realised joint angles deviate from a
    pure sinusoid because of gravity, inertia coupling, and damping. Useful
    as a baseline alternative to the PD-tracked figure-8 protocol.
    """
    omega = 2.0 * math.pi * f_shoulder_hz
    tau_shoulder = a_shoulder * math.sin(omega * t)
    tau_elbow = a_elbow * math.sin(elbow_freq_ratio * omega * t + elbow_phase_rad)
    return tau_shoulder, tau_elbow


def passive_torques(_t: float) -> tuple[float, float]:
    return 0.0, 0.0


def figure8_reference(
    t: float,
    q1_amp_rad: float,
    q2_amp_rad: float,
    q1_offset_rad: float,
    q2_offset_rad: float,
    f_shoulder_hz: float,
    elbow_phase_rad: float,
) -> tuple[float, float, float, float]:
    """Joint-space figure-8 reference (Lissajous 2:1 in joint angles).

    q1 (shoulder) at frequency `f_shoulder_hz`, q2 (elbow) at twice that
    frequency with a configurable phase offset.
    Returns (q1_des, q2_des, qd1_des, qd2_des).
    """
    omega = 2.0 * math.pi * f_shoulder_hz
    q1 = q1_offset_rad + q1_amp_rad * math.sin(omega * t)
    q2 = q2_offset_rad + q2_amp_rad * math.sin(2.0 * omega * t + elbow_phase_rad)
    qd1 = q1_amp_rad * omega * math.cos(omega * t)
    qd2 = q2_amp_rad * 2.0 * omega * math.cos(2.0 * omega * t + elbow_phase_rad)
    return q1, q2, qd1, qd2


# Two-link planar arm forward kinematics for the MuJoCo XML in
# example_two_link/two_link_arm.xml. The shoulder hinge axis is +Y, so a
# positive q1 takes the upperarm from +X toward -Z (i.e. "down").
# Shoulder origin is at world (0, 0, SHOULDER_Z).
SHOULDER_Z = 1.4
L1 = 0.32
L2 = 0.26


def two_link_fk(q1: float, q2: float) -> tuple[float, float]:
    """Forward kinematics: returns (hand_x, hand_z) in world frame."""
    hand_x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    hand_z = SHOULDER_Z - L1 * math.sin(q1) - L2 * math.sin(q1 + q2)
    return hand_x, hand_z


def two_link_ik(
    hand_x: float,
    hand_z: float,
    elbow_up: bool = False,
) -> tuple[float, float] | None:
    """Inverse kinematics for the two-link planar arm.

    Returns (q1, q2) in radians or None when the target is unreachable.
    Convention matches the MJCF: q1 about +Y, hand_z = SHOULDER_Z - L1 sin q1 - L2 sin(q1+q2).
    """
    dx = hand_x
    dz = SHOULDER_Z - hand_z
    r2 = dx * dx + dz * dz
    cos_q2 = (r2 - L1 * L1 - L2 * L2) / (2.0 * L1 * L2)
    if cos_q2 < -1.0 or cos_q2 > 1.0:
        return None
    q2 = math.acos(cos_q2)
    if elbow_up:
        q2 = -q2
    sin_q2 = math.sin(q2)
    k1 = L1 + L2 * cos_q2
    k2 = L2 * sin_q2
    q1 = math.atan2(dz, dx) - math.atan2(k2, k1)
    return q1, q2


def workspace_figure8_reference(
    t: float,
    cx: float,
    cz: float,
    half_width_m: float,
    half_height_m: float,
    f_hz: float,
    dt_eps: float = 1e-4,
) -> tuple[float, float, float, float] | None:
    """Workspace figure-8: (x,z) Lissajous 2:1, then back-solve via IK.

    Returns (q1_des, q2_des, qd1_des, qd2_des) or None if any sample is
    unreachable. Velocities are estimated by finite difference of the IK
    solution at +/- dt_eps for robustness without requiring an analytical
    Jacobian.
    """
    omega = 2.0 * math.pi * f_hz
    x = cx + half_width_m * math.sin(omega * t)
    z = cz + half_height_m * math.sin(2.0 * omega * t)
    sol = two_link_ik(x, z)
    if sol is None:
        return None
    q1, q2 = sol

    x_p = cx + half_width_m * math.sin(omega * (t + dt_eps))
    z_p = cz + half_height_m * math.sin(2.0 * omega * (t + dt_eps))
    sol_p = two_link_ik(x_p, z_p)
    x_m = cx + half_width_m * math.sin(omega * (t - dt_eps))
    z_m = cz + half_height_m * math.sin(2.0 * omega * (t - dt_eps))
    sol_m = two_link_ik(x_m, z_m)
    if sol_p is None or sol_m is None:
        return q1, q2, 0.0, 0.0

    qd1 = (sol_p[0] - sol_m[0]) / (2.0 * dt_eps)
    qd2 = (sol_p[1] - sol_m[1]) / (2.0 * dt_eps)
    return q1, q2, qd1, qd2


def pd_tracking_torques(
    q: np.ndarray,
    qd: np.ndarray,
    q_des: np.ndarray,
    qd_des: np.ndarray,
    kp: float,
    kd: float,
) -> np.ndarray:
    return kp * (q_des - q) + kd * (qd_des - qd)


def hand_speed_xz(model: mujoco.MjModel, data: mujoco.MjData, site_id: int) -> float:
    jacp = np.zeros((3, model.nv), dtype=float)
    jacr = np.zeros((3, model.nv), dtype=float)
    mujoco.mj_jacSite(model, data, jacp, jacr, site_id)
    v = jacp @ data.qvel
    return float(math.hypot(v[0], v[2]))


def detect_figure8(
    hand_x: np.ndarray,
    hand_z: np.ndarray,
    dt: float,
    settle_frac: float = 0.35,
) -> dict[str, float | bool | int]:
    """Lightweight Lissajous-style detector for an X-Z figure-8 trace.

    Strategy:
      * Drop the early settling window so the steady-state pattern dominates.
      * FFT both axes (after centring) and read the dominant frequency.
      * Figure-8 is flagged when z_dom_freq / x_dom_freq is approximately 2:1.
      * Also count self-intersections of the centred trace as a robustness check.
    """
    n = hand_x.size
    if n < 32:
        return {
            "figure8_detected": False,
            "x_dominant_freq_hz": float("nan"),
            "z_dominant_freq_hz": float("nan"),
            "freq_ratio_z_over_x": float("nan"),
            "self_intersections": 0,
            "trace_extent_x_m": 0.0,
            "trace_extent_z_m": 0.0,
        }

    start = int(n * settle_frac)
    x = hand_x[start:] - float(np.mean(hand_x[start:]))
    z = hand_z[start:] - float(np.mean(hand_z[start:]))
    fs = 1.0 / dt
    pad_n = max(x.size, 4096)
    freqs = np.fft.rfftfreq(pad_n, d=dt)
    spec_x = np.abs(np.fft.rfft(x, n=pad_n))
    spec_z = np.abs(np.fft.rfft(z, n=pad_n))
    if freqs.size > 1:
        spec_x[0] = 0.0
        spec_z[0] = 0.0

    f_x = float(freqs[int(np.argmax(spec_x))]) if spec_x.size else float("nan")
    f_z = float(freqs[int(np.argmax(spec_z))]) if spec_z.size else float("nan")
    ratio = f_z / f_x if f_x > 1e-9 else float("nan")
    figure8 = (
        math.isfinite(ratio)
        and (1.6 <= ratio <= 2.4 or 0.42 <= ratio <= 0.62)
        and float(np.std(x)) > 1e-3
        and float(np.std(z)) > 1e-3
    )
    target = max(64, x.size // 16)
    stride = max(1, x.size // target)
    intersections = _count_self_intersections(x, z, stride=stride)
    return {
        "figure8_detected": bool(figure8),
        "x_dominant_freq_hz": f_x,
        "z_dominant_freq_hz": f_z,
        "freq_ratio_z_over_x": float(ratio) if math.isfinite(ratio) else float("nan"),
        "self_intersections": int(intersections),
        "trace_extent_x_m": float(np.ptp(hand_x[start:])),
        "trace_extent_z_m": float(np.ptp(hand_z[start:])),
        "sampling_rate_hz": float(fs),
    }


def _count_self_intersections(x: np.ndarray, z: np.ndarray, stride: int = 1) -> int:
    """Count segment-segment crossings of a 2D polyline.

    O(n^2) but trimmed by `stride` and the fact that the centred trace size is
    moderate (a few thousand samples at most for typical horizons).
    """
    n = x.size
    if n < 4:
        return 0
    points = np.stack([x[::stride], z[::stride]], axis=1)
    m = points.shape[0]
    if m < 4:
        return 0
    crossings = 0
    for i in range(m - 1):
        p1, p2 = points[i], points[i + 1]
        for j in range(i + 2, m - 1):
            if i == 0 and j == m - 2:
                continue
            p3, p4 = points[j], points[j + 1]
            if _segments_intersect(p1, p2, p3, p4):
                crossings += 1
    return crossings


def _segments_intersect(p1, p2, p3, p4) -> bool:
    def ccw(a, b, c) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    d1 = ccw(p3, p4, p1)
    d2 = ccw(p3, p4, p2)
    d3 = ccw(p1, p2, p3)
    d4 = ccw(p1, p2, p4)
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
        (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
    )


def write_csv(rows: list[dict[str, float]], path: Path) -> None:
    if not rows:
        raise RuntimeError("No rows to write; rollout produced an empty trajectory.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(summary, f, indent=2)


def plot_outputs(
    rows: list[dict[str, float]],
    figures_dir: Path,
    summary: dict,
) -> dict[str, Path]:
    """Generate the X-Z trace and joint/speed-vs-time figures."""
    import matplotlib.pyplot as plt

    sys.path.insert(0, str(ROOT / "systematic_studies" / "visualisation"))
    from plot_results import configure_plot_style  # noqa: WPS433

    configure_plot_style(light_grid=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    t = np.array([r["time_s"] for r in rows], dtype=float)
    hx = np.array([r["hand_x"] for r in rows], dtype=float)
    hz = np.array([r["hand_z"] for r in rows], dtype=float)
    q1 = np.rad2deg(np.array([r["q1_rad"] for r in rows], dtype=float))
    q2 = np.rad2deg(np.array([r["q2_rad"] for r in rows], dtype=float))
    speed = np.array([r["hand_speed_xz_m_s"] for r in rows], dtype=float)

    paths: dict[str, Path] = {}

    fig, ax = plt.subplots(figsize=(7.0, 6.4))
    ax.plot(hx, hz, lw=1.4, label="Racket tip trace")
    ax.plot([hx[0]], [hz[0]], "o", color="tab:green", label="Start")
    ax.plot([hx[-1]], [hz[-1]], "o", color="tab:red", label="End")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Hand X (m)")
    ax.set_ylabel("Hand Z (m)")
    title = "Racket Tip Trajectory (X-Z plane)"
    if summary.get("figure8_detected"):
        title += "  -  Figure-8 detected"
    ax.set_title(title)
    ax.legend(loc="best")
    fig.tight_layout()
    xz_path = figures_dir / "racket_trajectory_xz.png"
    fig.savefig(xz_path, dpi=300)
    plt.close(fig)
    paths["xz"] = xz_path

    fig, axes = plt.subplots(2, 1, figsize=(9.0, 6.0), sharex=True)
    axes[0].plot(t, q1, label="Shoulder q1 (deg)")
    axes[0].plot(t, q2, label="Elbow q2 (deg)")
    axes[0].set_ylabel("Joint angle (deg)")
    axes[0].set_title("Joint Angles vs Time")
    axes[0].legend(loc="best")

    peak_idx = int(np.argmax(speed))
    axes[1].plot(t, speed, color="tab:purple", label="Hand speed (m/s)")
    axes[1].plot([t[peak_idx]], [speed[peak_idx]], "o", color="tab:red")
    axes[1].annotate(
        f"Peak {speed[peak_idx]:.2f} m/s",
        xy=(t[peak_idx], speed[peak_idx]),
        xytext=(8, 10),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "lw": 0.9},
    )
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Hand X-Z speed (m/s)")
    axes[1].set_title("Racket Tip Speed vs Time")
    axes[1].legend(loc="best")
    fig.tight_layout()
    speed_path = figures_dir / "racket_trajectory_joint_vs_time.png"
    fig.savefig(speed_path, dpi=300)
    plt.close(fig)
    paths["joint_vs_time"] = speed_path

    return paths


def simulate(
    xml_path: Path,
    protocol: str,
    steps: int,
    a_shoulder: float,
    a_elbow: float,
    f_shoulder_hz: float,
    elbow_freq_ratio: float,
    elbow_phase_deg: float,
    q1_amp_deg: float,
    q2_amp_deg: float,
    q1_offset_deg: float,
    q2_offset_deg: float,
    pd_kp: float,
    pd_kd: float,
    q1_init_deg: float,
    q2_init_deg: float,
    qd1: float,
    qd2: float,
    ws_center_x: float,
    ws_center_z: float,
    ws_half_width_m: float,
    ws_half_height_m: float,
    ws_f_hz: float,
    viewer_mode: bool,
    viewer_realtime: bool,
) -> tuple[list[dict[str, float]], dict]:
    """Run the rollout and return (rows, summary).

    When `viewer_mode` is True we additionally drive a passive MuJoCo viewer
    in the same loop; closing the viewer window stops the rollout.
    """
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)
    dt = float(model.opt.timestep)

    hand_sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "hand")
    if hand_sid < 0:
        raise RuntimeError(f"XML {xml_path} must define site 'hand'.")

    elbow_phase = math.radians(elbow_phase_deg)
    q1_amp_rad = math.radians(q1_amp_deg)
    q2_amp_rad = math.radians(q2_amp_deg)
    q1_offset_rad = math.radians(q1_offset_deg)
    q2_offset_rad = math.radians(q2_offset_deg)
    ctrl_range = model.actuator_ctrlrange[:2, :] if model.nu >= 2 else None

    if protocol == "figure8":
        q1_des0, q2_des0, qd1_des0, qd2_des0 = figure8_reference(
            0.0, q1_amp_rad, q2_amp_rad, q1_offset_rad, q2_offset_rad, f_shoulder_hz, elbow_phase
        )
        init_q1, init_q2, init_qd1, init_qd2 = q1_des0, q2_des0, qd1_des0, qd2_des0
    elif protocol == "workspace_figure8":
        ws_init = workspace_figure8_reference(
            0.0, ws_center_x, ws_center_z, ws_half_width_m, ws_half_height_m, ws_f_hz
        )
        if ws_init is None:
            raise RuntimeError(
                "workspace_figure8 initial target unreachable; tighten ws-half-width/height or recenter."
            )
        init_q1, init_q2, init_qd1, init_qd2 = ws_init
    else:
        init_q1 = math.radians(q1_init_deg)
        init_q2 = math.radians(q2_init_deg)
        init_qd1 = qd1
        init_qd2 = qd2

    mujoco.mj_resetData(model, data)
    data.qpos[0] = init_q1
    data.qpos[1] = init_q2
    data.qvel[0] = init_qd1
    data.qvel[1] = init_qd2
    mujoco.mj_forward(model, data)

    rows: list[dict[str, float]] = []
    tau_clip_max = 0.0

    viewer_ctx = None
    if viewer_mode:
        from mujoco import viewer as mj_viewer  # noqa: WPS433

        viewer_ctx = mj_viewer.launch_passive(model, data)

    try:
        for k in range(steps):
            t = k * dt
            q_now = np.array([data.qpos[0], data.qpos[1]], dtype=float)
            qd_now = np.array([data.qvel[0], data.qvel[1]], dtype=float)

            q_des = np.array([float("nan"), float("nan")], dtype=float)
            qd_des = np.array([float("nan"), float("nan")], dtype=float)
            if protocol == "figure8":
                q_des_1, q_des_2, qd_des_1, qd_des_2 = figure8_reference(
                    t,
                    q1_amp_rad,
                    q2_amp_rad,
                    q1_offset_rad,
                    q2_offset_rad,
                    f_shoulder_hz,
                    elbow_phase,
                )
                q_des = np.array([q_des_1, q_des_2], dtype=float)
                qd_des = np.array([qd_des_1, qd_des_2], dtype=float)
                tau = pd_tracking_torques(q_now, qd_now, q_des, qd_des, pd_kp, pd_kd)
                tau0, tau1 = float(tau[0]), float(tau[1])
            elif protocol == "workspace_figure8":
                ws_ref = workspace_figure8_reference(
                    t, ws_center_x, ws_center_z, ws_half_width_m, ws_half_height_m, ws_f_hz
                )
                if ws_ref is None:
                    tau0, tau1 = 0.0, 0.0
                else:
                    q_des = np.array([ws_ref[0], ws_ref[1]], dtype=float)
                    qd_des = np.array([ws_ref[2], ws_ref[3]], dtype=float)
                    tau = pd_tracking_torques(q_now, qd_now, q_des, qd_des, pd_kp, pd_kd)
                    tau0, tau1 = float(tau[0]), float(tau[1])
            elif protocol == "open_loop_lissajous":
                tau0, tau1 = open_loop_lissajous_torques(
                    t,
                    a_shoulder,
                    a_elbow,
                    f_shoulder_hz,
                    elbow_freq_ratio,
                    elbow_phase,
                )
            elif protocol == "passive":
                tau0, tau1 = passive_torques(t)
            else:
                raise ValueError(f"Unknown protocol: {protocol}")

            tau = np.array([tau0, tau1], dtype=float)
            applied = tau.copy()
            if ctrl_range is not None:
                applied = np.clip(tau, ctrl_range[:, 0], ctrl_range[:, 1])
            tau_clip_max = max(tau_clip_max, float(np.max(np.abs(applied - tau))))

            if model.nu >= 2:
                data.ctrl[0] = float(applied[0])
                data.ctrl[1] = float(applied[1])
            mujoco.mj_step(model, data)
            if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
                break

            hand = data.site_xpos[hand_sid].copy()
            speed = hand_speed_xz(model, data, hand_sid)
            row = {
                "step": float(k),
                "time_s": float(t),
                "dt_s": dt,
                "q1_rad": float(data.qpos[0]),
                "q2_rad": float(data.qpos[1]),
                "qd1_rad_s": float(data.qvel[0]),
                "qd2_rad_s": float(data.qvel[1]),
                "tau1_Nm": float(tau[0]),
                "tau2_Nm": float(tau[1]),
                "tau1_applied_Nm": float(applied[0]),
                "tau2_applied_Nm": float(applied[1]),
                "hand_x": float(hand[0]),
                "hand_y": float(hand[1]),
                "hand_z": float(hand[2]),
                "hand_speed_xz_m_s": speed,
            }
            row["q1_des_rad"] = float(q_des[0])
            row["q2_des_rad"] = float(q_des[1])
            row["qd1_des_rad_s"] = float(qd_des[0])
            row["qd2_des_rad_s"] = float(qd_des[1])
            rows.append(row)

            if viewer_ctx is not None:
                if not viewer_ctx.is_running():
                    break
                viewer_ctx.sync()
                if viewer_realtime:
                    time.sleep(dt)
    finally:
        if viewer_ctx is not None:
            viewer_ctx.close()

    if not rows:
        raise RuntimeError("Rollout produced no samples.")

    hx = np.array([r["hand_x"] for r in rows], dtype=float)
    hz = np.array([r["hand_z"] for r in rows], dtype=float)
    speeds = np.array([r["hand_speed_xz_m_s"] for r in rows], dtype=float)
    detection = detect_figure8(hx, hz, dt)

    summary: dict = {
        "xml": str(xml_path),
        "protocol": protocol,
        "dt_s": dt,
        "steps": len(rows),
        "duration_s": (len(rows) - 1) * dt,
        "a_shoulder_Nm": a_shoulder,
        "a_elbow_Nm": a_elbow,
        "f_shoulder_hz": f_shoulder_hz,
        "elbow_freq_ratio": elbow_freq_ratio,
        "elbow_phase_deg": elbow_phase_deg,
        "q1_amp_deg": q1_amp_deg,
        "q2_amp_deg": q2_amp_deg,
        "q1_offset_deg": q1_offset_deg,
        "q2_offset_deg": q2_offset_deg,
        "pd_kp": pd_kp,
        "pd_kd": pd_kd,
        "ws_center_x_m": ws_center_x,
        "ws_center_z_m": ws_center_z,
        "ws_half_width_m": ws_half_width_m,
        "ws_half_height_m": ws_half_height_m,
        "ws_f_hz": ws_f_hz,
        "tau_clip_max_delta_Nm": tau_clip_max,
        "peak_hand_speed_xz_m_s": float(np.max(speeds)),
        "mean_hand_speed_xz_m_s": float(np.mean(speeds)),
        "canonical_contract": {
            "time_s": "seconds",
            "q*_rad": "radians",
            "qdot*_rad_s": "rad/s",
            "tau*_Nm": "N*m",
            "hand_*": "m",
        },
    }
    summary.update(detection)
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Racket / end-effector trajectory visualiser for the two-link arm."
    )
    parser.add_argument("--xml", type=Path, default=DEFAULT_XML, help="MJCF path for the two-link arm.")
    parser.add_argument(
        "--protocol",
        choices=("passive", "open_loop_lissajous", "figure8", "workspace_figure8"),
        default="workspace_figure8",
        help=(
            "Driving protocol. workspace_figure8 (default) = PD-tracked workspace "
            "Lissajous 2:1 via inverse kinematics (cleanest infinity trace). "
            "figure8 = PD-tracked joint-space Lissajous 2:1. "
            "open_loop_lissajous = open-loop sinusoidal torques. "
            "passive = no torque."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("headless", "plot", "viewer"),
        default="plot",
        help="headless = CSV+JSON only; plot = also write PNGs; viewer = also open MuJoCo viewer.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=10000,
        help="Total simulation steps. >= 8000 recommended so FFT-based figure-8 detection is reliable.",
    )
    parser.add_argument("--a-shoulder", type=float, default=18.0, help="Open-loop shoulder torque amplitude (Nm).")
    parser.add_argument("--a-elbow", type=float, default=10.0, help="Open-loop elbow torque amplitude (Nm).")
    parser.add_argument("--f-shoulder-hz", type=float, default=0.6, help="Shoulder driving frequency (Hz).")
    parser.add_argument(
        "--elbow-freq-ratio",
        type=float,
        default=2.0,
        help="Open-loop elbow:shoulder frequency ratio (2.0 = 2:1 Lissajous).",
    )
    parser.add_argument("--elbow-phase-deg", type=float, default=90.0, help="Phase offset for the elbow signal (deg).")
    parser.add_argument("--q1-amp-deg", type=float, default=35.0, help="Figure-8 shoulder angle amplitude (deg).")
    parser.add_argument("--q2-amp-deg", type=float, default=45.0, help="Figure-8 elbow angle amplitude (deg).")
    parser.add_argument("--q1-offset-deg", type=float, default=0.0, help="Figure-8 shoulder angle offset (deg).")
    parser.add_argument("--q2-offset-deg", type=float, default=70.0, help="Figure-8 elbow angle offset (deg).")
    parser.add_argument("--pd-kp", type=float, default=120.0, help="PD proportional gain for figure-8 tracking.")
    parser.add_argument("--pd-kd", type=float, default=8.0, help="PD derivative gain for figure-8 tracking.")
    parser.add_argument("--q1-init-deg", type=float, default=10.0, help="Initial shoulder angle (deg) for non-figure-8 protocols.")
    parser.add_argument("--q2-init-deg", type=float, default=70.0, help="Initial elbow angle (deg) for non-figure-8 protocols.")
    parser.add_argument("--qd1", type=float, default=0.0, help="Initial shoulder velocity (rad/s) for non-figure-8 protocols.")
    parser.add_argument("--qd2", type=float, default=0.0, help="Initial elbow velocity (rad/s) for non-figure-8 protocols.")
    parser.add_argument("--ws-center-x", type=float, default=0.40, help="Workspace figure-8 centre X (m).")
    parser.add_argument("--ws-center-z", type=float, default=1.20, help="Workspace figure-8 centre Z (m).")
    parser.add_argument("--ws-half-width-m", type=float, default=0.12, help="Half-width of the figure-8 along X (m).")
    parser.add_argument("--ws-half-height-m", type=float, default=0.08, help="Half-height of the figure-8 along Z (m).")
    parser.add_argument("--ws-f-hz", type=float, default=0.5, help="Figure-8 base frequency (full ∞ takes 1/f_hz seconds).")
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--no-realtime", action="store_true", help="Disable real-time pacing in viewer mode.")
    args = parser.parse_args()

    rows, summary = simulate(
        xml_path=args.xml,
        protocol=args.protocol,
        steps=args.steps,
        a_shoulder=args.a_shoulder,
        a_elbow=args.a_elbow,
        f_shoulder_hz=args.f_shoulder_hz,
        elbow_freq_ratio=args.elbow_freq_ratio,
        elbow_phase_deg=args.elbow_phase_deg,
        q1_amp_deg=args.q1_amp_deg,
        q2_amp_deg=args.q2_amp_deg,
        q1_offset_deg=args.q1_offset_deg,
        q2_offset_deg=args.q2_offset_deg,
        pd_kp=args.pd_kp,
        pd_kd=args.pd_kd,
        q1_init_deg=args.q1_init_deg,
        q2_init_deg=args.q2_init_deg,
        qd1=args.qd1,
        qd2=args.qd2,
        ws_center_x=args.ws_center_x,
        ws_center_z=args.ws_center_z,
        ws_half_width_m=args.ws_half_width_m,
        ws_half_height_m=args.ws_half_height_m,
        ws_f_hz=args.ws_f_hz,
        viewer_mode=(args.mode == "viewer"),
        viewer_realtime=not args.no_realtime,
    )

    write_csv(rows, args.out_csv)
    write_summary(summary, args.out_json)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_json}")
    print(
        "Figure-8 detected: "
        f"{summary['figure8_detected']} (z/x freq ratio={summary['freq_ratio_z_over_x']:.2f}, "
        f"self-intersections={summary['self_intersections']}, "
        f"peak hand speed XZ={summary['peak_hand_speed_xz_m_s']:.3f} m/s)"
    )

    if args.mode in ("plot", "viewer"):
        out_paths = plot_outputs(rows, args.figures_dir, summary)
        for label, path in out_paths.items():
            print(f"Wrote figure [{label}]: {path}")


if __name__ == "__main__":
    main()
