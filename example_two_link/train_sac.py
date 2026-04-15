#!/usr/bin/env python3
"""
Train SAC on the two-link arm environment.

Experiment controls (fixed):
- Seeds: 0,1,2,3,4 (configurable via --seed)
- Training budget: 200k steps (configurable via --steps)
- Model saved to example_two_link/checkpoints/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on path when run via ./run.sh example_two_link/train_sac.py
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from stable_baselines3 import SAC

from arm_env import ArmSwingEnv
from example_two_link.matlab_v2_dynamics import compute_forward_dynamics, compute_inverse_dynamics
from example_two_link.matlab_v2_params import default_matlab_v2_params, params_from_mujoco_xml

# Paths relative to project root
MJCF_PATH = ROOT / "example_two_link" / "two_link_arm.xml"
CHECKPOINT_DIR = ROOT / "example_two_link" / "checkpoints"
DEFAULT_STEPS = 200_000
DEFAULT_SEED = 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="Training timesteps")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--out", type=Path, default=None, help="Checkpoint output path")
    parser.add_argument(
        "--action-mode",
        choices=("torque", "residual"),
        default="torque",
        help="Train either direct torque control or RL residual control on top of the analytical prior.",
    )
    parser.add_argument(
        "--target-mode",
        choices=("fixed", "planar_fixed", "random_planar"),
        default="planar_fixed",
        help="Target placement mode. planar_fixed keeps the original target in-plane.",
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
    parser.add_argument(
        "--bridge-check",
        action="store_true",
        help="Run a quick MATLAB_v2 forward/inverse dynamics consistency check before training.",
    )
    parser.add_argument(
        "--param-source",
        choices=("matlab_default", "from_xml"),
        default="matlab_default",
        help="Parameter source for bridge diagnostics.",
    )
    args = parser.parse_args()

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.out or CHECKPOINT_DIR / f"sac_two_link_{args.action_mode}_seed{args.seed}"
    out_path = out_path.with_suffix("") if out_path.suffix == ".zip" else out_path

    env = ArmSwingEnv(
        mjcf_path=str(MJCF_PATH),
        action_mode=args.action_mode,
        target_mode=args.target_mode,
        residual_limit=args.residual_limit,
        controller_param_source=args.controller_param_source,
    )
    env.reset(seed=args.seed)

    if args.bridge_check:
        params = (
            default_matlab_v2_params()
            if args.param_source == "matlab_default"
            else params_from_mujoco_xml(MJCF_PATH)
        )
        q = env.data.qpos[:2].copy()
        qd = env.data.qvel[:2].copy()
        tau = env.action_space.sample().astype(float)
        qdd = compute_forward_dynamics(q, qd, tau, params)
        tau_back = compute_inverse_dynamics(q, qd, qdd, params)
        residual = float(((tau_back - tau) ** 2).sum() ** 0.5)
        print(f"[bridge-check] tau residual L2: {residual:.6f} (param_source={args.param_source})")

    model = SAC(
        policy="MlpPolicy",
        env=env,
        verbose=1,
        seed=args.seed,
        learning_rate=3e-4,
        buffer_size=200_000,
        batch_size=256,
        gamma=0.99,
        train_freq=1,
        gradient_steps=1,
        tau=0.02,
        target_entropy=-2,
    )

    print(
        f"Training for {args.steps} steps, seed={args.seed}, "
        f"action_mode={args.action_mode}, target_mode={args.target_mode}, checkpoint -> {out_path}"
    )
    model.learn(total_timesteps=args.steps)
    model.save(str(out_path))
    env.close()
    print(f"Saved to {out_path}.zip")


if __name__ == "__main__":
    main()
