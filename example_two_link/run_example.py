#!/usr/bin/env python3
"""
Run the two-link arm model in MuJoCo.

Loads the MJCF model, optionally saves a compiled MJB for faster loading,
and launches the passive viewer for interactive simulation.

Modeling docs: https://mujoco.readthedocs.io/en/stable/modeling.html
"""
import argparse
import os
from pathlib import Path

import mujoco
import mujoco.viewer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run two-link arm in MuJoCo viewer")
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(__file__).parent / "two_link_arm.xml",
        help="Path to MJCF model file",
    )
    parser.add_argument(
        "--save-mjb",
        action="store_true",
        help="Save compiled model as MJB (faster loading next time)",
    )
    parser.add_argument(
        "--zero-torque",
        action="store_true",
        help="Run with zero control (gravity drop / passive swing)",
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Load from XML (Modeling > Loading models)
    print(f"Loading {model_path}...")
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    # Optional: save as MJB for faster loading (Modeling > Saving models)
    if args.save_mjb:
        mjb_path = model_path.with_suffix(".mjb")
        mujoco.mj_saveModel(model, str(mjb_path))
        print(f"Saved compiled model to {mjb_path}")

    print(f"Model: nq={model.nq} nv={model.nv} nu={model.nu}")
    print("Close the viewer window to exit.")
    if args.zero_torque:
        print("Running with zero torque (passive dynamics).")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            if args.zero_torque:
                data.ctrl[:] = 0.0
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
