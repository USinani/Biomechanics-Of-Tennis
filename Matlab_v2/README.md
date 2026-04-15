# Matlab_v2 — analytical swing benchmark (PhD / MuJoCo parity)

MATLAB is the **physics-grounded reference** for two-link / double-pendulum swing dynamics; MuJoCo validates and extends; RL explores policies. This package provides one canonical forward simulation, sweeps, exports, and comparison to Python-generated CSVs.

## Layout

| Path | Role |
|------|------|
| [`default_params.m`](default_params.m) | Single `params` struct (SI units, `x = [q1;q2;dq1;dq2]` rad, rad/s) |
| [`run_swing_sim.m`](run_swing_sim.m) | Integrate open-loop torques (semi-implicit Euler, matches [`example_two_link/matlab_v2_dynamics.py`](../example_two_link/matlab_v2_dynamics.py)) |
| [`run_batch_experiments.m`](run_batch_experiments.m) | Struct-array / cell overrides → many runs + exports |
| [`benchmark_mujoco_parity.m`](benchmark_mujoco_parity.m) | Load `systematic_studies` CSV, RMSE vs bridge/MuJoCo, overlay plots |
| `dynamics/` | `mass_matrix`, `coriolis_terms`, `gravity_terms`, `two_link_tennis_model`, `two_link_dynamics`, `compute_forward_dynamics`, FK / EE velocity |
| `controls/` | `control_profile`, torque primitives, `pronation_profile` (Option A kinematic proxy) |
| `analysis/` | Metrics, energy transfer, plots, heatmaps |
| `export/` | `states.csv`, `controls.csv`, `derived_outputs.csv`, `metrics.json`, `config.json`, `summary.mat` |
| `experiments/` | `exp_baseline_swing`, `exp_timing_sweep`, `exp_initial_angle_sweep`, `exp_pronation_sweep`, `exp_mujoco_benchmark` |
| `legacy/` | Three-link + ball + [`run_tennis_inverse_dynamics_demo.m`](legacy/run_tennis_inverse_dynamics_demo.m) (prescribed paths) |

Outputs: `outputs/<experiment_name>/<run_id>/`.

## Quick start

```matlab
cd Matlab_v2   % or addpath(genpath('.../Matlab_v2'))
main           % baseline driven swing (tau_amp = 5 N·m)
```

Or:

```matlab
params = default_params();
params.control.tau_amp = 5;
[t, x, u_hist, y, metrics] = run_swing_sim(params);
```

Enable export:

```matlab
params.export.enable = true;
params.export.experiment_name = 'my_run';
params.export.save_plots = true;
run_swing_sim(params);
```

## Sweeps

```matlab
exp_timing_sweep
exp_initial_angle_sweep
exp_pronation_sweep
```

Each writes runs under `outputs/<experiment>/`.

## MuJoCo parity benchmark

1. Generate timeseries (from repo root):

   `python systematic_studies/swing_benchmark_mujoco_vs_bridge.py`

2. In MATLAB:

   ```matlab
   benchmark_mujoco_parity
   ```

   Optional: `benchmark_mujoco_parity('tau_amp', 5, 'q1_deg', 5, 'q2_deg', 55)` to match CLI args.

Results: `outputs/mujoco_benchmark/<run_id>/parity_summary.json`, `.mat`, `parity_overlay.png`.

## Legacy inverse-dynamics demo

Prescribed minimum-jerk joint paths, inverse dynamics, ball model:

```matlab
run_tennis_simulation   % dispatches to legacy/run_tennis_inverse_dynamics_demo.m
```

## Tests

```matlab
test_all_functions
```

## Requirements

MATLAB R2018b+ recommended (`jsonencode`, `table`/`writetable`, `inputParser` name-value).

## Trunk / whole-body

`params.trunk` holds placeholders for future proximal DOF; the two-link core ignores them but they are carried in `config.json` for downstream extension.
