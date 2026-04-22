# Repository Layout

_Last updated: 2026-04-22 as part of the racket-viz + consolidation update._

This document is the authoritative map of the repository. It captures the
**current state** after the 2026-04-22 safe reorg, the **target layout** for a
later (larger) reorg, a **migration log**, and a **deferred moves** TODO list.

## 1. Guiding principles

1. **Single source of truth per asset.** One canonical MJCF, one canonical
   mesh, one canonical checkpoint path — referenced from everything else.
2. **Run scripts stay stable.** `run.sh`, `RUN.md`, and the commands in
   `systematic_studies/README.md` must keep working across reorgs. Broken
   command lines erode trust faster than a messy root directory.
3. **Safe moves only.** Anything whose reference count is high (e.g. the
   `arm_env.py` import graph, `example_two_link/` paths baked into metrics
   files) is moved only when we can do it in one atomic PR with tests.
4. **Outputs never leave `systematic_studies/outputs/`.** Figures, CSVs, and
   JSON summaries have a single home; reports link into it. The canonical
   report directory is `systematic_studies/outputs/reports/`, populated by
   `systematic_studies/weekly_dashboard.py`.

## 2. Current state (post 2026-04-22 reorg)

```
Mujoco/
|-- RUN.md                      top-level how-to-run guide
|-- EXPERIMENT_PARADIGM.md      experiment paradigm and acceptance gates
|-- run.sh                      venv + mjpython dispatcher
|-- arm_env.py                  SAC Gymnasium env (API unchanged)
|-- train_sac.py                root SAC training entry point (saves to checkpoints/)
|-- train_sac_quick.py          smoke-test SAC runner
|-- run_policy_in_mujoco_viewer.py    viewer runner (resolves checkpoints/)
|-- generate_mjcf_from_json.py  optional MJCF generator
|-- view_mujoco_arm.py          interactive 2-link viewer (uses mujoco_arm.xml)
|-- view_3d_two_link_model.py   loads assets/scenes/two_link_model_scene.xml
|-- view_dummy_two_link_obj.py  loads assets/scenes/dummy_two_link_obj_view.xml
|-- mujoco_arm.xml              interactive 2-link MJCF (root — still referenced)
|
|-- assets/                     NEW: static assets decoupled from code
|   |-- meshes/
|   |   |-- Two_link_model.obj, .mtl
|   |   |-- Two_link_model_obj.obj, .mtl
|   |-- scenes/
|       |-- dummy_two_link_obj_view.xml     (was root)
|       |-- two_link_model_scene.xml        (was root; was broken pointer)
|
|-- checkpoints/                NEW: canonical SAC checkpoint directory
|   |-- sac_two_link_arm.zip
|   |-- sac_two_link_arm_quick.zip
|
|-- docs/                       NEW: long-form engineering / research docs
|   |-- REPO_LAYOUT.md                       (this file)
|   |-- PHD_DIRECTIONS.md                    (future-work research doc)
|
|-- example_two_link/           canonical two-link arm pipeline
|   |-- two_link_arm.xml        single source of truth for the planar arm
|   |-- arm_env bindings, train_sac.py, eval.py, view.py, matlab_v2_*
|   |-- checkpoints/            per-seed training artifacts
|   |-- metrics/                per-checkpoint eval JSON
|   |-- exports/                Unity-replay trajectories
|
|-- example_double_pendulum/    pedagogical double-pendulum demos
|
|-- systematic_studies/         study pipeline (headless + viewer demos)
|   |-- README.md               commands + slide mapping
|   |-- racket_trajectory.py    NEW: racket / figure-8 visualiser
|   |-- mutual_motor_learning.py NEW: two-agent shared control (RT vs Static)
|   |-- swing_benchmark_mujoco_vs_bridge.py
|   |-- run_validated_timing_sweep.py
|   |-- run_native_matlab_parity.py
|   |-- compare_signals.py
|   |-- visualisation/plot_results.py     unified plotting entry point
|   |-- weekly_dashboard.py     NEW: renders the weekly HTML dashboard
|   |-- outputs/                CSV + JSON outputs
|       |-- figures/            all publication PNGs live here
|       |-- reports/            NEW: weekly_dashboard_<ISO-week>_<YYYY-MM-DD>.html reports
|
|-- Matlab_v2/                  MATLAB ground-truth code (unchanged)
|-- project_updates/            week-by-week narrative updates
|   |-- 2026-03-04_two_link_update.md
|   |-- 2026-03-11_two_link_update.md
|   |-- matlab_mujoco_parity_master_report.md
|   |-- parity_weekly_exec_summary.md
|   |-- parity_weekly_technical_tracker.md
|   |-- 2026-04-22_project_consolidation_and_racket_viz.md
```

## 3. Target layout (proposed; NOT executed today)

