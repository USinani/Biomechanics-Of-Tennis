# Two-Link MuJoCo Experiment Update — 2026-03-11

## 1) What changed
- Added a hybrid control path in `arm_env.py`:
  - `action_mode="torque"` keeps the original pure-RL torque policy.
  - `action_mode="residual"` adds an analytical inverse-dynamics prior and lets RL learn residual torques.
- Added target handling modes in `arm_env.py`:
  - `fixed`
  - `planar_fixed`
  - `random_planar`
- Fixed a benchmark design issue:
  - The XML target in `example_two_link/two_link_arm.xml` is at `y=0.10`, but the arm moves only in the X-Z plane around the Y axis.
  - This made the original task exactly unreachable and explains the previous `~0.100 m` final-distance floor.
  - `planar_fixed` now projects that target onto the reachable plane (`y=0.0`).
- Extended training/eval CLI:
  - `example_two_link/train_sac.py` now accepts `--action-mode`, `--target-mode`, `--residual-limit`, `--controller-param-source`.
  - `example_two_link/eval.py` now accepts the same environment configuration flags.
- Extended rollout export schema in `example_two_link/export_unity_txt.py` with:
  - prior torque
  - applied torque
  - target coordinates
- Updated docs:
  - `example_two_link/README.md`
  - `RUN.md`

## 2) How to run (from project root)
### Hybrid residual SAC smoke train
```bash
./run.sh example_two_link/train_sac.py \
  --steps 200 \
  --seed 0 \
  --action-mode residual \
  --target-mode planar_fixed \
  --out example_two_link/checkpoints/sac_two_link_hybrid_smoke
```

### Hybrid residual SAC evaluation
```bash
./run.sh example_two_link/eval.py \
  --checkpoint example_two_link/checkpoints/sac_two_link_hybrid_smoke \
  --action-mode residual \
  --target-mode planar_fixed \
  --out example_two_link/metrics/eval_sac_two_link_hybrid_smoke.json
```

### Full hybrid run target
```bash
./run.sh example_two_link/train_sac.py \
  --steps 200000 \
  --seed 0 \
  --action-mode residual \
  --target-mode planar_fixed \
  --controller-param-source from_xml
```

### Pure torque baseline on a reachable target
```bash
./run.sh example_two_link/train_sac.py \
  --steps 200000 \
  --seed 0 \
  --action-mode torque \
  --target-mode planar_fixed
```

## 3) Experiment details
- Environment: `example_two_link/two_link_arm.xml`
- Motion plane: X-Z plane (hinges rotate about the Y axis)
- Hybrid prior:
  - planar inverse kinematics to target
  - desired acceleration from PD in joint space
  - analytical inverse dynamics from `example_two_link/matlab_v2_dynamics.py`
- Analytical parameter source: `from_xml` by default for hybrid mode
- Residual action range: `[-20, 20] Nm` per joint
- Full actuator limit: `[-60, 60] Nm` per joint
- Observation:
  - base 15D state for torque mode
  - 19D state for residual mode (adds desired joint angles and prior torque)

## 4) Results
### Structural finding
- Old benchmark floor: `mean_final_dist ≈ 0.1001 m`
- Cause: target had off-plane displacement `y=0.10 m`
- Fix: use `target_mode=planar_fixed` or `random_planar`

### Hybrid smoke train/eval
From `example_two_link/metrics/eval_sac_two_link_hybrid_smoke.json`:
- Mean return: `-15.67 ± 1.43`
- Mean final distance: `0.0738 ± 0.0000 m`
- Success rate: `0.00%`

Interpretation:
- The hybrid residual pipeline now trains, saves, loads, and evaluates end-to-end.
- Even a 200-step smoke run improves the reachable-task distance relative to the previous unreachable baseline floor.
- The analytical prior helps but is not yet sufficient for stable reach-and-hold success over the full episode.

## 5) Problems + fixes
- Problem: benchmark target was unreachable by geometry.
- Fix: added reachable target modes and made `planar_fixed` the recommended default for experiments.

