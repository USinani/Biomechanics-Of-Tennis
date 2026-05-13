#!/usr/bin/env python3
"""
Derived one-step probe: compare MuJoCo qacc vs bridge qdd under two gravity sign modes.

Outputs are written ONLY under:
  runs/diagnostics/parity_gravity_sign_probe/one_step/
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

XML = ROOT / "example_two_link" / "two_link_arm.xml"
CSV_500 = (
    ROOT
    / "runs"
    / "diagnostics"
    / "parity_500step_probe"
    / "swing_benchmark_timeseries_500.csv"
)


@dataclass(frozen=True)
class State:
    state: str
    step: int | None
    time_s: float
    q1: float
    q2: float
    qdot1: float
    qdot2: float
    tau1: float
    tau2: float


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def _row_by_step(rows: list[dict[str, str]], step: int) -> dict[str, str]:
    for r in rows:
        if int(float(r["step"])) == int(step):
            return r
    raise KeyError(f"Missing step={step} in {CSV_500}")


def _state_from_row(label: str, row: dict[str, str]) -> State:
    return State(
        state=label,
        step=int(float(row["step"])),
        time_s=float(row["time_s"]),
        q1=float(row["mujoco_q1_rad"]),
        q2=float(row["mujoco_q2_rad"]),
        qdot1=float(row["mujoco_qdot1_rad_s"]),
        qdot2=float(row["mujoco_qdot2_rad_s"]),
        tau1=float(row.get("tau1_Nm", "0.0")),
        tau2=float(row.get("tau2_Nm", "0.0")),
    )


def _state_q00() -> State:
    return State(
        state="q00",
        step=None,
        time_s=0.0,
        q1=0.0,
        q2=0.0,
        qdot1=0.0,
        qdot2=0.0,
        tau1=0.0,
        tau2=0.0,
    )


def _mujoco_qacc(model: mujoco.MjModel, data: mujoco.MjData, st: State) -> np.ndarray:
    data.qpos[0] = float(st.q1)
    data.qpos[1] = float(st.q2)
    data.qvel[0] = float(st.qdot1)
    data.qvel[1] = float(st.qdot2)
    if model.nu >= 2:
        data.ctrl[0] = float(st.tau1)
        data.ctrl[1] = float(st.tau2)
    mujoco.mj_forward(model, data)
    return np.array([float(data.qacc[0]), float(data.qacc[1])], dtype=float)


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = _read_csv_rows(CSV_500)
    states = [
        _state_q00(),
        _state_from_row("step0", _row_by_step(rows, 0)),
        _state_from_row("step470", _row_by_step(rows, 470)),
        _state_from_row("step480", _row_by_step(rows, 480)),
        _state_from_row("step486", _row_by_step(rows, 486)),
    ]

    from example_two_link.matlab_v2_params import params_from_mujoco_xml
    from example_two_link.matlab_v2_dynamics import compute_forward_dynamics

    params = params_from_mujoco_xml(XML)

    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)

    recs: list[dict[str, object]] = []
    for st in states:
        mj_qacc = _mujoco_qacc(model, data, st)
        q = np.array([st.q1, st.q2], dtype=float)
        qd = np.array([st.qdot1, st.qdot2], dtype=float)
        tau = np.array([st.tau1, st.tau2], dtype=float)

        br_def = compute_forward_dynamics(q, qd, tau, params, gravity_sign="default")
        br_mj = compute_forward_dynamics(q, qd, tau, params, gravity_sign="mujoco")
        recs.append(
            {
                "state": st.state,
                "mujoco_qacc1": float(mj_qacc[0]),
                "mujoco_qacc2": float(mj_qacc[1]),
                "bridge_default_qdd1": float(br_def[0]),
                "bridge_default_qdd2": float(br_def[1]),
                "bridge_mujoco_sign_qdd1": float(br_mj[0]),
                "bridge_mujoco_sign_qdd2": float(br_mj[1]),
            }
        )

    # Write outputs.
    (out_dir / "states_used.json").write_text(json.dumps([asdict(s) for s in states], indent=2))
    out_csv = out_dir / "gravity_sign_one_step.csv"
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)

    print(f"Wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

