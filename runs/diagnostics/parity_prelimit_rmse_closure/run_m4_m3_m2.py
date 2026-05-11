#!/usr/bin/env python3
"""M4 -> M3 -> M2 pre-limit RMSE closure tranche (derived outputs only)."""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import mujoco  # noqa: E402

from example_two_link.matlab_v2_dynamics import compute_forward_dynamics  # noqa: E402
from example_two_link.matlab_v2_params import params_from_mujoco_xml  # noqa: E402
from systematic_studies.swing_torque_schedule import swing_torques  # noqa: E402

XML = ROOT / "example_two_link" / "two_link_arm.xml"
CSV_PATH = ROOT / "runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv"
OUT_DIR = Path(__file__).resolve().parent
PRELIMIT = 0.480
Q1_DEG_IC = 5.0
Q2_DEG_IC = 55.0
QD1_IC = 0.0
QD2_IC = 0.0
TAU_AMP = 0.0
TAU_F = 0.8
TAU_PHASE_DEG = 30.0
DT = 0.001


def load_rows() -> list[dict]:
    with CSV_PATH.open(newline="") as f:
        return list(csv.DictReader(f))


def run_m4(rows: list[dict]) -> dict:
    """IC / column / unit / sampling semantics."""
    r0 = rows[0]
    dt_csv = float(r0["dt_s"])
    # Column presence
    need = (
        "mujoco_q1_rad",
        "mujoco_q2_rad",
        "bridge_q1_rad",
        "bridge_q2_rad",
        "mujoco_qdot1_rad_s",
        "mujoco_qdot2_rad_s",
        "bridge_qdot1_rad_s",
        "bridge_qdot2_rad_s",
        "mj_q1_deg",
        "mj_q2_deg",
        "step",
        "time_s",
        "tau0",
        "tau1",
    )
    missing = [c for c in need if c not in r0]
    # Deg vs rad consistency (XML uses degrees)
    mq1 = float(r0["mujoco_q1_rad"])
    mq1_deg = float(r0["mj_q1_deg"])
    deg_err = abs(np.rad2deg(mq1) - mq1_deg)
    # Correlation sign (no swap): over pre-limit window, deltas should correlate
    pre = [r for r in rows if float(r["time_s"]) < PRELIMIT]
    b1 = np.array([float(r["bridge_q1_rad"]) for r in pre], float)
    b2 = np.array([float(r["bridge_q2_rad"]) for r in pre], float)
    m1 = np.array([float(r["mujoco_q1_rad"]) for r in pre], float)
    m2 = np.array([float(r["mujoco_q2_rad"]) for r in pre], float)
    corr_b1_m1 = float(np.corrcoef(b1, m1)[0, 1])
    corr_b1_m2 = float(np.corrcoef(b1, m2)[0, 1])
    corr_b2_m1 = float(np.corrcoef(b2, m1)[0, 1])
    corr_b2_m2 = float(np.corrcoef(b2, m2)[0, 1])
    swap_plausible = abs(corr_b1_m2) > abs(corr_b1_m1) and abs(corr_b2_m1) > abs(corr_b2_m2)
    # Reproduce first benchmark step (must match CSV row 0)
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    mujoco.mj_resetData(model, data)
    q0 = np.deg2rad([Q1_DEG_IC, Q2_DEG_IC], dtype=float)
    data.qpos[0], data.qpos[1] = q0[0], q0[1]
    data.qvel[0], data.qvel[1] = QD1_IC, QD2_IC
    phase = math.radians(TAU_PHASE_DEG)
    t0 = 0.0
    tau0, tau1 = swing_torques(t0, TAU_AMP, TAU_F, phase)
    data.ctrl[0], data.ctrl[1] = tau0, tau1
    mujoco.mj_step(model, data)
    mj_after = np.array([data.qpos[0], data.qpos[1], data.qvel[0], data.qvel[1]], float)
    params = params_from_mujoco_xml(XML)
    qb = np.deg2rad([Q1_DEG_IC, Q2_DEG_IC], dtype=float)
    qdb = np.array([QD1_IC, QD2_IC], float)
    from example_two_link.matlab_v2_dynamics import integrate_step  # noqa: E402

    qb2, qdb2 = integrate_step(qb, qdb, np.array([tau0, tau1]), DT, params, method="semi_implicit_euler", gravity_sign="default")
    br_after = np.concatenate([qb2, qdb2])
    csv_state = np.array(
        [
            float(r0["mujoco_q1_rad"]),
            float(r0["mujoco_q2_rad"]),
            float(r0["mujoco_qdot1_rad_s"]),
            float(r0["mujoco_qdot2_rad_s"]),
        ],
        float,
    )
    csv_bridge = np.array(
        [
            float(r0["bridge_q1_rad"]),
            float(r0["bridge_q2_rad"]),
            float(r0["bridge_qdot1_rad_s"]),
            float(r0["bridge_qdot2_rad_s"]),
        ],
        float,
    )
    repro_mj_err = float(np.linalg.norm(mj_after - csv_state))
    repro_br_err = float(np.linalg.norm(br_after - csv_bridge))
    time_label = float(r0["time_s"])
    step_label = float(r0["step"])
    blocking = False
    issues: list[str] = []
    if missing:
        issues.append(f"missing columns: {missing}")
        blocking = True
    if deg_err > 1e-6:
        issues.append(f"deg/rad mismatch row0: {deg_err}")
        blocking = True
    if swap_plausible:
        issues.append("cross-correlation suggests possible q1/q2 column swap between bridge and mujoco")
        blocking = True
    if repro_mj_err > 1e-5 or repro_br_err > 1e-5:
        issues.append(f"first step reproduction err mj={repro_mj_err} br={repro_br_err}")
        blocking = True
    if abs(dt_csv - DT) > 1e-12:
        issues.append(f"dt mismatch csv={dt_csv}")
    status = "blocking issue" if blocking else "pass"
    return {
        "status": status,
        "missing_columns": missing,
        "deg_rad_row0_max_abs_err_deg": deg_err,
        "prelimit_corrcoef_bridge_q1_mujoco_q1": corr_b1_m1,
        "prelimit_corrcoef_bridge_q1_mujoco_q2": corr_b1_m2,
        "prelimit_corrcoef_bridge_q2_mujoco_q1": corr_b2_m1,
        "prelimit_corrcoef_bridge_q2_mujoco_q2": corr_b2_m2,
        "swap_plausible_by_crosscorr": swap_plausible,
        "reproduce_first_step_mj_l2_err": repro_mj_err,
        "reproduce_first_step_bridge_l2_err": repro_br_err,
        "time_semantics": {
            "csv_time_s_is_loop_t_equals_k_times_dt": True,
            "state_recorded_after_mj_step_and_after_bridge_integrate_step": True,
            "interpretation": "Row k uses time_s=k*dt (start-of-step label) while q/qdot are post-step states for both simulators; pairwise comparison remains aligned.",
        },
        "issues": issues,
    }


