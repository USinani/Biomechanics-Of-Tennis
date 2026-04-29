# How to Run mujoco_arm.xml

## 1. Use the virtual environment

All commands must use the project's `.venv`:

```bash
cd /Users/uljan/Desktop/Mujoco
source .venv/bin/activate   # or use ./run.sh
```

Or use the `run.sh` helper:

```bash
./run.sh view_mujoco_arm.py
./run.sh train_sac_quick.py
./run.sh run_policy_in_mujoco_viewer.py
./run.sh example_two_link/train_sac.py --action-mode residual --target-mode planar_fixed
./run.sh systematic_studies/run_trunk_arm_demo.py --scripted-trunk --scripted-arm
./run.sh systematic_studies/visual_showcase.py
```

**Systematic studies** (sweeps/benchmarks, headless; visual demos in viewer): see [systematic_studies/README.md](systematic_studies/README.md).

**Racket / end-effector figure-8 (infinity) trajectory** (cleanest single-script demo):

```bash
# Headless: CSV + JSON only
./run.sh systematic_studies/racket_trajectory.py --protocol workspace_figure8 --mode headless --steps 10000

# Plot: also write racket_trajectory_xz.png and racket_trajectory_joint_vs_time.png
./run.sh systematic_studies/racket_trajectory.py --protocol workspace_figure8 --mode plot --steps 10000

# Viewer: open MuJoCo viewer alongside live capture (macOS uses mjpython)
./run.sh systematic_studies/racket_trajectory.py --protocol workspace_figure8 --mode viewer --steps 10000
```

To generate presentation-ready figures from systematic study CSV outputs:

```bash
python systematic_studies/visualisation/plot_results.py
```

**Weekly dashboard** (regenerate all figures + render a single portable HTML report with embedded PNGs, JSON summary tables, and the current-week markdown):

```bash
# Build + open the HTML report in your default browser
./run.sh systematic_studies/weekly_dashboard.py

# Build only; do not open a browser (useful over SSH / CI)
./run.sh systematic_studies/weekly_dashboard.py --no-open

# Override the report date (e.g. rebuild last Monday's dashboard)
./run.sh systematic_studies/weekly_dashboard.py --no-open --date 2026-04-22
```

Output path: `systematic_studies/outputs/reports/weekly_dashboard_<ISO-week>_<YYYY-MM-DD>.html`.

**Important (macOS):** The MuJoCo viewer requires `mjpython`, not `python`. The `run.sh` script automatically uses `mjpython` for viewer scripts on macOS.

## 2. View mujoco_arm.xml in the MuJoCo GUI

```bash
./run.sh view_mujoco_arm.py
```

or manually:

```bash
source .venv/bin/activate
# On macOS, viewer must use mjpython:
mjpython view_mujoco_arm.py
```

This loads `mujoco_arm.xml` and opens the interactive MuJoCo viewer. Close the window to exit.

## 2b. Canonical OBJ viewer flow (root command)

Use this sequence for the dummy two-link OBJ integration test:

```bash
# 1) Preflight compile check only (no viewer window)
./run.sh view_dummy_two_link_obj.py --check-only

# 2) Launch the viewer from root
./run.sh view_dummy_two_link_obj.py
```

Notes:
- Do not drag `.obj` directly into MuJoCo GUI.
- The wrapper XML (`dummy_two_link_obj_view.xml`) references `Two_link_model.obj`.
- `view_dummy_two_link_obj.py` auto-resolves both root and legacy `3D_model/` XML locations.

## 3. Run RL training

```bash
./run.sh train_sac_quick.py        # quick test (~10k steps)
./run.sh train_sac.py              # full training (~300k steps)
./run.sh example_two_link/train_sac.py --steps 200000 --seed 0 --action-mode residual --target-mode planar_fixed
./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_residual_seed0 --action-mode residual --target-mode planar_fixed
```

`example_two_link/train_sac.py` supports both direct torque control (`--action-mode torque`) and hybrid residual control (`--action-mode residual`). For the two-link planar model, use `--target-mode planar_fixed` or `random_planar`; the raw XML target is off-plane and not exactly reachable.

## 4. Visualize trained policy

After training (or if `checkpoints/sac_two_link_arm.zip` exists):

```bash
./run.sh run_policy_in_mujoco_viewer.py
```

## 5. Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: mujoco` | Use `.venv/bin/python` or `./run.sh` |
| `RuntimeError: launch_passive requires mjpython on macOS` | Use `mjpython view_mujoco_arm.py` or `./run.sh view_mujoco_arm.py` |
| No venv | `python -m venv .venv && .venv/bin/pip install mujoco gymnasium stable-baselines3` |
