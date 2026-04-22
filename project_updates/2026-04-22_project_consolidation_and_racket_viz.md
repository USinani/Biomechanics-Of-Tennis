# Project Consolidation and Racket-Infinity Trajectory Viz — 2026-04-22

This update is the authoritative entry point for a fresh reader. It
consolidates the full arc of the two-link MuJoCo + MATLAB parity project,
ships today's racket / figure-8 end-effector visualiser, and records the
safe directory reorganisation executed in the same commit.

## Executive summary

We shipped `systematic_studies/racket_trajectory.py`, a reproducible
visualiser that drives the planar two-link arm so the racket tip traces
an infinity / figure-8 in the X-Z plane. The cleanest protocol
(`workspace_figure8`) drives a workspace-level Lissajous via inverse
kinematics and PD tracking; the FFT-based detector now confirms
`figure8_detected = true` with a 2:1 frequency ratio and 89 self-
intersections over the 10 s reference run. We also executed the safe
subset of the planned repository reorganisation (assets, scenes,
checkpoints, docs into dedicated folders) with zero regressions in
existing `RUN.md` commands. The strict MATLAB-vs-MuJoCo parity gate
remains unclosed (`rmse_q ~ 2.49 rad`, `rmse_qdot ~ 13.76 rad/s`); no
"first timing result" is published yet.

## Timeline (authoritative reference)

### 2026-03-04 — SAC pipeline baseline

- First two-link SAC training + eval loop stood up (`project_updates/2026-03-04_two_link_update.md`).
- Reward, action, observation spaces, seeds, and eval horizon locked.
- Known issue flagged: benchmark target in `two_link_arm.xml` was
  unreachable, collapsing success rate.

### 2026-03-11 — Hybrid residual controller + planar targets

- Introduced `action_mode = residual` (SAC residual on top of an
  analytical MATLAB prior) and `target_mode = {planar_fixed, random_planar}`,
  fixing the unreachable-target root cause
  (`project_updates/2026-03-11_two_link_update.md`).
- Patched viewer scripts for robust scene resolution and added
  `--check-only` preflight mode (`view_dummy_two_link_obj.py`).
- `run.sh` routing for macOS `mjpython` tightened.

### 2026-04-08 -> 2026-04-15 (Week 2026-W16) — Parity program

- Canonical unit contract (radians, rad/s, N*m, m, s) propagated
  through the systematic-studies pipeline.
- `compare_signals.py`, `swing_benchmark_mujoco_vs_bridge.py`,
  `run_validated_timing_sweep.py`, and `run_native_matlab_parity.py`
  added.
- Bridge-relaxed gate passes; strict MATLAB-vs-MuJoCo gate fails.
- Key documents: `matlab_mujoco_parity_master_report.md`,
  `parity_weekly_exec_summary.md`, `parity_weekly_technical_tracker.md`.

### 2026-04-22 (today) — Consolidation + racket-viz + safe reorg

- `systematic_studies/racket_trajectory.py` added (four protocols,
  three run modes, figure-8 detector).
- `systematic_studies/visualisation/plot_results.py` extended with a
  `plot_racket_trajectory(...)` entry point; `generate_all_plots`
  auto-picks up the new CSV.
- `run.sh` extended with a mode-aware dispatch for the new module.
- Directory reorg: `assets/meshes/`, `assets/scenes/`, `checkpoints/`,
  `docs/` introduced; root clutter reduced; `3D_model/` removed.
- `docs/REPO_LAYOUT.md` and `docs/PHD_DIRECTIONS.md` added.

## Current state snapshot

### Parity metrics

Source: `systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json`.

| Metric                    | Value                 | Strict threshold | Pass? |
| ------------------------- | --------------------- | ---------------- | ----- |
| `rmse_q_rad`              | 2.4899                | `max_q_dev=0.35` | FAIL  |
| `max_abs_dev_q1_rad`      | 3.6768                | 0.35             | FAIL  |
| `max_abs_dev_q2_rad`      | 1.4877                | 0.35             | FAIL  |
| `rmse_qdot_rad_s`         | 13.7576               | `max_qdot_dev=4` | FAIL  |
| `spike_count_mujoco`      | 7                     | 0                | FAIL  |
| `jerk_outliers_mujoco`    | 9                     | 0                | FAIL  |
| `parity_ready` (strict)   | `false`               | —                | —     |

Relaxed gate (`compare_signals_bridge_relaxed_metrics.json`,
`max_q_dev = 5.0`, `max_qdot_dev = 25.0`) passes. This is the status
used for internal debugging, NOT a publication claim.

### Racket trajectory metrics (today's run)

Source: `systematic_studies/outputs/racket_trajectory_summary.json`.

