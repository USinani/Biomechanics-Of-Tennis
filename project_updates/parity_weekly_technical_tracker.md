# MATLAB-MuJoCo Parity Weekly Technical Tracker

## Audience
Master orchestrator and custom AI GPT collaborators.

## Goal
Track technical parity closure with enough detail to reproduce decisions, diagnostics, and fixes.

## Ground Rules
- MATLAB native parity benchmark is ground truth.
- Keep `example_two_link/two_link_arm.xml` and `mujoco_arm.xml` synchronized.
- Do not run timing sweep until parity gate is satisfied.

## Week Ending
- 2026-04-15

## Week Stamp
- `2026-W16`

## Technical Status
- Python/MuJoCo parity implementation completed and exercised.
- Remaining gap is native MATLAB execution validation in this environment.

## Active Workstreams
1. Canonical data contract (units/time/control).
2. Signal comparison utility (`q1`, `q2`, `qdot1`, `qdot2` overlays + diagnostics).
3. Numerical stability alignment (integrator and damping policy).
4. End-effector velocity cross-method validation.
5. Parity gate enforcement before timing analysis.

## Evidence Inventory
- Benchmark runner: `/Users/uljan/Desktop/Mujoco/systematic_studies/swing_benchmark_mujoco_vs_bridge.py`
- MATLAB parity script: `/Users/uljan/Desktop/Mujoco/Matlab_v2/benchmark_mujoco_parity.m`
- Plotting pipeline: `/Users/uljan/Desktop/Mujoco/systematic_studies/visualisation/plot_results.py`
- Existing parity artifact example: `/Users/uljan/Desktop/Mujoco/Matlab_v2/outputs/mujoco_benchmark/parity_20260408_120321_814723/parity_overlay.png`

## Open Gaps
- [x] Canonical CSV schema unified for benchmark export and MATLAB parity bridge points.
- [x] `compare_signals.py` implemented and producing four-panel overlays.
- [x] Integrator explicitly pinned in both target MuJoCo XML files.
- [ ] Native MATLAB parity execution still pending on a host with MATLAB CLI.
- [ ] Final strict spike/smoothness thresholds still need sign-off.

## Current Hypotheses (Ranked)
1. Parameterization differences (bridge inertia/length assumptions vs MuJoCo multibody model) dominate residual mismatch.
2. Threshold calibration (strict vs trend-level) determines whether parity gate is practically useful.
3. MATLAB-native replay may reveal control-profile/timebase edge cases not visible in bridge fallback.
4. Remaining velocity spikes likely reflect model mismatch rather than unit/time bugs after unit-state fix.

## Parity Gate (Draft)
Parity ready only when all pass:
- No nonphysical spikes in joint velocity diagnostics.
- Smoothness checks within threshold on all compared channels.
- Comparable trend shape and phase for `q1`, `q2`, `qdot1`, `qdot2`.
- End-effector velocity methods (FD vs Jacobian) mutually consistent and aligned with MATLAB trend.

## Custom AI GPT Handoff (Actionable)
### Inputs to Provide
- Latest overlay plots for `q1`, `q2`, `qdot1`, `qdot2`.
- Diagnostics JSON with max error, spike counts, and smoothness metrics.
- XML diffs for integrator/damping updates.

### Questions to Ask
- Are draft parity thresholds too permissive or too strict for early closure?
- Which additional shape/phase metrics should complement RMSE?
- Which mismatch source is most likely after unit/time normalization is verified?

### Expected Output
- Priority-ranked likely root causes.
- Recommended threshold values and rationale.
- Suggested next experiment design (minimal runs with maximum discrimination).

## Next 48h Technical Plan
- Run `Matlab_v2/benchmark_mujoco_parity.m` on MATLAB-enabled host to produce native `parity_timeseries.csv`.
- Feed MATLAB-native outputs into `systematic_studies/compare_signals.py` and archive metrics.
- Lock strict parity gate thresholds and update `run_validated_timing_sweep.py` invocation policy.
- Re-run validated timing sweep with finalized thresholds and publish evidence bundle.

## Completed This Week
- Fixed major MuJoCo state-unit bug by writing runtime `qpos` in radians (not raw degrees) in benchmark path.
- Added canonical columns to benchmark CSV (`mujoco_q*_rad`, `mujoco_qdot*_rad_s`, `tau*_Nm`, etc.) while preserving legacy columns for compatibility.
- Added end-effector velocity dual-method logging (finite-difference and Jacobian).
- Added bridge-gate diagnostics in benchmark summary (`velocity_spike_count`, jerk outliers, gate flag).
- Updated MATLAB parity script to enforce dt/duration checks, torque-profile replay checks, and canonical parity timeseries export.
- Added `run_validated_timing_sweep.py` to block sweeps when parity gate fails.

## Weekly Update Template
### Week Ending
- YYYY-MM-DD

### Week Stamp
- YYYY-WW

### Technical Status
- 

### Completed
- 

### Blockers
- 

### Open Gaps
- 

### Evidence Added
- 

### Decisions Taken
- 

### Next 48h
- 

## Change Log
- 2026-04-15: Initial technical tracker template and first weekly entry.
