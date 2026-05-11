# Lane A Evidence Packet — Actuator / Control Convention Check

Date: 2026-05-11

## Scope and constraints
- Read-only source inspection only.
- No simulations, no parity scripts, no threshold changes.
- Goal: determine whether MuJoCo, Python bridge, and MATLAB-native paths apply the *same* control/torque inputs (sign, order, scaling, saturation, timing, mapping).

## Files inspected (exact paths)
- `docs/research/LANE_A_DECISION_BOARD.md`
- `example_two_link/two_link_arm.xml`
- `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`
- `example_two_link/matlab_v2_dynamics.py`
- `Matlab_v2/run_swing_sim.m`
- `Matlab_v2/dynamics/two_link_dynamics.m`
- `Matlab_v2/dynamics/two_link_tennis_model.m`
- `Matlab_v2/benchmark_mujoco_parity.m`
- `Matlab_v2/controls/control_profile.m`
- `Matlab_v2/controls/torque_profile_piecewise.m`
- `Matlab_v2/default_params.m`
- `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv` (header + early rows only)

## 1) MuJoCo actuator/control convention (XML + benchmark driver)

### Actuator-to-joint mapping
- XML defines two motor actuators:
  - `m_shoulder` targets joint `shoulder_pitch`
  - `m_elbow` targets joint `elbow_pitch`
  Evidence: `example_two_link/two_link_arm.xml` actuator section.

### Gear/sign
- Both motors specify `gear="1"`.
- No explicit sign inversion is present in XML; sign follows MuJoCo motor convention: positive `ctrl` produces positive torque along the joint axis direction.
  Evidence: `example_two_link/two_link_arm.xml` actuator section (gear=1, motor shortcut).

### ctrlrange / saturation
- Both motors declare `ctrllimited="true"` and `ctrlrange="-60 60"`.
  Evidence: `example_two_link/two_link_arm.xml` actuator section.

### How tau1/tau2 are assigned (benchmark driver)
- In `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`, the torque schedule returns `(tau0, tau1)` and the script assigns:
  - `data.ctrl[0] = tau0` (shoulder)
  - `data.ctrl[1] = tau1` (elbow)
  Evidence: `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` main loop.

### Control timing (when applied relative to step)
- The benchmark sets `data.ctrl[...]` then calls `mujoco.mj_step(model, data)`. This means the control is applied for that integration step.
  Evidence: `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` main loop ordering.

### Recorded torque: commanded vs applied
- The benchmark *computes* a clipped torque vector using `model.actuator_ctrlrange`:
  - `clipped_tau = np.clip(tau, ctrl_range[:,0], ctrl_range[:,1])`
  - and writes both commanded (`tau1_Nm`,`tau2_Nm`) and “applied” (`tau1_applied_Nm`,`tau2_applied_Nm`) columns to the CSV.
- However, the benchmark assigns **unclipped** values to `data.ctrl[...]` (it does not overwrite `data.ctrl` with `clipped_tau`).
  - If the actuator is ctrl-limited in MuJoCo (it is, per XML), MuJoCo will internally saturate; in that case `tau*_applied_Nm` matches the internal applied torque *if* `model.actuator_ctrlrange` reflects those limits.
  Evidence: `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` (clipping used for reporting only) + `example_two_link/two_link_arm.xml` (ctrllimited/ctrlrange).

## 2) Python bridge control convention

### Input vector order and mapping
- The bridge dynamics consume `tau` as a 2-vector \([tau1, tau2]\) with the same joint ordering as the state \([q1,q2]\).
- Benchmark constructs `tau = np.array([tau0, tau1])` and feeds it to `integrate_step(q_b, qd_b, tau, ...)`.
  Evidence: `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` + `example_two_link/matlab_v2_dynamics.py` (`_vec2("tau", tau)` and use in forward dynamics).

### Sign convention
- Forward dynamics uses \(qdd = M^{-1}(tau - C qd - G)\); i.e., `tau` enters additively, without a sign flip.
  Evidence: `example_two_link/matlab_v2_dynamics.py` (`rhs = tq - C @ thd - G`).

### Saturation
- No saturation/clipping is performed inside `example_two_link/matlab_v2_dynamics.py`.
- Benchmark does not clamp `tau` before feeding bridge integration.
  Evidence: `example_two_link/matlab_v2_dynamics.py` and `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`.

### Control timing in integration
- Bridge integration step uses the torque value passed for that step (same `tau` used to compute `qdd` and update \([qd,q]\) under semi-implicit Euler).
  Evidence: `example_two_link/matlab_v2_dynamics.py` docstring + implementation of `semi_implicit_euler`.

## 3) MATLAB native control convention

### Input vector order and sign
- `control_profile(t, params)` returns \(u = [tau0; tau1]\) and documents it as:
  - `u = [tau_shoulder; tau_elbow] (N*m)`
  Evidence: `Matlab_v2/controls/control_profile.m`.
