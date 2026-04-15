# Systematic studies

Reproducible sweeps and benchmarks aligned with PhD systematic-study tasks. This folder **imports** existing modules from `example_two_link/` (MATLAB_v2 Python dynamics) and uses MJCF from `example_double_pendulum/` and `example_two_link/` without modifying them.

## Slide mapping

| Task | Script / artifact |
|------|-------------------|
| Double pendulum: joint angles and timing | `double_pendulum_sweep.py` (grid over `q1`,`q2`, optional elbow delay steps) |
| MATLAB model vs MuJoCo (same window, torques) | `swing_benchmark_mujoco_vs_bridge.py` (time series + RMSE; uses Python port of MATLAB_v2, not the MATLAB engine) |
| Pronation/supination vs speed proxy | `models/trunk_arm_wrist.xml` + `pronation_supination_sweep.py` |
| Whole-body rotation (trunk + arm) | `models/trunk_arm_wrist.xml` + `run_trunk_arm_demo.py` |

## Visual demos (MuJoCo viewer)

Sweeps and the swing **benchmark** are headless (CSV/JSON). For on-screen motion:

```bash
# All scenes in sequence (double pendulum → two-link passive → trunk+arm+wrist); close each window to continue
./run.sh systematic_studies/visual_showcase.py

# Single scene
./run.sh systematic_studies/visual_showcase.py --scene pendulum
./run.sh systematic_studies/visual_showcase.py --scene two_link
./run.sh systematic_studies/visual_showcase.py --scene trunk

# Same torque law as swing_benchmark; default tau_amp=0 (passive, stable). Add e.g. --tau-amp 1.2 for a gentle driven swing.
./run.sh systematic_studies/view_swing_protocol.py

# Optional: cap scene duration (seconds)
./run.sh systematic_studies/visual_showcase.py --seconds 45
```

Interactive muscle demo (separate terminal, key controls): `./run.sh example_double_pendulum/muscle_control.py`

### Interactive parameter lab (terminal + viewer)

`sim_parameter_lab.py` opens the passive viewer and reads **single-key commands** from stdin (same terminal idea as `muscle_control.py`): move the **double-pendulum pivot height** (`models/double_pendulum_lab.xml` adds a slide DOF), nudge joint angles, scale gravity, reset, and print state. Presets: `pendulum` (lab XML), `two_link`, `trunk`.

```bash
# Default: double pendulum with adjustable anchor height; real-time pacing unless --no-realtime
./run.sh systematic_studies/sim_parameter_lab.py
./run.sh systematic_studies/sim_parameter_lab.py --preset two_link
./run.sh systematic_studies/sim_parameter_lab.py --preset trunk

# Smoke (no window)
./run.sh systematic_studies/sim_parameter_lab.py --headless
```

**Mouse / “Unity-like” nudges:** the script turns on MuJoCo **perturbation** visualization. In the viewer, use the standard **interact / perturb** mode (toolbar and shortcuts depend on MuJoCo version) to select a body and apply mouse drags—handy for impulsive tests alongside keyboard nudges. Joint limits and passive dynamics still apply.

Press `h` in the terminal for the key map; `q` stops the loop (then close the viewer).

## Outputs

CSV/JSON are written under `systematic_studies/outputs/` (ignored by git except this policy).

### Publication plots for slides

Use the plotting module to convert sweep/benchmark CSV outputs into presentation-ready PNG figures (white background, tight layout, ~300 dpi):

```bash
python systematic_studies/visualisation/plot_results.py
```

By default, this reads from `systematic_studies/outputs/` and writes figures to `systematic_studies/outputs/figures/`:

- `timing_vs_velocity.png`: timing delay vs end-effector velocity, with peak annotation (`Optimal Timing Delay`)
- `energy_vs_timing.png`: normalized energy-transfer efficiency trend vs timing delay
- `benchmark_comparison.png`: MATLAB (dashed) vs MuJoCo (solid) overlay for joint angles and velocities
- `summary_figure.png`: compact multi-panel overview for quick insertion into presentation slides

If needed, you can point to a different outputs directory:

```bash
python systematic_studies/visualisation/plot_results.py --csv-path systematic_studies/outputs
```

### Parity diagnostics and gated analysis

```bash
# 1) Generate benchmark CSV/summary with canonical MuJoCo + bridge columns
python systematic_studies/swing_benchmark_mujoco_vs_bridge.py --steps 500 --param-source from_xml

# 2) Compare q/qdot signals (bridge as temporary reference; use matlab prefix when available)
python systematic_studies/compare_signals.py \
  --matlab-csv systematic_studies/outputs/swing_benchmark_timeseries.csv \
  --matlab-prefix bridge \
  --mujoco-csv systematic_studies/outputs/swing_benchmark_timeseries.csv \
  --mujoco-prefix mujoco

# 3) Run timing sweeps only if parity_ready=true in compare_signals_metrics.json
python systematic_studies/run_validated_timing_sweep.py --outputs-dir systematic_studies/outputs
```

### Native MATLAB parity (no PATH requirement)

If MATLAB is installed as an app bundle on macOS but `matlab` is not on PATH, use:

```bash
python systematic_studies/run_native_matlab_parity.py
```

This script auto-detects MATLAB (for example `/Applications/MATLAB_R2025a.app/bin/matlab`), runs `Matlab_v2/benchmark_mujoco_parity.m`, and then runs `compare_signals.py` on the generated native MATLAB parity CSV.

Optional explicit binary:

```bash
python systematic_studies/run_native_matlab_parity.py --matlab-bin /Applications/MATLAB_R2025a.app/bin/matlab
```

## Commands (from repo root)

```bash
# Double pendulum parameter sweep (small demo grid)
./run.sh systematic_studies/double_pendulum_sweep.py --steps 500

# MuJoCo vs analytical bridge, same dt and torque schedule
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py --steps 300 --param-source from_xml

# Pronation/supination sweep (default: passive / gravity-only; add --active-torque for driven swing)
./run.sh systematic_studies/pronation_supination_sweep.py --wrist-deg -30 0 30 --steps 400

# Viewer: trunk + arm + wrist (macOS: mjpython via run.sh)
./run.sh systematic_studies/run_trunk_arm_demo.py
```

## Assumptions

- **Bridge**: `example_two_link/matlab_v2_dynamics.py` is the reference “MATLAB” dynamics for comparison.
- **Angles and velocities at runtime**: even if MJCF uses `compiler angle="degree"` for XML parsing, MuJoCo runtime state uses SI (`qpos` in rad, `qvel` in rad/s). The benchmark writes canonical rad/rad-s columns and keeps legacy degree columns for plotting compatibility.
- **Pronation/racket metrics**: tip speeds are **engineering proxies** for systematic exploration, not validated sports biomechanics.
- **MuJoCo vs bridge RMSE**: `params_from_mujoco_xml` is an approximate inertia/mass model; trajectories will **diverge** from MuJoCo’s exact multibody dynamics. The benchmark script is for **aligned protocols** (same dt, torques, logging); tighten agreement by calibrating parameters or extracting properties from MuJoCo.
