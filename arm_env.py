import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import mujoco
import numpy as np

from example_two_link.matlab_v2_dynamics import compute_inverse_dynamics
from example_two_link.matlab_v2_params import default_matlab_v2_params, params_from_mujoco_xml


ASSET = os.path.join(os.path.dirname(__file__), "mujoco_arm.xml")


class ArmSwingEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(
        self,
        render_mode: Optional[str] = None,
        mjcf_path: Optional[str] = None,
        # Reward weights
        w_dist: float = 2.0,
        w_toward: float = 0.5,
        w_effort: float = 1e-3,
        w_smooth: float = 1e-3,
        w_speed: float = 0.0,
        w_limit: float = 0.05,
        terminal_bonus: float = 0.0,
        # Success / reach-and-hold configuration
        eps_success: float = 0.04,
        n_hold_success: int = 5,
        end_on_success: bool = False,
        # Joint limit barrier margin (radians)
        joint_margin: float = np.deg2rad(5.0),
        # Speed and torque thresholds for penalties / termination
        soft_speed_threshold: float = np.deg2rad(800.0),
        hard_speed_threshold: float = np.deg2rad(1200.0),
        torque_hard_limit: float = 1000.0,
        # Target configuration
        target_mode: str = "planar_fixed",
        # Hybrid controller configuration
        action_mode: str = "torque",
        residual_limit: float = 20.0,
        controller_param_source: str = "from_xml",
        controller_kp: Tuple[float, float] = (80.0, 50.0),
        controller_kd: Tuple[float, float] = (18.0, 12.0),
    ) -> None:
        super().__init__()

        xml_path = mjcf_path if mjcf_path is not None else ASSET
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)

        self.sim_rate = 500  # Hz
        self.ctrl_rate = 50  # Hz
        self.substeps = self.sim_rate // self.ctrl_rate
        self.max_steps = int(2.0 * self.ctrl_rate)

        self.render_mode = render_mode
        self.renderer = mujoco.Renderer(self.model) if render_mode == "human" else None

        self.target_site = self.model.site("target").id
        self.hand_site = self.model.site("hand").id
        self.shoulder_body = self.model.body("shoulder").id
        self.shoulder_pos = self.model.body_pos[self.shoulder_body].copy()
        self.joint_min = self.model.jnt_range[:2, 0].astype(float).copy()
        self.joint_max = self.model.jnt_range[:2, 1].astype(float).copy()
        self.ctrl_low = self.model.actuator_ctrlrange[:2, 0].astype(np.float32).copy()
        self.ctrl_high = self.model.actuator_ctrlrange[:2, 1].astype(np.float32).copy()

        if target_mode not in {"fixed", "planar_fixed", "random_planar"}:
            raise ValueError("target_mode must be one of: fixed, planar_fixed, random_planar")
        if action_mode not in {"torque", "residual"}:
            raise ValueError("action_mode must be one of: torque, residual")
        if controller_param_source not in {"matlab_default", "from_xml"}:
            raise ValueError("controller_param_source must be one of: matlab_default, from_xml")

        self.target_mode = target_mode
        self.action_mode = action_mode
        self.residual_limit = float(residual_limit)
        self.controller_param_source = controller_param_source
        self.controller_kp = np.asarray(controller_kp, dtype=float)
        self.controller_kd = np.asarray(controller_kd, dtype=float)
        self.controller_params = (
            default_matlab_v2_params()
            if controller_param_source == "matlab_default"
            else params_from_mujoco_xml(xml_path)
        )

        self.link_lengths = np.array(
            [self.controller_params.l1, self.controller_params.l2], dtype=float
        )

        obs_dim = 2 * 2 + 2 + 3 + 3 + 3
        if self.action_mode == "residual":
            obs_dim += 4  # desired joints + prior torque
        high = np.ones(obs_dim, dtype=np.float32) * np.inf
        self.observation_space = gym.spaces.Box(-high, high, dtype=np.float32)

        if self.action_mode == "torque":
            action_low = self.ctrl_low
            action_high = self.ctrl_high
        else:
            action_low = np.full(2, -self.residual_limit, dtype=np.float32)
            action_high = np.full(2, self.residual_limit, dtype=np.float32)
        self.action_space = gym.spaces.Box(low=action_low, high=action_high, shape=(2,), dtype=np.float32)

        # reward weights and thresholds
        self.w_dist = w_dist
        self.w_toward = w_toward
        self.w_effort = w_effort
        self.w_smooth = w_smooth
        self.w_speed = w_speed
        self.w_limit = w_limit
        self.terminal_bonus = terminal_bonus

        self.eps_success = eps_success
        self.n_hold_success = n_hold_success
        self.end_on_success = end_on_success
        self.joint_margin = joint_margin
        self.soft_speed_threshold = soft_speed_threshold
        self.hard_speed_threshold = hard_speed_threshold
        self.torque_hard_limit = torque_hard_limit

        self._prev_action = np.zeros(2, dtype=float)
        self._success_steps = 0
        self._last_q_des = np.zeros(2, dtype=float)
        self._last_prior_action = np.zeros(2, dtype=float)

    def _current_target(self) -> np.ndarray:
        return self.data.site_xpos[self.target_site].copy()

    def _set_target(self, target_world: np.ndarray) -> None:
        self.model.site_pos[self.target_site] = np.asarray(target_world, dtype=float)
        mujoco.mj_forward(self.model, self.data)

    def _forward_kinematics(self, q: np.ndarray) -> np.ndarray:
        l1, l2 = self.link_lengths
        q1, q2 = q
        x = l1 * np.cos(q1) + l2 * np.cos(q1 + q2)
        z = -(l1 * np.sin(q1) + l2 * np.sin(q1 + q2))
        return self.shoulder_pos + np.array([x, 0.0, z], dtype=float)

    def _sample_target(self) -> np.ndarray:
        if self.target_mode == "fixed":
            return self.model.site_pos[self.target_site].copy()
        if self.target_mode == "planar_fixed":
            target = self.model.site_pos[self.target_site].copy()
            target[1] = self.shoulder_pos[1]
            return target

        q_target = np.array(
            [
                self.np_random.uniform(low=np.deg2rad(-70.0), high=np.deg2rad(70.0)),
                self.np_random.uniform(low=np.deg2rad(15.0), high=np.deg2rad(135.0)),
            ],
            dtype=float,
        )
        return self._forward_kinematics(q_target)

    def _solve_planar_ik(self, target_world: np.ndarray) -> np.ndarray:
        l1, l2 = self.link_lengths
        rel = np.asarray(target_world, dtype=float) - self.shoulder_pos
        x = float(rel[0])
        y = float(-rel[2])

        r2 = x * x + y * y
        cos_q2 = (r2 - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)
        cos_q2 = float(np.clip(cos_q2, -1.0, 1.0))
        q2 = float(np.arccos(cos_q2))
        k1 = l1 + l2 * np.cos(q2)
        k2 = l2 * np.sin(q2)
        q1 = float(np.arctan2(y, x) - np.arctan2(k2, k1))
        q_des = np.array([q1, q2], dtype=float)
        return np.clip(q_des, self.joint_min, self.joint_max)

    def _hybrid_prior(self, q: np.ndarray, qd: np.ndarray, target_world: np.ndarray) -> np.ndarray:
        q_des = self._solve_planar_ik(target_world)
        qdd_des = self.controller_kp * (q_des - q) - self.controller_kd * qd
        prior = compute_inverse_dynamics(q, qd, qdd_des, self.controller_params)
        self._last_q_des = q_des
        self._last_prior_action = prior
        return prior

    def _obs(self) -> np.ndarray:
        q = self.data.qpos[:2].copy()
        qd = self.data.qvel[:2].copy()
        hand = self.data.site_xpos[self.hand_site].copy()
        target = self._current_target()
        delta = target - hand
        obs_parts = [np.sin(q), np.cos(q), qd, hand, target, delta]
        if self.action_mode == "residual":
            obs_parts.extend([self._last_q_des, self._last_prior_action])
        return np.concatenate(obs_parts).astype(np.float32)

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        target = self._sample_target()
        self._set_target(target)
        self.data.qpos[:2] = self.np_random.uniform(low=[-0.2, 0.3], high=[0.2, 1.0])
        self.data.qvel[:2] = 0
        self._last_q_des = self._solve_planar_ik(target)
        self._last_prior_action = np.zeros(2, dtype=float)
        mujoco.mj_forward(self.model, self.data)
        self.steps = 0
        self._prev_action[...] = 0.0
        self._success_steps = 0
        return self._obs(), {"target": target, "action_mode": self.action_mode, "target_mode": self.target_mode}

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        policy_action = np.clip(action, self.action_space.low, self.action_space.high).astype(float)
        q = self.data.qpos[:2].copy()
        qd = self.data.qvel[:2].copy()
        target = self._current_target()
        prior_action = np.zeros(2, dtype=float)
        applied_action = policy_action.copy()
        if self.action_mode == "residual":
            prior_action = self._hybrid_prior(q, qd, target)
            applied_action = prior_action + policy_action
        applied_action = np.clip(applied_action, self.ctrl_low, self.ctrl_high)

        for _ in range(self.substeps):
            self.data.ctrl[:2] = applied_action
            mujoco.mj_step(self.model, self.data)
        self.steps += 1

        obs = self._obs()
        delta = obs[12:15]
        dist = float(np.linalg.norm(delta))
        if hasattr(self.data, "site_xvelp"):
            hand_vel = self.data.site_xvelp[self.hand_site].copy()
        else:
            hand_vel = np.zeros(3, dtype=float)
        toward = 0.0 if dist < 1e-6 else float(np.dot(hand_vel, -delta / dist))

        r_dist = -self.w_dist * dist
        r_toward = self.w_toward * toward
        r_effort = -self.w_effort * float(np.sum(np.square(applied_action)))
        delta_tau = applied_action - self._prev_action
        r_smooth = -self.w_smooth * float(np.sum(np.square(delta_tau)))

        qd = self.data.qvel[:2].copy()
        excess_speed = np.maximum(0.0, np.abs(qd) - self.soft_speed_threshold)
        r_speed = -self.w_speed * float(np.sum(np.square(excess_speed)))

        q = self.data.qpos[:2].copy()
        upper_violation = np.maximum(0.0, q - (self.joint_max - self.joint_margin))
        lower_violation = np.maximum(0.0, (self.joint_min + self.joint_margin) - q)
        r_limit = -self.w_limit * float(
            np.sum(np.square(upper_violation) + np.square(lower_violation))
        )

        r_terminal = 0.0
        success_now = dist < self.eps_success
        if success_now:
            self._success_steps += 1
            if self._success_steps >= self.n_hold_success and self.terminal_bonus != 0.0:
                r_terminal += self.terminal_bonus
        else:
            self._success_steps = 0

        reward = r_dist + r_toward + r_effort + r_smooth + r_speed + r_limit + r_terminal
        self._prev_action = applied_action.copy()

        terminated = False
        truncated = self.steps >= self.max_steps

        safety_terminated = False
        safety_reason = ""

        if (
            self.end_on_success
            and self._success_steps >= self.n_hold_success
            and self.terminal_bonus != 0.0
        ):
            terminated = True
            safety_reason = "success"

        max_speed = float(np.max(np.abs(qd))) if qd.size else 0.0
        max_torque = float(np.max(np.abs(applied_action))) if applied_action.size else 0.0
        if max_speed > self.hard_speed_threshold:
            terminated = True
            safety_terminated = True
            safety_reason = "hard_speed_limit"
        elif max_torque > self.torque_hard_limit:
            terminated = True
            safety_terminated = True
            safety_reason = "torque_limit"

        if not np.isfinite(obs).all():
            terminated = True
            safety_terminated = True
            safety_reason = safety_reason or "non_finite_observation"
        info: Dict[str, Any] = {
            "dist": dist,
            "target": target,
            "hand_speed": float(np.linalg.norm(hand_vel)),
            "r_dist": r_dist,
            "r_toward": r_toward,
            "r_effort": r_effort,
            "r_smooth": r_smooth,
            "r_speed": r_speed,
            "r_limit": r_limit,
            "r_terminal": r_terminal,
            "success_steps": self._success_steps,
            "q": q,
            "qd": qd,
            "policy_action": policy_action,
            "prior_action": prior_action,
            "applied_action": applied_action,
            "q_des": self._last_q_des.copy(),
            "upper_violation": upper_violation,
            "lower_violation": lower_violation,
            "max_speed": max_speed,
            "max_torque": max_torque,
            "safety_terminated": safety_terminated,
            "safety_reason": safety_reason,
            "action_mode": self.action_mode,
            "target_mode": self.target_mode,
            "controller_param_source": self.controller_param_source,
        }
        return obs, reward, terminated, truncated, info

    def render(self):
        if self.renderer is None:
            return None
        self.renderer.update_scene(self.data)
        return self.renderer.render()

    def close(self) -> None:
        if self.renderer:
            self.renderer.close()
            self.renderer = None


def make_arm_env_from_json(
    model_params_path: str = "model_params.json",
    mjcf_out_path: str = "mujoco_arm_from_json.xml",
    **env_kwargs: Any,
) -> ArmSwingEnv:
    """Helper to generate MJCF from JSON (if needed) and construct ArmSwingEnv."""
    from generate_mjcf_from_json import generate_mjcf

    params_path = Path(model_params_path)
    out_path = Path(mjcf_out_path)

    import json

    with params_path.open("r") as f:
        model_params = json.load(f)

    xml = generate_mjcf(model_params)
    with out_path.open("w") as f:
        f.write(xml)

    return ArmSwingEnv(mjcf_path=str(out_path), **env_kwargs)