- `two_link_tennis_model(...).B = eye(2)` indicates a direct input-to-joint map (no re-ordering/scaling).
  Evidence: `Matlab_v2/dynamics/two_link_tennis_model.m`.

### Damping subtraction (if any)
- `two_link_dynamics` computes net torque as:
  - `tau = u - b .* qd` if `params.physics.damping_nm_s` is present/non-empty.
  Evidence: `Matlab_v2/dynamics/two_link_dynamics.m`.
- Default parameters set `damping_nm_s = [0; 0]`.
  Evidence: `Matlab_v2/default_params.m`.

### Piecewise replay behavior from CSV
- `benchmark_mujoco_parity` reads torques from CSV columns and sets:
  - `params.control.type = 'piecewise'`
  - `params.control.piecewise_times = t_csv`
  - `params.control.piecewise_taus = [tau1_csv, tau2_csv]`
  Evidence: `Matlab_v2/benchmark_mujoco_parity.m`.
- Piecewise torque semantics are “previous hold”:
  - `idx = find(t >= times, 1, 'last'); u = taus(idx,:)'`
  Evidence: `Matlab_v2/controls/torque_profile_piecewise.m`.

### Saturation / scaling
- No saturation/clipping is applied in MATLAB control profile functions (for `piecewise`).
  Evidence: `Matlab_v2/controls/control_profile.m` + `Matlab_v2/controls/torque_profile_piecewise.m`.

## 4) Note on the 500-step probe CSV fields (observed structure)
- The derived 500-step CSV includes both commanded and “applied” torque columns:
  - `tau1_Nm`, `tau2_Nm`, `tau1_applied_Nm`, `tau2_applied_Nm`
  Evidence: header line in `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`.

## 5) Comparison matrix (control convention)

| Dimension | MuJoCo | Bridge | MATLAB native | Match? | Evidence |
|---|---|---|---|---|---|
| joint_order | \[shoulder_pitch, elbow_pitch] | \[q1, q2] | \[q1, q2] | likely | XML joint names + benchmark `data.ctrl[0/1]` + state ordering in MATLAB/Python |
| torque_order | `data.ctrl[0]=tau0`, `data.ctrl[1]=tau1` | `tau=[tau0,tau1]` | `u=[tau_shoulder; tau_elbow]` | likely | `swing_benchmark_mujoco_vs_bridge.py`; `control_profile.m` |
| torque_sign | positive ctrl → positive joint torque (no explicit inversion in XML) | enters as \(+tau\) in \(M^{-1}(tau - Cqd - G)\) | enters as \(+u\) (B=I) | likely | XML gear=1; `matlab_v2_dynamics.py`; `two_link_tennis_model.m` |
| gear/scaling | gear=1 | none | none (B=I) | yes | XML; `two_link_tennis_model.m` |
| saturation | ctrlrange \[-60,60] with `ctrllimited="true"` | none | none | **potential mismatch if torques exceed ctrlrange** | XML; Python benchmark clips only for reporting; MATLAB piecewise has no clamp |
| control_timing | set `data.ctrl` then `mj_step` | torque used for that integration step | torque evaluated at `t(k)` then step update | likely | loop ordering in `swing_benchmark_mujoco_vs_bridge.py`; `run_swing_sim.m` |
| recorded_vs_applied_tau | CSV includes commanded + “applied” (clipped) but assigns unclipped to `data.ctrl` | only sees commanded | piecewise replays commanded from CSV (no clamp) | **potential mismatch if saturation occurs** | `swing_benchmark_mujoco_vs_bridge.py`; CSV header; MATLAB replay setup in `benchmark_mujoco_parity.m` |
| damping_interaction | MuJoCo joint damping exists (XML default joint damping; may be scaled in derived probes) | none in dynamics equations | optional `u - b.*qd` (default b=0) | mismatch in general, but **not a control mapping mismatch** | XML default joint damping; `two_link_dynamics.m`; `default_params.m` |

## 6) Assessment (Lane A)
**actuator/control convention appears aligned** for joint/torque order, sign, and scaling **under the current passive baseline (tau_amp=0)**.

The remaining *control-convention* mismatch risk that is still concrete is **saturation semantics** (MuJoCo ctrlrange vs no clipping in bridge/MATLAB) — but this only matters in driven cases where commanded torques exceed \[-60,60]. In the passive probe CSV excerpt, `tau0=tau1=0` early on, so saturation is not implicated in the qdot2 event reproduction.

## 7) Research implication
This reduces the probability that Lane A’s remaining divergence is caused by a simple actuator mapping/sign/order bug in the benchmark plumbing. It pushes the active hypothesis toward **model-formulation / contract mismatch** (e.g., damping/friction/contact/constraint/integrator-state semantics, or other MuJoCo physics terms not represented in analytical dynamics), rather than an input convention mismatch.

## 8) Next smallest safe action (pick exactly one)
**park actuator/control branch and inspect model-formulation equivalence**

