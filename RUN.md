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

To generate presentation-ready figures from systematic study CSV outputs:

```bash
python systematic_studies/visualisation/plot_results.py
```

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

## 3. Run RL training

```bash
./run.sh train_sac_quick.py        # quick test (~10k steps)
./run.sh train_sac.py              # full training (~300k steps)
./run.sh example_two_link/train_sac.py --steps 200000 --seed 0 --action-mode residual --target-mode planar_fixed
./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_residual_seed0 --action-mode residual --target-mode planar_fixed
```

`example_two_link/train_sac.py` supports both direct torque control (`--action-mode torque`) and hybrid residual control (`--action-mode residual`). For the two-link planar model, use `--target-mode planar_fixed` or `random_planar`; the raw XML target is off-plane and not exactly reachable.

## 4. Visualize trained policy

After training (or if `sac_two_link_arm.zip` exists):

```bash
./run.sh run_policy_in_mujoco_viewer.py
```

## 5. Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: mujoco` | Use `.venv/bin/python` or `./run.sh` |
| `RuntimeError: launch_passive requires mjpython on macOS` | Use `mjpython view_mujoco_arm.py` or `./run.sh view_mujoco_arm.py` |
| No venv | `python -m venv .venv && .venv/bin/pip install mujoco gymnasium stable-baselines3` |
