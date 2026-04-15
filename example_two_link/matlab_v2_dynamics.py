#!/usr/bin/env python3
"""Python port of MATLAB_v2 two-link tennis dynamics."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Mapping, Any

import numpy as np


REQUIRED_FIELDS = ("l1", "l2", "m1", "m2", "lc1", "lc2", "I1", "I2", "g")


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
) -> np.ndarray:
    """Compute qdd from q, qd, tau."""
    th = _vec2("theta", theta)
    thd = _vec2("theta_dot", theta_dot)
    tq = _vec2("tau", tau)
    M, C, G, _ = two_link_tennis_model(th, thd, params)
    rhs = tq - C @ thd - G
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

