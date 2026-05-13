# Lane A Evidence Packet — Static Gravity / qacc Sign Reconciliation

Date: 2026-05-11

## Goal
Explain why MuJoCo (`mj_forward` → `data.qacc`) and the analytical bridge (`qdd = M^{-1}(tau - C qd - G)`) predict opposite-sign accelerations at static poses with `qdot=0`, `tau=0` (especially `q=[0,0]`).

## Artifacts / sources consulted
- `runs/diagnostics/one_step_acceleration_probe/acceleration_comparison.csv`
- `runs/diagnostics/one_step_acceleration_probe/run_probe.py`
- `example_two_link/two_link_arm.xml`
- `example_two_link/matlab_v2_dynamics.py`
- `example_two_link/matlab_v2_params.py`
- `Matlab_v2/dynamics/gravity_terms.m`
- `Matlab_v2/dynamics/mass_matrix.m`
- `Matlab_v2/dynamics/two_link_dynamics.m`
- `docs/research/LANE_A_DECISION_BOARD.md`

## Core reproduction (static, tau=0, qdot=0)
From `acceleration_comparison.csv` (sanity pose):
- MuJoCo `qacc ≈ [+38.868, -52.951]`
- Bridge `qdd ≈ [-27.839, +24.866]`

Independent re-check via a read-only Python snippet (MuJoCo `mj_forward` + bridge `two_link_tennis_model`):
- MuJoCo model gravity: `[0, 0, -9.81]`
- Joint axes (first 2 joints): `[[0,1,0],[0,1,0]]`
- At `q=[0,0]`:
  - bridge `G=[4.347, 0.771]` (positive)
  - bridge `qdd=[-27.839, +24.866]`
  - MuJoCo `qacc=[+38.868, -52.951]`

## Pose sweep (within joint limits)
Tested poses (rad):
- `q=[0,0]`
- `q=[+pi/2,0]` (within shoulder range)
- `q=[-pi/2,0]` (within shoulder range)
- `q=[0,+pi/2]` (within elbow range)

Observation:
- At `q=[±pi/2, 0]`, both systems produce ~0 gravity acceleration (as expected).
- At `q=[0,+pi/2]`, the bridge `qdd` is approximately the opposite sign of MuJoCo `qacc`.

## Sign-transform tests (bridge-side only)
Tested transforms mapping the MuJoCo pose `q_mj` to the bridge pose `q_br`:
- `q_br = q_mj`
- `q_br = -q_mj`
- `q_br = [q1, -q2]`
- `q_br = [-q1, q2]`

None of these angle sign transforms reconciled the sign mismatch at `q=[0,0]` and `q=[0,+pi/2]`.

Tested a pure gravity-sign flip (equivalently: `G -> -G` so `qdd -> -qdd` when `tau=0,qdot=0`):
- This *did* align the **signs** at `q=[0,0]` and `q=[0,+pi/2]` (magnitudes still differ).

## Critical caveat (joint limits / constraints)
The earlier pose `q=[0,-pi/2]` produces extremely large MuJoCo `qacc`. This configuration is **outside** the XML elbow joint range (`elbow_pitch range="0 150"` degrees), so constraint forces dominate and the resulting `qacc` is not a clean gravity-only diagnostic.

## Interim conclusion
The static tests indicate a **systematic gravity/coordinate-sign convention mismatch** between MuJoCo and the analytical bridge at least in the direction of gravitational generalized forces (or the sign of the generalized coordinates as used in the gravity terms), rather than damping or control.

