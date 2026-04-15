## MuJoCo Two-Link RL – Progress Update (Concise)

### What changed since previous implementation

- Added a **MATLAB_v2 → Python dynamics bridge** for the two-link model:
  - `example_two_link/matlab_v2_dynamics.py`
  - `example_two_link/matlab_v2_params.py`
- Added **bridge validation** against MuJoCo snapshots:
  - `example_two_link/validate_matlab_v2_bridge.py`
  - Outputs: `example_two_link/metrics/bridge_validation*.json`
- Added **Unity-ready data export** from evaluation:
  - `example_two_link/export_unity_txt.py`
  - `eval.py --export-trajectory` now writes `.csv/.txt/.json` in `example_two_link/exports/`
- Integrated bridge hooks into RL scripts:
  - `train_sac.py --bridge-check`
  - `eval.py --bridge-diagnostics --param-source ...`
- Updated guidance/docs:
  - `example_two_link/README.md`
  - `EXPERIMENT_PARADIGM.md`
  - `run.sh` usage examples

### Current status (presentation-ready)

- End-to-end pipeline is runnable:
  1. Train (`train_sac.py`)
  2. Evaluate (`eval.py`)
  3. Viewer demo (`view.py`)
  4. Export replay/control data for Unity (`--export-trajectory`)
- Latest run artifacts include:
  - `example_two_link/metrics/eval_sac_two_link_arm.json`
  - `example_two_link/exports/trajectory_sac_two_link_arm.csv`
  - `example_two_link/exports/trajectory_sac_two_link_arm.txt`

### Key technical takeaway

- **Bridge internal consistency is correct** (inverse/forward dynamics residual ~0).
- **Bridge vs MuJoCo acceleration mismatch remains** (expected due to model/parameter/solver differences), but the XML-derived parameter set reduces mismatch relative to MATLAB defaults.
- This supports a clean story for the PhD presentation:
  - *Stage 1*: validated cross-model equations
  - *Stage 2*: RL loop operational in MuJoCo
  - *Stage 3*: Unity integration path established via trajectory export

### Minimal commands to demonstrate live

```bash
# 1) Validate MATLAB_v2 bridge
./run.sh example_two_link/validate_matlab_v2_bridge.py --samples 30 --param-source matlab_default

# 2) Train smoke run with bridge check
./run.sh example_two_link/train_sac.py --steps 200 --seed 1 --bridge-check

# 3) Evaluate + export Unity-ready trajectories
./run.sh example_two_link/eval.py --checkpoint sac_two_link_arm --seeds 0,1,2,3,4 --export-trajectory --bridge-diagnostics

# 4) Visualize policy in MuJoCo
./run.sh example_two_link/view.py --checkpoint sac_two_link_arm
```

### Next slide-worthy steps

- Run full 200k training for seeds `0..4` and report aggregate statistics.
- Add one calibrated inertial parameter set to further reduce bridge-vs-MuJoCo acceleration error.
- Build Unity-side parser/replayer for the exported TXT/CSV trajectory format.