- Problem: hybrid controller needed a clean integration path into the existing RL scripts.
- Fix: unified the environment/training/eval CLI instead of adding a separate forked script tree.

- Problem: Matplotlib/font cache warnings appear on this machine.
- Fix: non-fatal; training and evaluation completed.

## 6) Next steps
- [ ] Run 200k-step residual SAC for seeds `0..4`.
- [ ] Compare `torque` vs `residual` on the same reachable target protocol.
- [ ] Add a pure analytical-prior baseline script for explicit no-RL comparison.
- [ ] Tune PD gains and reward weights for reach-and-hold stability.
- [ ] Add calibration/identification so the analytical prior is fitted from MuJoCo rollouts rather than only XML-derived.

## 7) Run scoring
| Metric | Value | Notes |
|---|---:|---|
| Time-to-runnable (min) | ~15 | Included environment refactor + smoke verification |
| Reproducible from clean checkout | Y | Via `./run.sh` commands above |
| Correctness (1–5) | 4 | Hybrid path works; target bug identified and fixed in protocol |
| Code quality (1–5) | 4 | Single environment supports both baseline and hybrid modes |
| Doc quality (1–5) | 4 | Commands and benchmark caveat documented |
| Failures encountered (#) | 1 | Original benchmark target was unreachable |

---

## 8) Patch note — 2026-04-15 (OBJ viewer reliability fix)

### Why this patch was needed
- The persistent "not showing" issue was not a MATLAB/RL dynamics failure.
- Root cause was visualization packaging/execution mismatch for OBJ loading.
- The intended integration test is a root script launch (`./run.sh view_dummy_two_link_obj.py`) that must resolve the MJCF scene reliably.

### Actions taken
- Updated `view_dummy_two_link_obj.py` to use robust scene resolution:
  - preferred scene: `dummy_two_link_obj_view.xml` (root)
  - fallback scene: `3D_model/dummy_two_link_obj_view.xml` (legacy layout)
- Added explicit compile/preflight failure reporting in `view_dummy_two_link_obj.py`:
  - wraps `mujoco.MjModel.from_xml_path(...)`
  - provides clear error guidance for XML/mesh/material path failures
- Added headless preflight mode in `view_dummy_two_link_obj.py`:
  - `--check-only` compiles XML + mesh and exits before launching viewer
- Updated `run.sh` routing:
  - `./run.sh view_dummy_two_link_obj.py --check-only` now runs with standard Python for CI/headless checks
  - `./run.sh view_dummy_two_link_obj.py` still runs with `mjpython` on macOS for GUI launch
- Verified root MJCF wrapper uses direct mesh reference in `dummy_two_link_obj_view.xml`:
  - `<mesh ... file="Two_link_model.obj" .../>`

### Verification commands run
```bash
./run.sh -c "import mujoco; m=mujoco.MjModel.from_xml_path('dummy_two_link_obj_view.xml'); print('dummy_compile_ok', m.nq, m.nmesh)"
./run.sh -c "from view_dummy_two_link_obj import resolve_asset; print(resolve_asset())"
./run.sh -m py_compile view_dummy_two_link_obj.py
./run.sh -c "import mujoco; m=mujoco.MjModel.from_xml_path('dummy_two_link_obj_view.xml'); print('root_dummy_ok', m.nq, m.nmesh)"
./run.sh view_dummy_two_link_obj.py --check-only
./run.sh view_dummy_two_link_obj.py
```

### Observed outputs
- `dummy_compile_ok 0 1`
- Resolved asset path: `/Users/uljan/Desktop/Mujoco/dummy_two_link_obj_view.xml`
- `root_dummy_ok 0 1`
- `Preflight OK: /Users/uljan/Desktop/Mujoco/dummy_two_link_obj_view.xml (nq=0, nmesh=1)`
- Viewer smoke command entered running state without XML/resource parse errors

### Stakeholder impact
- The root-level command remains the canonical launch path:
  - `./run.sh view_dummy_two_link_obj.py`
- This de-risks GUI-side manual file loading mistakes (dragging `.obj` directly).
- Visualization validation is now explicitly separated from RL/MATLAB benchmark logic.
