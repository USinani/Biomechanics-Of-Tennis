from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Any

from stable_baselines3 import SAC

from arm_env import ArmSwingEnv


def evaluate_policy(env: ArmSwingEnv, model: SAC, n_steps: int = 100) -> Dict[str, Any]:
    obs, _ = env.reset()
    info: Dict[str, Any] = {}
    episode_reward = 0.0
    for _ in range(n_steps):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        episode_reward += float(reward)
        if terminated or truncated:
            break
    summary: Dict[str, Any] = {
        "episode_reward": episode_reward,
        "final_dist": info.get("dist"),
        "max_speed": info.get("max_speed"),
        "max_torque": info.get("max_torque"),
        "success_steps": info.get("success_steps"),
        "safety_terminated": info.get("safety_terminated"),
        "safety_reason": info.get("safety_reason"),
    }
    # Include reward components if present
    for key in ("r_dist", "r_toward", "r_effort", "r_smooth", "r_speed", "r_limit", "r_terminal"):
        if key in info:
            summary[key] = info[key]
    return summary


def main() -> None:
    env = ArmSwingEnv()
    model = SAC(
        policy="MlpPolicy",
        env=env,
        verbose=1,
        learning_rate=3e-4,
        buffer_size=200_000,
        batch_size=256,
        gamma=0.99,
        train_freq=1,
        gradient_steps=1,
        tau=0.02,
        target_entropy=-2,  # for 2D action
    )
    model.learn(total_timesteps=300_000)
    model.save("sac_two_link_arm")

    summary = evaluate_policy(env, model, n_steps=100)

    # Print a concise diagnostic summary
    print("Evaluation summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # Save to CSV for later plotting / analysis
    out_path = Path("eval_summary.csv")
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    env.close()


if __name__ == "__main__":
    main()
