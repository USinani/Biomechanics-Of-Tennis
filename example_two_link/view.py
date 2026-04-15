#!/usr/bin/env python3
"""
View a trained SAC policy rollout in the MuJoCo passive viewer.

On macOS, must be run with mjpython (run.sh handles this).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mujoco.viewer
from stable_baselines3 import SAC

from arm_env import ArmSwingEnv

MJCF_PATH = ROOT / "example_two_link" / "two_link_arm.xml"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True, help="Path to SAC checkpoint")
    parser.add_argument("--episodes", type=int, default=3, help="Number of full episodes to show")
    parser.add_argument(
        "--action-mode",
        choices=("torque", "residual"),
        default="torque",
        help="Match the action mode used during training.",
    )
    parser.add_argument(
        "--target-mode",
        choices=("fixed", "planar_fixed", "random_planar"),
        default="planar_fixed",
        help="Target placement mode for viewer rollouts.",
    )
    parser.add_argument(
        "--residual-limit",
        type=float,
        default=20.0,
        help="Residual torque limit used when --action-mode residual.",
    )
    parser.add_argument(
        "--controller-param-source",
        choices=("matlab_default", "from_xml"),
        default="from_xml",
        help="Parameter source for the analytical prior in residual mode.",
    )
    args = parser.parse_args()

    ckpt = Path(args.checkpoint)
    if ckpt.suffix != ".zip" and (ckpt.with_suffix(".zip")).exists():
        ckpt = ckpt.with_suffix(".zip")

    env = ArmSwingEnv(
        mjcf_path=str(MJCF_PATH),
        action_mode=args.action_mode,
        target_mode=args.target_mode,
        residual_limit=args.residual_limit,
        controller_param_source=args.controller_param_source,
    )
    model = SAC.load(str(ckpt))

    ctrl_dt = 1.0 / env.ctrl_rate
    episode = 0

    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        obs, _ = env.reset()
        while viewer.is_running() and episode < args.episodes:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, info = env.step(action)
            viewer.sync()
            time.sleep(ctrl_dt)

            if terminated or truncated:
                episode += 1
                if episode < args.episodes:
                    obs, _ = env.reset()

    env.close()


if __name__ == "__main__":
    main()