```
Mujoco/
  README.md                    (new top-level README pointing into RUN.md)
  RUN.md
  EXPERIMENT_PARADIGM.md
  run.sh
  assets/
    meshes/                    (done)
    scenes/                    (done)
  models/
    two_link/                  (from example_two_link/)
    double_pendulum/           (from example_double_pendulum/)
    trunk_arm_wrist/           (current systematic_studies/models/*.xml)
  envs/
    arm_env.py                 (moved from root; unchanged API)
  training/
    train_sac.py               (root + example_two_link reconciled)
    train_sac_quick.py
  evaluation/
    run_policy_in_mujoco_viewer.py
  viewers/
    view_mujoco_arm.py
    view_3d_two_link_model.py
    view_dummy_two_link_obj.py
  systematic_studies/          (unchanged; kept as a lab-notebook style folder)
  Matlab_v2/                   (unchanged; canonical ground truth)
  project_updates/
  checkpoints/
  docs/
```

## 4. Migration log (2026-04-22 reorg)

Executed moves and path updates:

- `mkdir -p assets/meshes assets/scenes checkpoints docs`.
- `rmdir 3D_model` (was empty; viewers that still referenced it now fall
  through to canonical paths via resolver functions).
- `git mv` of mesh files into `assets/meshes/`:
  - `Two_link_model.obj`, `Two_link_model.mtl`
  - `Two_link_model_obj.obj`, `Two_link_model_obj.mtl`
- `git mv` of scene XMLs into `assets/scenes/`:
  - `dummy_two_link_obj_view.xml`
  - `two_link_model_scene.xml`
- `git mv` of root-level checkpoints into `checkpoints/`:
  - `sac_two_link_arm.zip`
  - `sac_two_link_arm_quick.zip`

Reference updates applied in the same commit:

- `assets/scenes/dummy_two_link_obj_view.xml`: mesh path changed to
  `../meshes/Two_link_model.obj`.
- `assets/scenes/two_link_model_scene.xml`: mesh path changed to
  `../meshes/Two_link_model.obj`.
- `example_double_pendulum/double_pendulum_mesh.xml`: `meshdir=".."`
  changed to `meshdir="../assets/meshes"`.
- `example_two_link/view_matlab_model.xml` and
  `example_two_link/view_mesh.xml`: mesh path changed from
  `../Two_link_model.obj` to `../assets/meshes/Two_link_model.obj`.
- `view_dummy_two_link_obj.py::resolve_asset()`: canonical target is now
  `assets/scenes/dummy_two_link_obj_view.xml`, with root and `3D_model/`
  fallbacks for older checkouts.
- `view_3d_two_link_model.py`: resolves against
  `assets/scenes/two_link_model_scene.xml` first, with fallbacks.
- `train_sac.py`: saves to `checkpoints/sac_two_link_arm` (creates
  `checkpoints/` if missing).
- `run_policy_in_mujoco_viewer.py`: default checkpoint resolves to
  `checkpoints/sac_two_link_arm` with a legacy root fallback.
- `example_two_link/eval.py` and `example_two_link/view.py`: if the user
  passes a bare stem checkpoint (e.g. `sac_two_link_arm`), fall through to
  `checkpoints/<stem>[.zip]` before erroring.
- `run.sh`: added dispatch so `systematic_studies/racket_trajectory.py`
  routes through `mjpython` only when `--mode viewer` is used.
- `RUN.md` and `systematic_studies/README.md`: updated command examples
  to reflect the new paths.

Verification run after the reorg (see the 2026-04-22 project update for
details):

- `./run.sh view_dummy_two_link_obj.py --check-only` -> Preflight OK.
- Compile-only load of every migrated XML -> `nmesh=1`.
- `./run.sh systematic_studies/racket_trajectory.py --protocol workspace_figure8 --mode plot --steps 10000` -> figure-8 detected, figures written.
- `python systematic_studies/visualisation/plot_results.py` -> 6 figures regenerated, including the new racket trajectory pair.

## 5. Deferred moves (tracked as TODOs)

- Rename `example_two_link/` -> `models/two_link/`. Blast radius: imports
  in many modules (`example_two_link.matlab_v2_*`, `example_two_link.export_unity_txt`),
  hardcoded paths in JSON metrics, and every `RUN.md` command.
- Move `arm_env.py` -> `envs/arm_env.py`. Requires updating many imports
  across training, eval, and viewer scripts.
- Consolidate root `train_sac.py` with `example_two_link/train_sac.py`.
  Only one should own the SAC training entrypoint.
- Move `view_*.py` from root into `viewers/` and `run_policy_in_mujoco_viewer.py`
  into `evaluation/`. Low-risk but requires updating `run.sh` allow-list.
- Decide whether `mujoco_arm.xml` stays at root or moves to
  `assets/scenes/mujoco_arm.xml`. Currently referenced by `view_mujoco_arm.py`.
- Add a top-level `README.md` pointing to `RUN.md` and this document.
- Gitignore `systematic_studies/outputs/` regenerated artifacts that
  users should rebuild locally; keep only canonical reference PNGs / JSON
  checked in.

## 6. How to validate after any future reorg

Run this minimal sanity suite from the repo root:

```bash
./run.sh view_dummy_two_link_obj.py --check-only
./run.sh systematic_studies/racket_trajectory.py --protocol workspace_figure8 --mode plot --steps 10000
python systematic_studies/visualisation/plot_results.py
```

All three must succeed and the figures under
`systematic_studies/outputs/figures/` must regenerate.