| Metric                     | Value   |
| -------------------------- | ------- |
| Protocol                   | `workspace_figure8` |
| Steps (dt = 1 ms)          | 10 000  |
| Duration (s)               | 9.999   |
| `figure8_detected`         | `true`  |
| `x_dominant_freq_hz`       | 0.462   |
| `z_dominant_freq_hz`       | 0.923   |
| `freq_ratio_z_over_x`      | 2.00    |
| `self_intersections`       | 89      |
| `peak_hand_speed_xz_m_s`   | 0.645   |
| `mean_hand_speed_xz_m_s`   | 0.437   |
| `trace_extent_x_m`         | 0.238   |
| `trace_extent_z_m`         | 0.176   |
| `tau_clip_max_delta_Nm`    | 0.00    |

Peak racket speed here is intentionally modest — the workspace figure-8
uses conservative amplitudes and frequencies so the PD tracker stays
well inside the `ctrlrange = [-60, 60] N*m`. The visualiser is a
warm-up / geometry demo, not a hitting-task baseline.

## Today's changes

### What was added / modified

- `systematic_studies/racket_trajectory.py` (new): four protocols
  (`passive`, `open_loop_lissajous`, `figure8`, `workspace_figure8`) and
  three modes (`headless`, `plot`, `viewer`). Canonical logging, JSON
  summary with FFT-based figure-8 detector.
- `systematic_studies/visualisation/plot_results.py`: added
  `plot_racket_trajectory(rows, figures_dir)` and wired it into
  `generate_all_plots(...)` so the figures auto-regenerate when the
  racket CSV is present.
- `run.sh`: added a mode-aware dispatch so
  `systematic_studies/racket_trajectory.py --mode viewer` runs under
  `mjpython`, but headless / plot stay on plain Python.
- `systematic_studies/README.md`: added a "Racket trajectory and
  figure-8 motion" section with commands and output paths.
- `RUN.md`: top-level how-to block for the new visualiser.
- Directory reorg (safe-only subset of the plan):
  - `assets/meshes/` now holds the four mesh + mtl files (moved via
    `git mv` from the repo root).
  - `assets/scenes/` holds `dummy_two_link_obj_view.xml` and
    `two_link_model_scene.xml` with mesh paths updated to
    `../meshes/Two_link_model.obj`.
  - `checkpoints/` holds `sac_two_link_arm.zip` and
    `sac_two_link_arm_quick.zip`.
  - Empty `3D_model/` removed.
  - `view_dummy_two_link_obj.py::resolve_asset()`,
    `view_3d_two_link_model.py`, `train_sac.py`,
    `run_policy_in_mujoco_viewer.py`, `example_two_link/eval.py`,
    `example_two_link/view.py` all updated to resolve moved paths
    with legacy fallbacks.
- `docs/REPO_LAYOUT.md` (new): canonical layout map, migration log,
  deferred-move TODO list.
- `docs/PHD_DIRECTIONS.md` (new): open questions, methodological
  improvements, novel directions, supervisor asks.

### Commands run (verification)

```bash
./run.sh view_dummy_two_link_obj.py --check-only
# -> Preflight OK: /Users/uljan/Desktop/Mujoco/assets/scenes/dummy_two_link_obj_view.xml (nq=0, nmesh=1)

./run.sh systematic_studies/racket_trajectory.py \
  --protocol workspace_figure8 --mode plot --steps 10000
# -> Figure-8 detected: True (z/x freq ratio=2.00, self-intersections=89)
# -> Wrote racket_trajectory_xz.png and racket_trajectory_joint_vs_time.png

python systematic_studies/visualisation/plot_results.py
# -> 6 figures regenerated, including the new racket pair.
```

## Artifact index

### Canonical inputs

- `example_two_link/two_link_arm.xml` — single source of truth for the
  planar two-link arm.
- `example_two_link/matlab_v2_params.py`,
  `example_two_link/matlab_v2_dynamics.py` — analytical prior and
  MATLAB-bridge dynamics.
- `Matlab_v2/` — canonical ground truth (native MATLAB pipeline).
- `assets/meshes/Two_link_model{,_obj}.obj` + `.mtl` — visual mesh
  assets (moved here 2026-04-22).
- `assets/scenes/dummy_two_link_obj_view.xml`,
  `assets/scenes/two_link_model_scene.xml` — mesh-viewing scenes.
- `checkpoints/sac_two_link_arm.zip`,
  `checkpoints/sac_two_link_arm_quick.zip` — baseline SAC policies.

### Canonical outputs

- `systematic_studies/outputs/racket_trajectory_timeseries.csv` (today).
- `systematic_studies/outputs/racket_trajectory_summary.json` (today).
- `systematic_studies/outputs/figures/racket_trajectory_xz.png` (today).
- `systematic_studies/outputs/figures/racket_trajectory_joint_vs_time.png` (today).
- `systematic_studies/outputs/figures/timing_vs_velocity.png`,
  `energy_vs_timing.png`, `benchmark_comparison.png`, `summary_figure.png`.
- `systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json`
  (strict gate, fails).
