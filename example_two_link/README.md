# Two-Link Arm Example

Minimal MuJoCo example: a planar two-link arm with torque actuators. Uses MJCF and follows the [MuJoCo Modeling Guide](https://mujoco.readthedocs.io/en/stable/modeling.html).

## Files

| File | Description |
|------|-------------|
| `two_link_arm.xml` | MJCF model: kinematic tree, default settings, motor actuators |
| `run_example.py` | Loads the model and runs it in the passive viewer |
| `train_sac.py` | SAC training with `--steps`, `--seed`, `--action-mode`; saves to `checkpoints/` |
| `eval.py` | Evaluation over 10 rollouts; saves metrics JSON to `metrics/` |
| `view.py` | Rollout visualization in MuJoCo viewer (mjpython on macOS) |
| `matlab_v2_params.py` | MATLAB_v2 parameter presets + XML-derived approximation |
| `matlab_v2_dynamics.py` | Python port of MATLAB_v2 two-link dynamics (`M, C, G, B`, forward/inverse) |
| `validate_matlab_v2_bridge.py` | Bridge-vs-MuJoCo diagnostics on sampled states |
| `export_unity_txt.py` | TXT/CSV export utility for Unity replay ingestion |

## MJCF modeling concepts used

From the [Modeling documentation](https://mujoco.readthedocs.io/en/stable/modeling.html):

- **Kinematic tree** – nested `body` elements under `worldbody`; child bodies are attached to parents via joints
- **Default settings** – `default` block for `joint` (damping, limited) and `geom` (capsule, rgba, density, friction)
- **Actuator shortcuts** – `motor` elements with `ctrlrange` for torque limits
- **Coordinate frames** – `compiler angle="degree"` and `coordinate="local"` for positions/orientations
- **Saving models** – optional MJB export for faster loading (standalone binary, no XML/mesh dependencies)

## How to run

From the **project root** (parent of `example_two_link/`):

```bash
# Using the project run script (handles venv and mjpython on macOS)
./run.sh example_two_link/run_example.py

# Or with options
./run.sh example_two_link/run_example.py --zero-torque
./run.sh example_two_link/run_example.py --save-mjb
./run.sh example_two_link/run_example.py --model example_two_link/two_link_arm.xml
```

From inside `example_two_link/`:

```bash
cd example_two_link
# Activate venv first, then on macOS use mjpython for the viewer:
mjpython run_example.py
```

## RL experiment pipeline (Cursor Agent paradigm)

From project root:

```bash
# Train direct torque SAC (200k steps, seed 0)
./run.sh example_two_link/train_sac.py --steps 200000 --seed 0 --action-mode torque

# Train hybrid residual SAC on top of the analytical prior
./run.sh example_two_link/train_sac.py --steps 200000 --seed 0 --action-mode residual --target-mode planar_fixed

# Evaluate (10 rollouts, seeds 0,1,2,3,4)
./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_torque_seed0 --seeds 0,1,2,3,4 --action-mode torque

# Evaluate hybrid residual SAC
./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_residual_seed0 --seeds 0,1,2,3,4 --action-mode residual --target-mode planar_fixed

# View rollout
./run.sh example_two_link/view.py --checkpoint example_two_link/checkpoints/sac_two_link_residual_seed0 --action-mode residual --target-mode planar_fixed
```

### Hybrid dynamics mode

`ArmSwingEnv` now supports two controller modes:

- `action-mode torque`: policy outputs full joint torques.
- `action-mode residual`: policy outputs residual torques around an analytical inverse-dynamics prior.

The default target mode for training/evaluation is now `planar_fixed`, which projects the original XML target onto the arm's motion plane. The raw XML target has `y=0.10`, which is off-plane for this 2D hinge setup and therefore unreachable by construction.

### MATLAB_v2 bridge validation

```bash
# Validate bridge using MATLAB defaults
./run.sh example_two_link/validate_matlab_v2_bridge.py --samples 50 --param-source matlab_default

# Validate bridge using parameters approximated from MuJoCo XML
./run.sh example_two_link/validate_matlab_v2_bridge.py --samples 50 --param-source from_xml
```

Validation output is saved to `example_two_link/metrics/bridge_validation.json`.

### Unity-compatible trajectory export (TXT/CSV)

```bash
./run.sh example_two_link/eval.py \
  --checkpoint example_two_link/checkpoints/sac_two_link_seed0 \
  --seeds 0,1,2,3,4 \
  --export-trajectory
```

This produces:
- `example_two_link/exports/trajectory_<checkpoint>.csv`
- `example_two_link/exports/trajectory_<checkpoint>.txt`
- `example_two_link/exports/trajectory_<checkpoint>.json`

Column schema for TXT/CSV:
`episode, step, time_s, q1, q2, qd1, qd2, tau1, tau2, prior_tau1, prior_tau2, applied_tau1, applied_tau2, hand_x, hand_y, hand_z, target_x, target_y, target_z, reward, dist`

Project updates (results, commands, scoring) go in `project_updates/YYYY-MM-DD_two_link_update.md`.

## Requirements

- MuJoCo, Gymnasium, Stable-Baselines3 (`pip install mujoco gymnasium stable-baselines3`)
- On macOS: use `mjpython` (not `python`) for viewer scripts — `run.sh` handles this

## Model structure

```
worldbody
└── shoulder (pos 0 0 1.4)
    ├── joint shoulder_pitch (hinge, axis Y, ±120°)
    ├── geom upperarm (capsule 0.32m, radius 0.03m)
    └── elbow (pos 0.32 0 0)
        ├── joint elbow_pitch (hinge, axis Y, 0–150°)
        ├── geom forearm (capsule 0.26m, radius 0.025m)
        └── site hand (end effector)
site target (goal position)
actuator: 2 motors, ctrlrange ±60 Nm
```
