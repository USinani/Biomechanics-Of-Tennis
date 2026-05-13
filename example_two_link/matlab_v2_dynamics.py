#!/usr/bin/env python3
"""Python port of MATLAB_v2 two-link tennis dynamics."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Mapping, Any

import numpy as np


REQUIRED_FIELDS = ("l1", "l2", "m1", "m2", "lc1", "lc2", "I1", "I2", "g")

def _gravity_sign_mode_to_factor(mode: str) -> float:
    m = (mode or "").lower().strip()
    if m == "default":
        return 1.0
    if m == "mujoco":
        # Opt-in hypothesis: flip generalized gravity sign to match MuJoCo convention.
        return -1.0
    raise ValueError(
        f"Unknown gravity sign mode: {mode!r} (expected 'default' or 'mujoco')"
    )


def _as_param_dict(params: Mapping[str, Any] | Any) -> dict[str, float]:
    if is_dataclass(params):
        p = asdict(params)
    elif isinstance(params, Mapping):
        p = dict(params)
    else:
        raise TypeError("params must be mapping or dataclass-like object")
    missing = [k for k in REQUIRED_FIELDS if k not in p]
    if missing:
        raise ValueError(f"Missing required parameter fields: {missing}")
    return {k: float(p[k]) for k in REQUIRED_FIELDS}


def _vec2(name: str, x: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    arr = np.asarray(x, dtype=float).reshape(-1)
    if arr.size != 2:
        raise ValueError(f"{name} must have exactly 2 elements")
    return arr


def two_link_tennis_model(
    theta: np.ndarray | list[float] | tuple[float, ...],
    theta_dot: np.ndarray | list[float] | tuple[float, ...],
    params: Mapping[str, Any] | Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (M, C, G, B) matching MATLAB_v2 equations."""
    th = _vec2("theta", theta)
    thd = _vec2("theta_dot", theta_dot)
    p = _as_param_dict(params)

    l1 = p["l1"]
    m1, m2 = p["m1"], p["m2"]
    lc1, lc2 = p["lc1"], p["lc2"]
    I1, I2 = p["I1"], p["I2"]
    g = p["g"]

    theta1, theta2 = th
    theta1_dot, theta2_dot = thd

    c1 = np.cos(theta1)
    c2 = np.cos(theta2)
    c12 = np.cos(theta1 + theta2)
    s2 = np.sin(theta2)

    alpha = I1 + I2 + m1 * lc1**2 + m2 * (l1**2 + lc2**2)
    beta = m2 * l1 * lc2
    delta = I2 + m2 * lc2**2

    M11 = alpha + 2.0 * beta * c2
    M12 = delta + beta * c2
    M22 = delta
    M = np.array([[M11, M12], [M12, M22]], dtype=float)

    h = -m2 * l1 * lc2 * s2
    C11 = h * theta2_dot
    C12 = h * (theta1_dot + theta2_dot)
    C21 = -h * theta1_dot
    C = np.array([[C11, C12], [C21, 0.0]], dtype=float)

    G1 = (m1 * lc1 + m2 * l1) * g * c1 + m2 * lc2 * g * c12
    G2 = m2 * lc2 * g * c12
    G = np.array([G1, G2], dtype=float)

    B = np.eye(2, dtype=float)
    return M, C, G, B


def compute_forward_dynamics(
    theta: np.ndarray | list[float] | tuple[float, ...],
    theta_dot: np.ndarray | list[float] | tuple[float, ...],
    tau: np.ndarray | list[float] | tuple[float, ...],
    params: Mapping[str, Any] | Any,
    *,
    gravity_sign: str = "default",
) -> np.ndarray:
    """Compute qdd from q, qd, tau."""
    th = _vec2("theta", theta)
    thd = _vec2("theta_dot", theta_dot)
    tq = _vec2("tau", tau)
    M, C, G, _ = two_link_tennis_model(th, thd, params)
    gfac = _gravity_sign_mode_to_factor(gravity_sign)
    rhs = tq - C @ thd - (gfac * G)
    return np.linalg.solve(M, rhs)


def compute_inverse_dynamics(
    theta: np.ndarray | list[float] | tuple[float, ...],
    theta_dot: np.ndarray | list[float] | tuple[float, ...],
    theta_ddot: np.ndarray | list[float] | tuple[float, ...],
    params: Mapping[str, Any] | Any,
) -> np.ndarray:
    """Compute tau from q, qd, qdd."""
    th = _vec2("theta", theta)
    thd = _vec2("theta_dot", theta_dot)
    thdd = _vec2("theta_ddot", theta_ddot)
    M, C, G, _ = two_link_tennis_model(th, thd, params)
    return M @ thdd + C @ thd + G


def _state_derivative(
    x: np.ndarray,
    tau: np.ndarray,
    params: Mapping[str, Any] | Any,
    *,
    gravity_sign: str,
) -> np.ndarray:
    """Continuous-time derivative for x=[q1,q2,qd1,qd2]."""
    x = np.asarray(x, dtype=float).reshape(-1)
    if x.size != 4:
        raise ValueError("state x must have 4 elements: [q1,q2,qd1,qd2]")
    q = x[:2]
    qd = x[2:]
    qdd = compute_forward_dynamics(q, qd, tau, params, gravity_sign=gravity_sign)
    return np.concatenate([qd, qdd], dtype=float)


def integrate_step(
    q: np.ndarray | list[float] | tuple[float, ...],
    qd: np.ndarray | list[float] | tuple[float, ...],
    tau: np.ndarray | list[float] | tuple[float, ...],
    dt: float,
    params: Mapping[str, Any] | Any,
    *,
    method: str = "semi_implicit_euler",
    gravity_sign: str = "default",
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate one step of the two-link dynamics.

    Methods:
      - semi_implicit_euler: qd_{k+1} = qd_k + qdd*dt; q_{k+1} = q_k + qd_{k+1}*dt
        (matches MATLAB_v2/run_swing_sim.m and the repo's benchmark convention).
      - rk4: classic RK4 on the continuous-time state derivative.
    """
    q = _vec2("q", q)
    qd = _vec2("qd", qd)
    tau = _vec2("tau", tau)
    dt = float(dt)
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be positive and finite")

    m = method.lower().strip()
    if m in ("semi_implicit_euler", "symplectic_euler", "euler"):
        qdd = compute_forward_dynamics(q, qd, tau, params, gravity_sign=gravity_sign)
        qd_new = qd + qdd * dt
        q_new = q + qd_new * dt
        return q_new, qd_new

    if m in ("rk4", "runge_kutta_4"):
        x0 = np.concatenate([q, qd], dtype=float)
        k1 = _state_derivative(x0, tau, params, gravity_sign=gravity_sign)
        k2 = _state_derivative(x0 + 0.5 * dt * k1, tau, params, gravity_sign=gravity_sign)
        k3 = _state_derivative(x0 + 0.5 * dt * k2, tau, params, gravity_sign=gravity_sign)
        k4 = _state_derivative(x0 + dt * k3, tau, params, gravity_sign=gravity_sign)
        x1 = x0 + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        return x1[:2].copy(), x1[2:].copy()

    raise ValueError(f"Unknown integration method: {method!r}")