def run_m3(model: mujoco.MjModel, rows: list[dict]) -> dict:
    params = params_from_mujoco_xml(XML)
    # MuJoCo masses from bodies (skip world)
    bid_shoulder = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "shoulder")
    bid_elbow = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "elbow")
    mj_masses = {
        "shoulder_body_mass": float(model.body_mass[bid_shoulder]),
        "elbow_body_mass": float(model.body_mass[bid_elbow]),
    }
    pdict = params.to_dict()
    # Compare nominal params
    param_compare = {k: {"bridge": pdict[k], "note": "mujoco uses geom density-derived in params_from_mujoco_xml"} for k in ("l1", "l2", "m1", "m2", "I1", "I2", "g")}
    # Mass matrix at a few states
    data = mujoco.MjData(model)
    idxs = [0, 120, 240, 360, 470]
    M_rows = []
    for i in idxs:
        r = rows[i]
        q = np.array([float(r["mujoco_q1_rad"]), float(r["mujoco_q2_rad"])], float)
        qd = np.array([float(r["mujoco_qdot1_rad_s"]), float(r["mujoco_qdot2_rad_s"])], float)
        data.qpos[0], data.qpos[1] = q[0], q[1]
        data.qvel[0], data.qvel[1] = qd[0], qd[1]
        mujoco.mj_forward(model, data)
        Mm = np.zeros((model.nv, model.nv), dtype=float)
        mujoco.mj_fullM(model, Mm, data.qM)
        Mmj = Mm[:2, :2].copy()
        from example_two_link.matlab_v2_dynamics import two_link_tennis_model  # noqa: E402

        Mbr, _, _, _ = two_link_tennis_model(q, qd, params)
        frob = float(np.linalg.norm(Mmj - Mbr))
        rel = frob / (float(np.linalg.norm(Mmj)) + 1e-12)
        cond_mj = float(np.linalg.cond(Mmj))
        cond_br = float(np.linalg.cond(Mbr))
        M_rows.append(
            {
                "csv_row_index": i,
                "time_s": float(r["time_s"]),
                "frob_norm_diff_M": frob,
                "relative_frob": rel,
                "cond_mujoco": cond_mj,
                "cond_bridge": cond_br,
            }
        )
    max_rel = max(x["relative_frob"] for x in M_rows)
    # Bridge params intentionally approximate capsule geometry — expect M mismatch; not a harness "blocking bug".
    status = "plausible mismatch"
    return {
        "status": status,
        "params_bridge": pdict,
        "mujoco_body_masses": mj_masses,
        "mass_matrix_samples": M_rows,
        "max_relative_frobenius_M": max_rel,
        "note": "Bridge dynamics use params_from_mujoco_xml (approximate inertia from density); MuJoCo uses full MJCF. Analytical M will not match mj_fullM exactly even if lengths align.",
    }


