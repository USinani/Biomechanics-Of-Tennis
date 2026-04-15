#!/usr/bin/env python3
"""Validate MATLAB_v2 dynamics bridge against MuJoCo state snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from example_two_link.matlab_v2_dynamics import (  # noqa: E402
    compute_forward_dynamics,
    compute_inverse_dynamics,
    two_link_tennis_model,
)
from example_two_link.matlab_v2_params import (  # noqa: E402
    default_matlab_v2_params,
    params_from_mujoco_xml,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, default=ROOT / "example_two_link" / "two_link_arm.xml")
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--param-source",
        choices=("matlab_default", "from_xml"),
        default="matlab_default",
        help="Choose dynamics parameters for bridge computations.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "example_two_link" / "metrics" / "bridge_validation.json",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    model = mujoco.MjModel.from_xml_path(str(args.xml))
    data = mujoco.MjData(model)
    dt = model.opt.timestep

    params = (
        default_matlab_v2_params()
        if args.param_source == "matlab_default"
        else params_from_mujoco_xml(args.xml)
    )

    qdd_err = []
    inv_fwd_err = []
    min_eigs = []

    for _ in range(args.samples):
        q = rng.uniform(low=np.array([-0.8, 0.1]), high=np.array([0.8, 1.2]))
        qd = rng.uniform(low=-4.0, high=4.0, size=2)
        tau = rng.uniform(low=-40.0, high=40.0, size=2)

        # Bridge predictions
        M, C, G, _ = two_link_tennis_model(q, qd, params)
        qdd_bridge = compute_forward_dynamics(q, qd, tau, params)
        tau_back = compute_inverse_dynamics(q, qd, qdd_bridge, params)

        # MuJoCo one-step acceleration estimate
        data.qpos[:2] = q
        data.qvel[:2] = qd
        data.ctrl[:2] = tau
        mujoco.mj_forward(model, data)
        qd0 = data.qvel[:2].copy()
        mujoco.mj_step(model, data)
        qd1 = data.qvel[:2].copy()
        qdd_mj = (qd1 - qd0) / dt

        qdd_err.append(float(np.linalg.norm(qdd_bridge - qdd_mj)))
        inv_fwd_err.append(float(np.linalg.norm(tau_back - tau)))
        min_eigs.append(float(np.min(np.linalg.eigvals(M).real)))

    summary = {
        "xml": str(args.xml),
        "param_source": args.param_source,
        "params": params.__dict__ if hasattr(params, "__dict__") else {},
        "samples": args.samples,
        "seed": args.seed,
        "qdd_error_l2_mean": float(np.mean(qdd_err)),
        "qdd_error_l2_std": float(np.std(qdd_err)),
        "inv_fwd_tau_residual_mean": float(np.mean(inv_fwd_err)),
        "inv_fwd_tau_residual_std": float(np.std(inv_fwd_err)),
        "mass_matrix_min_eig_min": float(np.min(min_eigs)),
        "mass_matrix_min_eig_mean": float(np.mean(min_eigs)),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        json.dump(summary, f, indent=2)

    print("Bridge validation summary:")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.6f}")
        else:
            print(f"  {k}: {v}")
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()

