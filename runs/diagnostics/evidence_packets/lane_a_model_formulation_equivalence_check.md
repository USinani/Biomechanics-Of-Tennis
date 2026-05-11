# Lane A Evidence Packet — Model Formulation Equivalence Check (MuJoCo vs Analytical)

Date: 2026-05-11

## Scope and constraints
- Read-only inspection of equations and model structure only.
- No simulations, no parity scripts, no threshold changes, no edits to XML / Python / MATLAB code.
- Goal: assess structural equivalence (angle conventions, term structure, damping placement, state semantics), not parameter numerical fit.

## Files inspected (exact paths)
- `docs/research/LANE_A_DECISION_BOARD.md`
- `example_two_link/matlab_v2_dynamics.py`
- `example_two_link/matlab_v2_params.py`
- `example_two_link/two_link_arm.xml`
- `Matlab_v2/dynamics/two_link_dynamics.m`
- `Matlab_v2/dynamics/two_link_tennis_model.m`
- `Matlab_v2/dynamics/mass_matrix.m`
- `Matlab_v2/dynamics/gravity_terms.m`
- `Matlab_v2/dynamics/coriolis_terms.m`
- `Matlab_v2/default_params.m`
- `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`

## Key findings

### Angle convention (relative vs absolute)
- MuJoCo: elbow joint is nested under shoulder body, so `q2` is **relative** to link1 (a hinge in the child body frame).
  - Evidence: `example_two_link/two_link_arm.xml` has `<body name="elbow" pos="0.32 0 0">` nested under shoulder, with `<joint name="elbow_pitch" .../>`.
- Analytical (Python + MATLAB): terms repeatedly use `theta1 + theta2` (e.g., `cos(theta1+theta2)`), which is the standard **relative elbow angle** convention (absolute angle of link2 is `theta1+theta2`).
  - Evidence: `example_two_link/matlab_v2_dynamics.py` uses `c12 = cos(theta1+theta2)`.
  - Evidence: `Matlab_v2/dynamics/gravity_terms.m` uses `c12 = cos(theta1 + theta2)`.

### Mass matrix / Coriolis / gravity structural form
- Python and MATLAB implement the same canonical 2-link planar rigid-body structure:
  - Mass matrix \(M(q)\) depends on `cos(theta2)` only (relative elbow angle), via `beta*cos(theta2)`.
  - Coriolis matrix uses `h = -m2*l1*lc2*sin(theta2)` and multiplies by `theta_dot` terms.
  - Gravity uses `cos(theta1)` and `cos(theta1+theta2)`.
  - Evidence: `example_two_link/matlab_v2_dynamics.py`, `Matlab_v2/dynamics/mass_matrix.m`, `coriolis_terms.m`, `gravity_terms.m`.

### Damping / force-model placement
- MuJoCo: joint damping is part of the model (XML default `<joint damping="0.12" .../>`); and geoms have friction parameters.
  - Evidence: `example_two_link/two_link_arm.xml` default joint damping + geom friction.
- Analytical: optional viscous damping is implemented as a **torque subtraction** `tau_net = u - b.*qd` if `params.physics.damping_nm_s` is set; default is `[0;0]`.
  - Evidence: `Matlab_v2/dynamics/two_link_dynamics.m`; `Matlab_v2/default_params.m`.
- Python bridge: does not include damping unless it is embedded into the torque input passed (it is not in current benchmark; tau is passed directly).
  - Evidence: `example_two_link/matlab_v2_dynamics.py` forward dynamics has no damping term; `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` passes `tau` straight to `integrate_step`.

### State / qdot semantics
- All analytical code uses state \(x=[q1,q2,qd1,qd2]\) with \(q\) in radians and \(qd\) in rad/s, and semi-implicit Euler update is explicitly used in both Python bridge and MATLAB simulation path.
  - Evidence: `example_two_link/matlab_v2_dynamics.py` (semi-implicit Euler) and `Matlab_v2/dynamics/two_link_dynamics.m` + `Matlab_v2/run_swing_sim.m` (semi-implicit Euler loop).
- MuJoCo internal integrator is `implicitfast` and timestep is `0.001`, and qvel is rad/s regardless of XML `angle="degree"`.
  - Evidence: `example_two_link/two_link_arm.xml` option; `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` qvel conversion helpers.

### Inertial assumptions
- Analytical model is a planar 2-link rigid-body model parameterized by `(l1,l2,m1,m2,lc1,lc2,I1,I2)`.
  - Evidence: required fields in `example_two_link/matlab_v2_dynamics.py` and in MATLAB `two_link_tennis_model.m`.
- MuJoCo inertias are generated from geoms unless explicit `<inertial>` tags are provided (none are present). The Python helper `params_from_mujoco_xml` explicitly notes it builds an approximate parameter set from the XML geoms (capsule/rod proxy).
  - Evidence: `example_two_link/two_link_arm.xml` has no `<inertial>` tags; `example_two_link/matlab_v2_params.py` notes approximations.

## Assessment (Lane A)
Angle conventions (relative elbow) and the analytical equation structure (M/C/G) appear mutually consistent between Python bridge and MATLAB. The remaining structural mismatch vs MuJoCo is most plausibly dominated by **model-force formulation differences** (MuJoCo joint damping / geom friction and other MuJoCo forces vs analytical dynamics without those forces), and integrator differences.

