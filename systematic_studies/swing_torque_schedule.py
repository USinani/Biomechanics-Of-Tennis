"""Open-loop shoulder/elbow torques used by swing benchmark and viewer demos (keep in sync)."""

from __future__ import annotations

import math


def swing_torques(
    t: float,
    tau_amp: float,
    tau_f_hz: float,
    phase_rad: float,
) -> tuple[float, float]:
    """Same law as `swing_benchmark_mujoco_vs_bridge.py` (sine burst on both joints)."""
    tau0 = tau_amp * math.sin(2.0 * math.pi * tau_f_hz * t)
    tau1 = tau_amp * math.sin(2.0 * math.pi * tau_f_hz * t + phase_rad)
    return tau0, tau1
