# Lane A Evidence Packet — One-Step Acceleration Comparison Probe (Plan + Run Log)

Date: 2026-05-11

## Goal
At identical \(q\), \(\dot q\), \(\tau\), and parameters, compare MuJoCo instantaneous `qacc` against analytical bridge \(qdd\) to isolate whether remaining mismatch is local force-term / model-equivalence mismatch (especially damping/model forces), rather than accumulated integration drift.

## Method (implementation contract)
- Candidate states taken from derived CSV:
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
  - steps: 0, 470, 480, 486
  - plus optional synthetic sanity pose `q=[0,0]`, `qdot=[0,0]`, `tau=[0,0]`
- MuJoCo instantaneous acceleration:
  - load `example_two_link/two_link_arm.xml`
  - set `data.qpos`, `data.qvel`, `data.ctrl`
  - (variant) scale `model.dof_damping` in-memory
  - call `mujoco.mj_forward(model, data)`
  - read `data.qacc[:2]`
- Analytical bridge acceleration:
  - use `example_two_link/matlab_v2_dynamics.compute_forward_dynamics(q, qd, tau, params)`
  - where `params` are derived via `example_two_link/matlab_v2_params.params_from_mujoco_xml(xml)`
- Variants compared:
  1) MuJoCo damping scale 1.0 vs bridge no damping
  2) MuJoCo damping scale 0.0 vs bridge no damping
  3) MuJoCo damping scale 1.0 vs bridge with manual damping torque correction
     - \(\tau_\mathrm{eff} = \tau - b \odot \dot q\)
     - with \(b\) taken from MuJoCo `model.dof_damping[:2]` at damping scale 1.0

## Derived outputs (written only under allowed paths)
- `runs/diagnostics/one_step_acceleration_probe/acceleration_comparison.csv`
- `runs/diagnostics/one_step_acceleration_probe/states_used.json`
- `runs/diagnostics/one_step_acceleration_probe/mujoco_meta.json`
- `runs/diagnostics/one_step_acceleration_probe/run_probe.py`