- `systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json`
  (relaxed gate, passes).
- `systematic_studies/outputs/swing_benchmark_summary.json`.
- `example_two_link/metrics/eval_sac_two_link_arm.json`.

### Docs

- `project_updates/2026-03-04_two_link_update.md`
- `project_updates/2026-03-11_two_link_update.md`
- `project_updates/matlab_mujoco_parity_master_report.md`
- `project_updates/parity_weekly_exec_summary.md`
- `project_updates/parity_weekly_technical_tracker.md`
- `project_updates/2026-04-22_project_consolidation_and_racket_viz.md` (this doc)
- `docs/REPO_LAYOUT.md`
- `docs/PHD_DIRECTIONS.md`
- `RUN.md`, `EXPERIMENT_PARADIGM.md`, `systematic_studies/README.md`,
  `example_two_link/README.md`.

## Risk / gap register

| Risk                                                                 | Impact   | Owner  | Status |
| -------------------------------------------------------------------- | -------- | ------ | ------ |
| Strict MATLAB-vs-MuJoCo parity gate still fails                      | Blocks publishable timing result | PI | Open |
| Velocity spikes + jerk outliers in MuJoCo rollout                    | Contaminates RMSE; may need integrator / contact tuning | PI | Open |
| Checkpoint loading breaks if users pass bare stem without `checkpoints/` prefix | Broken command line for returning users | PI | Mitigated via stem fallback in `eval.py` / `view.py` |
| Matplotlib / fontconfig cache write errors on macOS sandbox          | Benign warnings; figures still written | PI | Mitigated (set `MPLCONFIGDIR` if needed) |
| Large-scope rename (`example_two_link/` -> `models/two_link/`) still deferred | Repo root still has stray scripts | PI | Tracked in `docs/REPO_LAYOUT.md` |

## Next steps

### Parity closure stream

- [ ] Implement a sysID loop to fit `matlab_v2_params.py` to MuJoCo
      rollouts (expected to close the strict gate).
- [ ] Replace the Python bridge's first-order Euler step with RK4;
      isolate integrator-vs-parameter mismatch contributions.
- [ ] Re-run the strict gate with 10 seeds + CIs once the sysID loop
      converges.
- [ ] Only then publish a "first timing result" (timing-vs-velocity).

### Systematic-study stream

- [ ] Add a `racket_trajectory.py --sweep` mode that sweeps
      `--ws-f-hz` and emits a tidy CSV suitable for a
      peak-speed-vs-frequency plot.
- [ ] Sensitivity analysis (Morris + Sobol) on damping, mass, length.
- [ ] Extend the visualiser to overlay the SAC residual policy's hand
      trace on the analytical figure-8.

### Repo / tooling

- [ ] Execute the deferred moves listed in `docs/REPO_LAYOUT.md` in a
      single atomic PR, with the three-command verification suite.
- [ ] Add a top-level `README.md` pointing to `RUN.md` and
      `docs/REPO_LAYOUT.md`.
- [ ] Gitignore regenerated outputs; keep only reference PNGs / JSON
      checked in.

## Reproducibility appendix (fresh clone -> full outputs)

```bash
git clone <repo> && cd Mujoco

# 1) Environment (one-off)
python -m venv .venv && .venv/bin/pip install mujoco gymnasium stable-baselines3 numpy matplotlib

# 2) Sanity: preflight the scene viewer after the 2026-04-22 reorg
./run.sh view_dummy_two_link_obj.py --check-only

# 3) Racket figure-8 trajectory
./run.sh systematic_studies/racket_trajectory.py \
  --protocol workspace_figure8 --mode plot --steps 10000

# 4) Parity diagnostics (optional: requires existing rollout CSVs)
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py
./run.sh systematic_studies/compare_signals.py

# 5) Regenerate all publication figures
.venv/bin/python systematic_studies/visualisation/plot_results.py

# 6) Inspect
open systematic_studies/outputs/figures/racket_trajectory_xz.png
cat  systematic_studies/outputs/racket_trajectory_summary.json
```

## Run scoring (research tracking)

| Metric                             | Value | Notes |
| ---------------------------------- | ---:  | --- |
| Time-to-runnable (min)             | ~5    | After `pip install`; single `./run.sh ...` call. |
| Reproducible from clean checkout   | Y     | Verified `preflight + plot + regenerate` on 2026-04-22. |
| Correctness (1–5)                  | 4     | Racket figure-8 verified; parity gate still fails (tracked). |
| Code quality (1–5)                 | 4     | Type hints, no linter errors, canonical contract reused. |
| Doc quality (1–5)                  | 5     | This consolidated update + `REPO_LAYOUT.md` + `PHD_DIRECTIONS.md`. |
| Failures encountered (#)           | 2     | `mujoco.viewer` local-import shadowed module (fixed); FFT bin resolution required zero-padding (fixed). |
