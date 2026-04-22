from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import mujoco
import mujoco.viewer
from stable_baselines3 import SAC

from arm_env import ArmSwingEnv, make_arm_env_from_json


_DEFAULT_CKPT_CANDIDATES = (
    Path(__file__).resolve().parent / "checkpoints" / "sac_two_link_arm",
    Path(__file__).resolve().parent / "sac_two_link_arm",
)


def _resolve_default_checkpoint() -> str:
    for cand in _DEFAULT_CKPT_CANDIDATES:
        if cand.with_suffix(".zip").exists() or cand.exists():
            return str(cand)
    return str(_DEFAULT_CKPT_CANDIDATES[0])


def run_viewer_with_policy(
    model_path: Optional[str] = None,
    use_json_model: bool = False,
    total_sim_time: Optional[float] = None,
) -> None:
    """Run a trained SAC policy in the interactive MuJoCo viewer."""
    if use_json_model:
        env = make_arm_env_from_json()
    else:
        env = ArmSwingEnv()

    if model_path is None:
        model_path = _resolve_default_checkpoint()
    model = SAC.load(model_path)

    ctrl_dt = 1.0 / env.ctrl_rate
    sim_start = time.time()

    with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
        obs, _ = env.reset()
        while viewer.is_running():
            # Optional wall-clock limit
            if total_sim_time is not None and (time.time() - sim_start) > total_sim_time:
                break

            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = env.step(action)

            viewer.sync()

            if terminated or truncated:
                obs, _ = env.reset()

            # Sleep to roughly match control rate in real time
            time.sleep(ctrl_dt)

    env.close()


if __name__ == "__main__":
    run_viewer_with_policy()

