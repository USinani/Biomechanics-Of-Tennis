#!/usr/bin/env python3
"""
Evaluate a trained SAC policy on the two-link arm.

Fixed evaluation: 10 rollouts, seeds 0,1,2,3,4 (2 per seed), up to 100 steps per episode.
Saves metrics to example_two_link/metrics/eval_<run_id>.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from stable_baselines3 import SAC

from arm_env import ArmSwingEnv
from example_two_link.export_unity_txt import write_rollout_csv, write_rollout_txt
from example_two_link.matlab_v2_dynamics import compute_forward_dynamics, compute_inverse_dynamics
from example_two_link.matlab_v2_params import default_matlab_v2_params, params_from_mujoco_xml

MJCF_PATH = ROOT / "example_two_link" / "two_link_arm.xml"
EVAL_SEEDS = [0, 1, 2, 3, 4]
EVAL_EPISODES_PER_SEED = 2  # 10 total rollouts
EVAL_MAX_STEPS = 100


def run_episode(
    env: ArmSwingEnv,
    model: SAC,
    seed: int,
    export_episode_id: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    obs, _ = env.reset(seed=seed)
    total_reward = 0.0
    steps = 0
    info_last = {}
    trajectory_rows: list[dict[str, Any]] = []
    for _ in range(EVAL_MAX_STEPS):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        steps += 1
        info_last = info
        if export_episode_id is not None:
            hand = env.data.site_xpos[env.hand_site].copy()
            q = env.data.qpos[:2].copy()
            qd = env.data.qvel[:2].copy()
            trajectory_rows.append(
                {
                    "episode": export_episode_id,
                    "step": steps,
                    "time_s": float(steps / env.ctrl_rate),
                    "q1": float(q[0]),
                    "q2": float(q[1]),
                    "qd1": float(qd[0]),
                    "qd2": float(qd[1]),
                    "tau1": float(action[0]),
                    "tau2": float(action[1]),
                    "prior_tau1": float(info.get("prior_action", np.zeros(2))[0]),
                    "prior_tau2": float(info.get("prior_action", np.zeros(2))[1]),
                    "applied_tau1": float(info.get("applied_action", action)[0]),
                    "applied_tau2": float(info.get("applied_action", action)[1]),
                    "hand_x": float(hand[0]),
                    "hand_y": float(hand[1]),
                    "hand_z": float(hand[2]),
                    "target_x": float(info.get("target", np.zeros(3))[0]),
                    "target_y": float(info.get("target", np.zeros(3))[1]),
                    "target_z": float(info.get("target", np.zeros(3))[2]),
                    "reward": float(reward),
                    "dist": float(info.get("dist", -1.0)),
                }
            )
        if terminated or truncated:
            break
    result = {
        "episode_return": total_reward,
        "steps": steps,
        "final_dist": float(info_last.get("dist", -1)),
        "max_torque": float(info_last.get("max_torque", -1)),
        "max_speed": float(info_last.get("max_speed", -1)),
        "success_steps": int(info_last.get("success_steps", 0)),
        "seed": seed,
    }
    return result, trajectory_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True, help="Path to SAC checkpoint (without .zip)")
    parser.add_argument("--seeds", type=str, default="0,1,2,3,4", help="Comma-separated seeds")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path")
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
        help="Target placement mode for evaluation episodes.",
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
        "--export-trajectory",
        action="store_true",
        help="Export per-step rollout trajectory to TXT/CSV for Unity replay.",
    )
    parser.add_argument(
        "--bridge-diagnostics",
        action="store_true",
        help="Compute bridge forward/inverse residual summary during eval.",
    )
    parser.add_argument(
        "--param-source",
        choices=("matlab_default", "from_xml"),
        default="matlab_default",
        help="Parameter source for bridge diagnostics.",
    )
    args = parser.parse_args()

    seeds = [int(s.strip()) for s in args.seeds.split(",")]
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

    results: list[dict[str, Any]] = []
    trajectory_rows_all: list[dict[str, Any]] = []
    bridge_residuals: list[float] = []
    params = (
        default_matlab_v2_params()
        if args.param_source == "matlab_default"
        else params_from_mujoco_xml(MJCF_PATH)
    )
    episode_id = 0
    for seed in seeds:
        for ep in range(EVAL_EPISODES_PER_SEED):
            ep_seed = seed * 1000 + ep  # distinct episode seeds
            r, rows = run_episode(
                env,
                model,
                ep_seed,
                export_episode_id=episode_id if args.export_trajectory else None,
            )
            results.append(r)
            trajectory_rows_all.extend(rows)
            if args.bridge_diagnostics and rows:
                last = rows[-1]
                q = np.array([last["q1"], last["q2"]], dtype=float)
                qd = np.array([last["qd1"], last["qd2"]], dtype=float)
                tau = np.array([last["applied_tau1"], last["applied_tau2"]], dtype=float)
                qdd = compute_forward_dynamics(q, qd, tau, params)
                tau_back = compute_inverse_dynamics(q, qd, qdd, params)
                bridge_residuals.append(float(np.linalg.norm(tau_back - tau)))
            episode_id += 1

    env.close()

    returns = [x["episode_return"] for x in results]
    dists = [x["final_dist"] for x in results]
    success = sum(1 for x in results if x["success_steps"] >= 5)  # reached and held
    success_rate = success / len(results)

    summary = {
        "checkpoint": str(ckpt),
        "action_mode": args.action_mode,
        "target_mode": args.target_mode,
        "controller_param_source": args.controller_param_source,
        "seeds": seeds,
        "episodes_per_seed": EVAL_EPISODES_PER_SEED,
        "n_episodes": len(results),
        "mean_return": float(np.mean(returns)),
        "std_return": float(np.std(returns)),
        "mean_final_dist": float(np.mean(dists)),
        "std_final_dist": float(np.std(dists)),
        "success_rate": success_rate,
        "episodes": results,
    }
    if args.bridge_diagnostics and bridge_residuals:
        summary["bridge_tau_residual_mean"] = float(np.mean(bridge_residuals))
        summary["bridge_tau_residual_std"] = float(np.std(bridge_residuals))
        summary["bridge_param_source"] = args.param_source

    out_dir = ROOT / "example_two_link" / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out or out_dir / f"eval_{ckpt.stem}.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    export_paths = {}
    if args.export_trajectory and trajectory_rows_all:
        export_dir = ROOT / "example_two_link" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        base = export_dir / f"trajectory_{ckpt.stem}"
        csv_path = write_rollout_csv(trajectory_rows_all, base.with_suffix(".csv"))
        txt_path = write_rollout_txt(trajectory_rows_all, base.with_suffix(".txt"))
        export_paths["csv"] = str(csv_path)
        export_paths["txt"] = str(txt_path)
        raw_json = base.with_suffix(".json")
        with raw_json.open("w") as f:
            json.dump(trajectory_rows_all, f, indent=2)
        export_paths["json"] = str(raw_json)

    print("Evaluation summary:")
    print(f"  Mean return: {summary['mean_return']:.2f} ± {summary['std_return']:.2f}")
    print(f"  Mean final dist (m): {summary['mean_final_dist']:.4f} ± {summary['std_final_dist']:.4f}")
    print(f"  Success rate: {success_rate:.2%}")
    if "bridge_tau_residual_mean" in summary:
        print(
            f"  Bridge tau residual: {summary['bridge_tau_residual_mean']:.6f} ± "
            f"{summary['bridge_tau_residual_std']:.6f}"
        )
    print(f"  Saved to {out_path}")
    if export_paths:
        print("  Trajectory exports:")
        for k, v in export_paths.items():
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
