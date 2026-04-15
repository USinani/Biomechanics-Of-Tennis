from __future__ import annotations

import argparse
from typing import Dict, Any

from stable_baselines3 import SAC

from arm_env import ArmSwingEnv


def run_single_experiment(
    total_timesteps: int,
    env_kwargs: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    env = ArmSwingEnv(**(env_kwargs or {}))
    model = SAC("MlpPolicy", env=env, verbose=1)

    model.learn(total_timesteps=total_timesteps)
    summary: Dict[str, Any] = {}

    # Quick evaluation rollout
    obs, _ = env.reset()
    info: Dict[str, Any] = {}
    episode_reward = 0.0
    for _ in range(100):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, term, trunc, info = env.step(action)
        episode_reward += float(reward)
        if term or trunc:
            break

    summary["episode_reward"] = episode_reward
    summary["final_dist"] = info.get("dist")
    summary["max_speed"] = info.get("max_speed")
    summary["max_torque"] = info.get("max_torque")
    summary["safety_terminated"] = info.get("safety_terminated")
    summary["safety_reason"] = info.get("safety_reason")
    for key in ("r_dist", "r_toward", "r_effort", "r_smooth", "r_speed", "r_limit", "r_terminal"):
        if key in info:
            summary[key] = info[key]

    env.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run a small ablation ladder over reward terms.",
    )
    args = parser.parse_args()

    if not args.ablation:
        summary = run_single_experiment(total_timesteps=10_000)
        print("Quick run summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        return

    # Simple ablation ladder: progressively enable penalties
    configs = [
        {"name": "task_only", "env_kwargs": {"w_effort": 0.0, "w_smooth": 0.0, "w_speed": 0.0, "w_limit": 0.0}},
        {"name": "task_torque", "env_kwargs": {"w_smooth": 0.0, "w_speed": 0.0, "w_limit": 0.0}},
        {"name": "task_torque_smooth", "env_kwargs": {"w_speed": 0.0, "w_limit": 0.0}},
        {"name": "full", "env_kwargs": {}},
    ]

    for cfg in configs:
        print(f"\n=== Running ablation setting: {cfg['name']} ===")
        summary = run_single_experiment(total_timesteps=5_000, env_kwargs=cfg["env_kwargs"])
        for k, v in summary.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

