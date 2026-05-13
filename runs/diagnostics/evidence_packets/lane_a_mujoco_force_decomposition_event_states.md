# Lane A Evidence Packet — MuJoCo Force Decomposition at Event States

Date: 2026-05-11

## Goal
Explain why MuJoCo instantaneous `qacc` is extremely large at event states (step480/step486) while analytical bridge `qdd` remains small even after gravity-sign correction.

## Artifacts
- Source states:
  - `runs/diagnostics/parity_gravity_sign_probe/one_step/states_used.json`
- One-step sign table:
  - `runs/diagnostics/parity_gravity_sign_probe/one_step/gravity_sign_one_step.csv`
- Derived decomposition table (this investigation):
  - `runs/diagnostics/parity_gravity_sign_probe/force_decomposition/force_decomposition_event_states.csv`

## Method (read-only)
For each state (q00, step470, step480, step486):
1) Set MuJoCo `data.qpos[:2]`, `data.qvel[:2]`, `data.ctrl[:2]` from `states_used.json`.
2) Call `mujoco.mj_forward(model, data)`.
3) Record:
   - `data.qacc[:2]`
   - `data.qfrc_bias[:2]`, `data.qfrc_passive[:2]`, `data.qfrc_actuator[:2]`, `data.qfrc_applied[:2]`, `data.qfrc_constraint[:2]`
   - mass matrix `M` via `mj_fullM(model, M, data.qM)` and cond/det of the 2x2 block
   - `model.nefc`/`data.efc_force` max abs (if any)
   - joint-limit margin (degrees) relative to XML ranges
4) Compute bridge terms from `example_two_link/matlab_v2_dynamics.two_link_tennis_model`:
   - `M`, `C`, `G`, `Cqd=C@qd`
   - `qdd` under `gravity_sign=default` and `gravity_sign=mujoco`
   - optional “damping-corrected” bridge: `tau_eff = tau - model.dof_damping[:2] * qdot`, with `gravity_sign=mujoco`

## Key raw observations (from derived CSV)
- MuJoCo event-state `qfrc_constraint` is nonzero at step480 and step486:
  - step480: `qfrc_constraint1 ≈ -20.65`, `qfrc_constraint2 ≈ 0.0`
  - step486: `qfrc_constraint1 ≈ -14.04`, `qfrc_constraint2 ≈ 0.0`
- Joint-limit margin indicates both event states are within limits (not at hard bounds):
  - step480 shoulder margin ≈ -0.074° (slightly past +120°), elbow margin ≈ 6.79°
  - step486 shoulder margin ≈ -0.945° (further past +120°), elbow margin ≈ 8.10°
  This suggests shoulder joint is *just beyond* nominal range at these states, plausibly activating limit constraint forces.

## Interim conclusion
The presence of nonzero `qfrc_constraint` coincident with enormous `qacc` at step480/486, and the shoulder angle being slightly beyond its range, supports the hypothesis that **joint limit / constraint forces** are a major contributor to the MuJoCo event accelerations (and are absent from the bridge model).

