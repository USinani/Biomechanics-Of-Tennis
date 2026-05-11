#!/usr/bin/env python3
"""
One-step acceleration comparison probe (Lane A).

Compares MuJoCo instantaneous qacc (via mj_forward) against analytical bridge qdd
at identical (q, qd, tau) states extracted from a derived 500-step CSV.

Writes derived outputs ONLY under runs/diagnostics/one_step_acceleration_probe/.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
DEFAULT_XML = ROOT / "example_two_link" / "two_link_arm.xml"
DEFAULT_CSV = (
    ROOT
    / "runs"
    / "diagnostics"
    / "parity_500step_probe"
    / "swing_benchmark_timeseries_500.csv"
)


@dataclass(frozen=True)
class CandidateState:
    label: str
    source: str
    step: int | None
    time_s: float
    q1: float
    q2: float
    qdot1: float
    qdot2: float
    tau1: float
    tau2: float


def _load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", newline="") as f:
        r = csv.DictReader(f)
        return list(r)


def _row_by_step(rows: list[dict[str, str]], step: int) -> dict[str, str]:
    for row in rows:
        if int(float(row["step"])) == int(step):
            return row
    raise KeyError(f"CSV missing requested step={step}")


def _state_from_row(label: str, csv_path: Path, row: dict[str, str]) -> CandidateState:
    # Prefer MuJoCo-native rad/rad_s columns to ensure we set state in consistent units.
    q1 = float(row["mujoco_q1_rad"])
    q2 = float(row["mujoco_q2_rad"])
    qd1 = float(row["mujoco_qdot1_rad_s"])
    qd2 = float(row["mujoco_qdot2_rad_s"])
    # Torques in the derived benchmarks are in N*m.
    tau1 = float(row.get("tau1_Nm", row.get("tau0", "0.0")))
    tau2 = float(row.get("tau2_Nm", row.get("tau1", "0.0")))
    return CandidateState(
        label=label,
        source=str(csv_path),
        step=int(float(row["step"])),
        time_s=float(row["time_s"]),
        q1=q1,
        q2=q2,
        qdot1=qd1,
        qdot2=qd2,
        tau1=tau1,
        tau2=tau2,
    )


def _synthetic_state() -> CandidateState:
    return CandidateState(
        label="sanity_q0",
        source="synthetic",
        step=None,
        time_s=0.0,
        q1=0.0,
        q2=0.0,
        qdot1=0.0,
        qdot2=0.0,
        tau1=0.0,
        tau2=0.0,
    )


def _mujoco_qacc(
    xml_path: Path,
    state: CandidateState,
    *,
    damping_scale: float,
    tau_override: tuple[float, float] | None = None,
) -> tuple[np.ndarray, dict[str, object]]:
    model = mujoco.MjModel.from_xml_path(str(xml_path))
    data = mujoco.MjData(model)

    # Apply damping scale variant in-memory.
    original_damping = np.array(model.dof_damping, dtype=float, copy=True)
    model.dof_damping[:] = model.dof_damping[:] * float(damping_scale)
    effective_damping = np.array(model.dof_damping, dtype=float, copy=True)

    # Set state.
    data.qpos[0] = float(state.q1)
    data.qpos[1] = float(state.q2)
    data.qvel[0] = float(state.qdot1)
    data.qvel[1] = float(state.qdot2)

    # Set control (motor shortcut expects ctrl to map to joint torque under gear=1).
    if tau_override is None:
        tau1, tau2 = float(state.tau1), float(state.tau2)
    else:
        tau1, tau2 = float(tau_override[0]), float(tau_override[1])

    if model.nu >= 2:
        data.ctrl[0] = tau1
        data.ctrl[1] = tau2

    mujoco.mj_forward(model, data)

    qacc = np.array([float(data.qacc[0]), float(data.qacc[1])], dtype=float)
    meta: dict[str, object] = {
        "xml": str(xml_path),
        "damping_scale": float(damping_scale),
        "dof_damping_original_first2": [float(x) for x in original_damping[:2].reshape(-1)],
        "dof_damping_effective_first2": [float(x) for x in effective_damping[:2].reshape(-1)],
        "tau_used": [tau1, tau2],
    }
    return qacc, meta


def _bridge_qdd(state: CandidateState, tau: tuple[float, float], params) -> np.ndarray:
    # Import here to ensure repo pathing stays consistent when run from root.
    from example_two_link.matlab_v2_dynamics import compute_forward_dynamics

    q = np.array([state.q1, state.q2], dtype=float)
    qd = np.array([state.qdot1, state.qdot2], dtype=float)
    tau_vec = np.array([float(tau[0]), float(tau[1])], dtype=float)
    qdd = compute_forward_dynamics(q, qd, tau_vec, params)
    return np.array([float(qdd[0]), float(qdd[1])], dtype=float)


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    xml_path = DEFAULT_XML
    csv_path = DEFAULT_CSV

    rows = _load_csv_rows(csv_path)
    states: list[CandidateState] = [
        _state_from_row("step0", csv_path, _row_by_step(rows, 0)),
        _state_from_row("pre_event_470", csv_path, _row_by_step(rows, 470)),
        _state_from_row("event_onset_480", csv_path, _row_by_step(rows, 480)),
        _state_from_row("post_event_486", csv_path, _row_by_step(rows, 486)),
        _synthetic_state(),
    ]

    # Bridge parameters aligned to benchmark default: XML-derived approximation.
    from example_two_link.matlab_v2_params import params_from_mujoco_xml

    params = params_from_mujoco_xml(xml_path)

    # Use MuJoCo dof_damping (scale=1) for manual damping correction candidate b.
    _, meta_scale1 = _mujoco_qacc(xml_path, states[0], damping_scale=1.0)
    b = np.array(meta_scale1["dof_damping_effective_first2"], dtype=float)

    records: list[dict[str, object]] = []
    mujoco_meta: dict[str, object] = {
        "scale1_probe": meta_scale1,
        "b_used_first2": [float(x) for x in b.reshape(-1)],
    }

    for st in states:
        qdot = np.array([st.qdot1, st.qdot2], dtype=float)
        tau = (float(st.tau1), float(st.tau2))
        tau_eff = (float(tau[0] - b[0] * qdot[0]), float(tau[1] - b[1] * qdot[1]))

        # Variant 1: MuJoCo damping 1.0 vs bridge no damping
        mj_qacc_1, _ = _mujoco_qacc(xml_path, st, damping_scale=1.0)
        br_qdd_1 = _bridge_qdd(st, tau, params)
        records.append(
            {
                "state": st.label,
                "variant": "mj_damp1_vs_bridge_no_damp",
                "mujoco_qacc1": float(mj_qacc_1[0]),
                "mujoco_qacc2": float(mj_qacc_1[1]),
                "bridge_qdd1": float(br_qdd_1[0]),
                "bridge_qdd2": float(br_qdd_1[1]),
                "delta1": float(mj_qacc_1[0] - br_qdd_1[0]),
                "delta2": float(mj_qacc_1[1] - br_qdd_1[1]),
            }
        )

        # Variant 2: MuJoCo damping 0.0 vs bridge no damping
        mj_qacc_0, _ = _mujoco_qacc(xml_path, st, damping_scale=0.0)
        br_qdd_0 = _bridge_qdd(st, tau, params)
        records.append(
            {
                "state": st.label,
                "variant": "mj_damp0_vs_bridge_no_damp",
                "mujoco_qacc1": float(mj_qacc_0[0]),
                "mujoco_qacc2": float(mj_qacc_0[1]),
                "bridge_qdd1": float(br_qdd_0[0]),
                "bridge_qdd2": float(br_qdd_0[1]),
                "delta1": float(mj_qacc_0[0] - br_qdd_0[0]),
                "delta2": float(mj_qacc_0[1] - br_qdd_0[1]),
            }
        )

        # Variant 3: MuJoCo damping 1.0 vs bridge with manual damping correction tau_eff = tau - b*qdot
        mj_qacc_1b, _ = _mujoco_qacc(xml_path, st, damping_scale=1.0)
        br_qdd_1b = _bridge_qdd(st, tau_eff, params)
        records.append(
            {
                "state": st.label,
                "variant": "mj_damp1_vs_bridge_manual_tau_eff",
                "mujoco_qacc1": float(mj_qacc_1b[0]),
                "mujoco_qacc2": float(mj_qacc_1b[1]),
                "bridge_qdd1": float(br_qdd_1b[0]),
                "bridge_qdd2": float(br_qdd_1b[1]),
                "delta1": float(mj_qacc_1b[0] - br_qdd_1b[0]),
                "delta2": float(mj_qacc_1b[1] - br_qdd_1b[1]),
                "tau_eff1": float(tau_eff[0]),
                "tau_eff2": float(tau_eff[1]),
            }
        )

    # Write derived outputs.
    (out_dir / "states_used.json").write_text(
        json.dumps([asdict(s) for s in states], indent=2)
    )
    (out_dir / "mujoco_meta.json").write_text(json.dumps(mujoco_meta, indent=2))

    out_csv = out_dir / "acceleration_comparison.csv"
    fieldnames_set: set[str] = set()
    for rec in records:
        fieldnames_set.update(rec.keys())
    fieldnames = sorted(fieldnames_set)
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(records)

    print(f"Wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

