# Lane A Evidence Packet — Joint-Limit Contract Inspection (Read-Only)

Date: 2026-05-11

## Scope
Read-only inspection: XML joint ranges, 500-step derived benchmark joint-angle margins vs limits, alignment with qdot2 jerk window, and whether bridge/MATLAB dynamics include equivalent joint-limit mechanics.

## Artifacts inspected
- `docs/research/LANE_A_DECISION_BOARD.md` (updated hypothesis)
- `example_two_link/two_link_arm.xml`
- `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
- `runs/diagnostics/evidence_packets/lane_a_mujoco_force_decomposition_event_states.md`
- `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` (parity harness context; not modified)
- `example_two_link/matlab_v2_dynamics.py` (grep: no joint-limit keywords)
- `Matlab_v2/dynamics/two_link_dynamics.m` (grep: no joint-limit keywords)
- `Matlab_v2/default_params.m`, `Matlab_v2/utils/validate_params.m` (no joint-range validation)

## Derived outputs (this packet)
- `runs/diagnostics/parity_gravity_sign_probe/joint_limit_inspection/limit_margin_summary.csv`

## 1. MuJoCo XML joint limits (compiler angle=degree)

| joint | lower deg | upper deg | lower rad | upper rad |
|-------|-----------|-----------|-----------|-----------|
| shoulder_pitch | -120 | 120 | -2.0943951023931953 | 2.0943951023931953 |
| elbow_pitch | 0 | 150 | 0.0 | 2.6179938779914944 |

Source: `example_two_link/two_link_arm.xml` lines 22–25.

## 2. Benchmark margin analysis (500-step CSV)

Margin definition (degrees): distance to nearest bound,
`min(q - q_lo, q_hi - q)`; negative means outside the XML range.

| joint | first crossing step | first crossing time (s) | min margin (deg) | notes |
|-------|--------------------:|------------------------:|-----------------:|-------|
| shoulder (q1) | 480 | 0.48 | -1.478 (at step 499) | First violation at step 480 with q1≈120.074° (≈0.074° past +120°); margin worsens to end of run |
| elbow (q2) | — | — | +2.838 (at step 374) | No limit crossing over the run; minimum margin remains positive |

## 3. Alignment with qdot2 spike / jerk window
- Largest finite-difference “jerk” spikes in `mujoco_qdot2_rad_s` (using `dt_s` from adjacent rows) occur at **steps 481–485** (immediately after the first shoulder limit violation at **step 480**).
- **Conclusion:** the qdot2 spike/jerk window **aligns** with the onset of shoulder limit violation and the subsequent constrained dynamics window.

## 4. Bridge / MATLAB joint-limit handling
- **Python bridge (`matlab_v2_dynamics.py`):** no joint-angle clamping, saturation, penalty, or constraint-force terms found by keyword search; dynamics are unconstrained ODE-style `M qdd = tau - C qd - G` (plus optional damping in benchmark harness).
- **MATLAB native (`two_link_dynamics.m`):** no limit/clamp/constraint keywords; unconstrained rigid-body dynamics.
- **Validation / config (`validate_params.m`, `default_params.m`):** required-field checks only; **no** enforcement or validation of joint angle ranges against MuJoCo XML limits.

## 5. Parity contract assessment
**Constrained MuJoCo vs unconstrained analytical bridge/MATLAB mismatch confirmed** (for joint limits): MuJoCo applies XML `range` with `limited="true"` default; analytical path integrates without equivalent hard limits or constraint impulses.

## 6. Research implication
Strict parity comparing full MuJoCo rollouts against unconstrained analytical trajectories can fail at states where MuJoCo’s joint-limit constraints inject `qfrc_constraint` and large `qacc`, while the bridge predicts smooth continuation. This is consistent with the step480/486 event and qdot2 jerk gate behavior **without** requiring a single root cause beyond the contract gap.

## 7. Next smallest safe action (no fix proposed here)
**Plan derived MuJoCo no-limit probe** (e.g., temporary duplicate MJCF or harness flag) to quantify trajectory divergence when limits are disabled vs enabled—requires explicit approval before any XML/code change.
