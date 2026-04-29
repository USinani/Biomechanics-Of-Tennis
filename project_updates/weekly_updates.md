# Weekly Updates (Rolling Log)

Single authoritative rolling log for the two-link MuJoCo + MATLAB parity
project. Newest week at the top; older weeks are append-only. Use
[WEEKLY_TEMPLATE.md](WEEKLY_TEMPLATE.md) when adding a new week.

## Past weeks (archive)

- [Week 2026-W18 (ending 2026-05-03)](#week-2026-w18-ending-2026-05-03) - current
- [Week 2026-W17 (ending 2026-04-26)](#week-2026-w17-ending-2026-04-26)
- [Week 2026-W16 (ending 2026-04-19)](#week-2026-w16-ending-2026-04-19)
- [Week 2026-W11 (ending 2026-03-15)](#week-2026-w11-ending-2026-03-15)
- [Week 2026-W10 (ending 2026-03-08)](#week-2026-w10-ending-2026-03-08)

---

## Week 2026-W18 (ending 2026-05-03)

Meeting date: 2026-04-29. See the rendered HTML at
`systematic_studies/outputs/reports/weekly_dashboard_2026-W18_2026-04-29.html`
(regenerate via `./run.sh systematic_studies/weekly_dashboard.py`).

### Done this week

- [x] Upgraded `systematic_studies/weekly_dashboard.py` to be presentation-ready: live "At a glance" KPI strip (parity-strict, relaxed gate, racket figure-8, SAC eval) read from the embedded JSONs; fixed 5-field caption per figure (What / Why / How / Takeaway / Likely supervisor question), 6/6 figures covered; one-line context line per JSON summary, 5/5 covered; "How to read this report" intro banner. (completed 2026-04-29) [viz] [PI]
- [x] Mutual-motor-learning prototype removed and all related docs reverted; `grep` + `git status` confirm no traces remain. Scope kept aligned with this PhD's research question (kinetic-chain timing, not paired motor learning). (completed 2026-04-22) [repo] [PI]
- [x] Confirmed `systematic_studies/outputs/.gitignore` is `* + !.gitignore`, so regenerated figures, JSONs, and HTML reports are excluded by default. (closes part of W17 gitignore commitment.) (completed 2026-04-29) [repo] [PI]

### Slipped from W17 (re-committed)

- [ ] SysID loop fitting `example_two_link/matlab_v2_params.py` to MuJoCo rollouts. First acceptance criterion remains closing the strict parity gate. (re-target 2026-05-02) [parity] [PI]
- [ ] Replace bridge first-order Euler integrator with RK4 in `example_two_link/matlab_v2_dynamics.py`; produce a 2-row ablation table (Euler vs RK4 at identical params). (re-target 2026-05-01) [parity] [PI]
- [ ] Add `--sweep` mode to `systematic_studies/racket_trajectory.py` that sweeps `--ws-f-hz` and writes a tidy CSV for a peak-speed-vs-frequency plot. (re-target 2026-05-02) [viz] [PI]
- [ ] Add a top-level `README.md` pointing to `RUN.md`, `docs/REPO_LAYOUT.md`, `docs/PHD_DIRECTIONS.md`, and this rolling weekly log. (re-target 2026-04-30) [repo] [PI]

### Next week

- [ ] First combined sysID + RK4 ablation table written to `docs/PHD_DIRECTIONS.md §2.1` (rmse_q, rmse_qdot, spike_count, jerk_outliers, parity_ready) per cell. (target 2026-05-03) [parity] [PI]
- [ ] Commit + tag the current dashboard / scope-cleanup work as `v0.2-dashboard-ready` before any further changes (no save point exists since 2026-04-22). (target 2026-04-29 EOD) [repo] [PI]
- [ ] Move `hundred_x_alerts/` and `tests/test_hundred_x_alerts.py` out of this repository (unrelated side-project; not part of this PhD). (target 2026-04-29 EOD) [repo] [PI]

### Carried from past weeks

- [ ] Strict MATLAB-vs-MuJoCo parity gate still failing (`rmse_q ~ 2.49 rad`, `rmse_qdot ~ 13.76 rad/s`, `parity_ready = false`). (carried since 2026-W16) (target 2026-05-03) [parity] [PI]
- [ ] Publish "first timing result" (timing vs velocity with CIs) - still blocked on the strict parity gate above. (carried since 2026-W16) (target 2026-05-10) [parity] [PI]
- [ ] Large-scope rename `example_two_link/ -> models/two_link/` with `arm_env.py`, `train_sac*.py`, `run_policy_in_mujoco_viewer.py` relocations - deferred; tracked in `docs/REPO_LAYOUT.md` section 5. (carried since 2026-W17) (target 2026-05-10) [repo] [PI]

### Notes

- Honest assessment: 4 of 5 W17 hard commitments slipped (sysID, RK4, racket sweep, top-level README). Parity is the single bottleneck for Paper 1; the next four working days must be spent on sysID + RK4 with no detours.
- The dashboard presentation upgrade is a force multiplier for supervisor meetings but does NOT advance the parity gate; tracked accordingly under [viz], not [parity].
- Supervisor ask for the meeting: confirm the sysID loss function before another week of work - joint-residual only, hand-residual only, or both, and the relative weighting.

---

## Week 2026-W17 (ending 2026-04-26)

Supporting update: [2026-04-22_project_consolidation_and_racket_viz.md](2026-04-22_project_consolidation_and_racket_viz.md).

### Done this week

- [x] Shipped `systematic_studies/racket_trajectory.py` with four protocols (passive, open-loop Lissajous, joint-space figure-8, workspace figure-8) and three modes (headless, plot, viewer). (completed 2026-04-22) [viz] [PI]
- [x] Added FFT-based figure-8 detector with zero-padded rFFT; reference run reports `figure8_detected = true`, `freq_ratio_z_over_x = 2.00`, `self_intersections = 89`. (completed 2026-04-22) [viz] [PI]
- [x] Wired `plot_racket_trajectory(...)` into `systematic_studies/visualisation/plot_results.py::generate_all_plots`. (completed 2026-04-22) [viz] [PI]
- [x] Extended `run.sh` with a mode-aware dispatch so `racket_trajectory.py --mode viewer` routes through `mjpython` on macOS, while headless and plot stay on plain Python. (completed 2026-04-22) [repo] [PI]
- [x] Safe repo reorg: `assets/meshes/`, `assets/scenes/`, `checkpoints/`, `docs/` introduced via `git mv`; empty `3D_model/` removed; all XMLs and Python entrypoints updated with backward-compat fallbacks. (completed 2026-04-22) [repo] [PI]
- [x] Added `docs/REPO_LAYOUT.md` (current + target layout, migration log, deferred-move TODOs). (completed 2026-04-22) [repo] [PI]
- [x] Added `docs/PHD_DIRECTIONS.md` (open scientific questions, methodological improvements, novel directions, supervisor asks). (completed 2026-04-22) [phd] [PI]
- [x] Published consolidated project update `project_updates/2026-04-22_project_consolidation_and_racket_viz.md`. (completed 2026-04-22) [repo] [PI]
- [x] Appended 2026-04-22 change-log lines to `matlab_mujoco_parity_master_report.md` and `parity_weekly_technical_tracker.md`. (completed 2026-04-22) [parity] [PI]
- [x] Verification suite passed: preflight OK, all 7 MJCFs compile, racket figure-8 detected, `plot_results.py` regenerates six figures. (completed 2026-04-22) [repo] [PI]

### Next week

- [ ] Implement a sysID loop to fit `example_two_link/matlab_v2_params.py` to MuJoCo rollouts; first acceptance criterion is closing the strict MATLAB-vs-MuJoCo parity gate. (target 2026-04-29) [parity] [PI]
- [ ] Replace the Python bridge's first-order Euler integrator with RK4 in `example_two_link/matlab_v2_dynamics.py`; re-run `compare_signals.py` to separate integrator mismatch from parameter mismatch. (target 2026-04-29) [parity] [PI]
- [ ] Add a `--sweep` mode to `systematic_studies/racket_trajectory.py` that sweeps `--ws-f-hz` and writes a tidy CSV suitable for a peak-speed-vs-frequency plot. (target 2026-04-30) [viz] [PI]
- [ ] Add a top-level `README.md` pointing to `RUN.md`, `docs/REPO_LAYOUT.md`, and this weekly log. (target 2026-04-28) [repo] [PI]
- [ ] Gitignore regenerated artefacts under `systematic_studies/outputs/figures/` and `reports/` that should be rebuilt locally; keep only canonical reference PNGs in version control. (target 2026-04-28) [repo] [PI]

### Carried from past weeks

- [ ] Strict MATLAB-vs-MuJoCo parity gate still failing (`rmse_q ~ 2.49 rad`, `rmse_qdot ~ 13.76 rad/s`, `parity_ready = false`). (carried since 2026-W16) (target 2026-04-29) [parity] [PI]
- [ ] Publish "first timing result" (timing vs velocity with CIs) - blocked on the strict parity gate above. (carried since 2026-W16) (target 2026-05-03) [parity] [PI]
- [ ] Large-scope rename `example_two_link/ -> models/two_link/` with `arm_env.py`, `train_sac*.py`, `run_policy_in_mujoco_viewer.py` relocations - deferred; tracked in `docs/REPO_LAYOUT.md` section 5. (carried since 2026-W17) (target 2026-05-10) [repo] [PI]

### Notes

- Relaxed parity gate continues to pass; it is used only for internal debugging and is NOT a publication claim.
- Dashboard command (added this week): `./run.sh systematic_studies/weekly_dashboard.py` renders all figures + key JSON summaries + this markdown as a portable HTML report under `systematic_studies/outputs/reports/`.

---

## Week 2026-W16 (ending 2026-04-19)

Supporting updates: [matlab_mujoco_parity_master_report.md](matlab_mujoco_parity_master_report.md), [parity_weekly_technical_tracker.md](parity_weekly_technical_tracker.md), [parity_weekly_exec_summary.md](parity_weekly_exec_summary.md).

### Done this week

- [x] Canonical unit contract (radians, rad/s, N*m, m, s) propagated through the systematic-studies pipeline. (completed 2026-04-15) [parity] [PI]
- [x] Added `systematic_studies/compare_signals.py`, `swing_benchmark_mujoco_vs_bridge.py`, `run_validated_timing_sweep.py`. (completed 2026-04-15) [parity] [PI]
- [x] Added `run_native_matlab_parity.py`; verified native MATLAB execution via `/Applications/MATLAB_R2025a.app/bin/matlab` without requiring `matlab` on PATH. (completed 2026-04-15) [parity] [PI]
- [x] Fixed MuJoCo state-unit bug in benchmark (write `qpos` in radians, not degrees). (completed 2026-04-15) [parity] [PI]
- [x] Added end-effector velocity dual-method logging (finite-difference + Jacobian). (completed 2026-04-15) [viz] [PI]
- [x] Added bridge-gate diagnostics in benchmark summary: spike count, jerk outliers, `parity_ready` flag. (completed 2026-04-15) [parity] [PI]

### Next week

(See Week 2026-W17 above.)

### Notes

- Strict gate failing was flagged as the top blocker to a "first timing result".

---

## Week 2026-W11 (ending 2026-03-15)

Supporting update: [2026-03-11_two_link_update.md](2026-03-11_two_link_update.md).

### Done this week

- [x] Introduced `action_mode = residual` (SAC residual on top of analytical MATLAB prior) in `arm_env.py`. (completed 2026-03-11) [rl] [PI]
- [x] Introduced `target_mode = {planar_fixed, random_planar}`, fixing the unreachable-target issue. (completed 2026-03-11) [rl] [PI]
- [x] Patched viewer scripts for robust scene resolution; added `--check-only` preflight mode to `view_dummy_two_link_obj.py`. (completed 2026-03-11) [viz] [PI]
- [x] Tightened `run.sh` routing for macOS `mjpython`. (completed 2026-03-11) [repo] [PI]

### Notes

- Baseline eval success jumped materially after planar-target fix.

---

## Week 2026-W10 (ending 2026-03-08)

Supporting update: [2026-03-04_two_link_update.md](2026-03-04_two_link_update.md).

### Done this week

- [x] First two-link SAC training + eval loop stood up: reward, action, observation spaces, seeds, eval horizon. (completed 2026-03-04) [rl] [PI]
- [x] Produced first `example_two_link/metrics/eval_sac_two_link_arm.json` with baseline metrics. (completed 2026-03-04) [rl] [PI]

### Notes

- Flagged: benchmark target in `two_link_arm.xml` was unreachable, collapsing success rate (addressed in Week 2026-W11).
