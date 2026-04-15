# MATLAB-MuJoCo Parity Weekly Operating Report

## Purpose
This is the recurring project sync document for the master orchestrator, custom AI GPT, supervisor, and other stakeholders. Update this file weekly and after any major parity checkpoint.

## Document Set (Use These Weekly)
- Executive summary (supervisor-facing): `/Users/uljan/Desktop/Mujoco/project_updates/parity_weekly_exec_summary.md`
- Technical tracker (orchestrator + custom AI GPT): `/Users/uljan/Desktop/Mujoco/project_updates/parity_weekly_technical_tracker.md`
- This master report remains the policy and reference backbone.

## Versioning Convention
- Week stamp format for all recurring updates: `YYYY-WW` (ISO week), for example `2026-W16`.
- Keep `Week Ending` (calendar date) and `Week Stamp` (ISO identifier) in both weekly docs.
- Optional archival naming:
  - `parity_weekly_exec_summary_YYYY-WW.md`
  - `parity_weekly_technical_tracker_YYYY-WW.md`

## Operating Rules
- Ground truth: native MATLAB pipeline via `/Users/uljan/Desktop/Mujoco/Matlab_v2/run_swing_sim.m` and `/Users/uljan/Desktop/Mujoco/Matlab_v2/benchmark_mujoco_parity.m`.
- MuJoCo scope lock: keep `/Users/uljan/Desktop/Mujoco/example_two_link/two_link_arm.xml` and `/Users/uljan/Desktop/Mujoco/mujoco_arm.xml` synchronized.
- Priority: correctness and physical validity over speed.
- Hard gate: no timing sweep or downstream analysis until parity gate passes.

## Weekly Snapshot (Current)
### Week Ending
- 2026-04-15

### Week Stamp
- 2026-W16

### Status
- Core implementation completed for Python/MuJoCo parity workflow.
- Gated comparison run executed and timing sweep/plot regeneration completed after gate pass.
- Native MATLAB execution remains pending due missing local MATLAB CLI.

### Blockers
- Local environment blocker: `matlab` executable unavailable for native MATLAB parity run.
- Strict production gate thresholds still need review; current pass used trend-level relaxed thresholds.

### Decisions
- MATLAB native simulation is the parity reference.
- Both MuJoCo XML models remain synchronized throughout fixes.
- Timing-sweep re-run is explicitly blocked until parity readiness criteria are met.

### Next 48h
- Execute native MATLAB parity script on MATLAB-enabled host and export canonical parity timeseries.
- Re-run `compare_signals.py` against MATLAB-vs-MuJoCo canonical data.
- Lock strict parity thresholds and rerun validated timing sweep under final gate settings.
- Publish refreshed stakeholder artifact bundle with updated decisions and residual risks.

## Metrics and Evidence (Update Every Week)
### Validation Gate Definition
Parity is considered ready only when all conditions are met:
- No unphysical velocity spikes.
- Smooth trajectories under controlled torque profiles.
- Comparable MATLAB vs MuJoCo trend behavior for `q1`, `q2`, `qdot1`, `qdot2`.
- End-effector velocity consistency across computation methods.

### Latest Evidence Artifacts
- MuJoCo/bridge benchmark runner: `/Users/uljan/Desktop/Mujoco/systematic_studies/swing_benchmark_mujoco_vs_bridge.py`
- MATLAB parity benchmark: `/Users/uljan/Desktop/Mujoco/Matlab_v2/benchmark_mujoco_parity.m`
- Plot pipeline: `/Users/uljan/Desktop/Mujoco/systematic_studies/visualisation/plot_results.py`
- Signal comparison plot: `/Users/uljan/Desktop/Mujoco/systematic_studies/outputs/figures/compare_signals.png`
- Signal diagnostics: `/Users/uljan/Desktop/Mujoco/systematic_studies/outputs/compare_signals_metrics.json`
- Regenerated timing/summary plots: `/Users/uljan/Desktop/Mujoco/systematic_studies/outputs/figures/timing_vs_velocity.png`, `/Users/uljan/Desktop/Mujoco/systematic_studies/outputs/figures/energy_vs_timing.png`, `/Users/uljan/Desktop/Mujoco/systematic_studies/outputs/figures/summary_figure.png`

## Gap Register (Live)
### Open Gaps
- [x] Canonical CSV schema implemented for benchmark export and parity handoff.
- [x] Direct four-panel signal comparator script (`compare_signals.py`) implemented.
- [x] Integrator and damping explicitly synchronized in both parity MuJoCo XML models.
- [ ] Final strict pass/fail thresholds for spike/smoothness still need lock-in.
- [ ] Native MATLAB parity run still pending due local environment availability.

### Resolved Gaps
- MuJoCo runtime state-unit mismatch fixed in benchmark pipeline.
- End-effector velocity dual-method diagnostics (FD + Jacobian) added for stability validation.

## Risk Register (Live)
- Risk: false mismatch due to unit conversion mistakes.
  - Mitigation: log both raw and canonical units and assert expected ranges.
- Risk: apparent parity failure due to unsynchronized simulation horizons.
  - Mitigation: enforce shared `dt` and total duration from a common benchmark input.
- Risk: overfitting damping to hide model mismatch.
  - Mitigation: apply minimal damping changes and require trend-consistency evidence in comparison plots.

## Custom AI GPT Handoff (Weekly)
### Current Ask
- Review proposed parity gate thresholds for spike/smoothness detection.
- Challenge assumptions around integrator parity and damping equivalence.
- Suggest robust statistical checks for trend similarity beyond RMSE (for example shape/phase consistency metrics).

### Inputs to Provide
- Overlay plots for `q1`, `q2`, `qdot1`, `qdot2`.
- Diagnostic JSON from `compare_signals.py`.
- Updated MuJoCo XML snippets with pinned integrator/damping values.

### Expected Outputs
- Ranked list of likely remaining mismatch causes.
- Suggested threshold values for pass/fail criteria.
- Improvement recommendations for model-fidelity and reproducibility.

## Supervisor Update (Weekly One-Paragraph)
Parity program is in setup phase with decisions locked on ground truth (native MATLAB), MuJoCo model synchronization strategy, and strict no-analysis-before-validation gating. Next execution cycle will produce the first canonical comparison overlays and quantitative diagnostics to move from planning to evidence-based closure of model inconsistencies.

## Reusable Weekly Template
Copy this block for each new weekly entry.

### Week Ending
- YYYY-MM-DD

### Week Stamp
- YYYY-WW

### Status
- 

### Blockers
- 

### Decisions
- 

### Next 48h
- 

### Evidence Added This Week
- 

### Gaps Closed This Week
- 

### New Risks / Mitigations
- 

## Change Log
- 2026-04-15: Converted master report into recurring weekly operating format with fixed sync sections.
- 2026-04-15: Updated with implementation results, generated artifacts, and remaining MATLAB/threshold blockers.