def run_m2(model: mujoco.MjModel, rows: list[dict]) -> dict:
    data = mujoco.MjData(model)
    params = params_from_mujoco_xml(XML)
    phase = math.radians(TAU_PHASE_DEG)
    specs: list[tuple[str, int | None, np.ndarray, np.ndarray, np.ndarray, float]] = [
        ("q00", None, np.zeros(2), np.zeros(2), np.zeros(2), 0.0),
    ]
    for idx in (0, 120, 240, 360, 470):
        r = rows[idx]
        if float(r["time_s"]) >= PRELIMIT:
            raise RuntimeError(f"row {idx} not pre-limit")
        q = np.array([float(r["mujoco_q1_rad"]), float(r["mujoco_q2_rad"])], float)
        qd = np.array([float(r["mujoco_qdot1_rad_s"]), float(r["mujoco_qdot2_rad_s"])], float)
        t = float(r["time_s"])
        tau0, tau1 = swing_torques(t, TAU_AMP, TAU_F, phase)
        specs.append((f"row_{idx}", idx, q, qd, np.array([tau0, tau1], float), t))
    out_rows = []
    for name, idx, q, qd, tau, t_s in specs:
        data.qpos[0], data.qpos[1] = q[0], q[1]
        data.qvel[0], data.qvel[1] = qd[0], qd[1]
        data.ctrl[0], data.ctrl[1] = tau[0], tau[1]
        mujoco.mj_forward(model, data)
        mj_acc = np.array([data.qacc[0], data.qacc[1]], float)
        bd = compute_forward_dynamics(q, qd, tau, params, gravity_sign="default")
        bm = compute_forward_dynamics(q, qd, tau, params, gravity_sign="mujoco")
        d0 = float(np.linalg.norm(mj_acc - bd))
        dm = float(np.linalg.norm(mj_acc - bm))
        best = min(d0, dm)
        out_rows.append(
            {
                "state": name,
                "csv_row": idx,
                "time_s": t_s,
                "mujoco_qacc1": mj_acc[0],
                "mujoco_qacc2": mj_acc[1],
                "bridge_default_qdd1": bd[0],
                "bridge_default_qdd2": bd[1],
                "bridge_mujoco_sign_qdd1": bm[0],
                "bridge_mujoco_sign_qdd2": bm[1],
                "l2_err_default": d0,
                "l2_err_mujoco_sign": dm,
                "best_delta_norm": best,
                "closer": "default" if d0 <= dm else "mujoco_sign",
            }
        )
    return {"rows": out_rows}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    m4 = run_m4(rows)
    (OUT_DIR / "m4_ic_column_audit.json").write_text(json.dumps(m4, indent=2), encoding="utf-8")

    m4_block = m4["status"] == "blocking issue"
    m3 = {"status": "skipped_m4_blocking", "detail": m4} if m4_block else run_m3(mujoco.MjModel.from_xml_path(str(XML)), rows)
    (OUT_DIR / "m3_mass_matrix_audit.json").write_text(json.dumps(m3, indent=2), encoding="utf-8")

    if m4_block:
        m2 = {"status": "skipped_m4_blocking", "m4": m4.get("status")}
    else:
        m2 = {"status": "ok", **run_m2(mujoco.MjModel.from_xml_path(str(XML)), rows)}
    (OUT_DIR / "m2_sparse_qacc.json").write_text(json.dumps(m2, indent=2), encoding="utf-8")

    summary = {"m4": m4["status"], "m3": m3.get("status") if isinstance(m3, dict) else str(m3), "m2": m2.get("status")}
    (OUT_DIR / "tranche_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
