# Cursor Agent Experiment Paradigm: Two-Link MuJoCo

## Goal

Evaluate whether a Cursor Agent can reliably take a small robotics/RL task from **spec → runnable experiment → documented update**, with measurable quality, speed, and reproducibility.

## Task family (micro-project backbone)

1. **Environment definition** — MuJoCo XML + Python wrapper (`arm_env.py`, `example_two_link/two_link_arm.xml`)
2. **Dynamics bridge** — MATLAB_v2 two-link equations ported to Python (`example_two_link/matlab_v2_dynamics.py`)
3. **Training loop** — SAC (`example_two_link/train_sac.py`)
4. **Evaluation script** — Fixed seeds, metrics JSON (+ optional trajectory export) (`example_two_link/eval.py`)
5. **Viewer demo** — Render/rollout (`example_two_link/view.py`)
6. **Project update** — `.md` with results + instructions (`project_updates/YYYY-MM-DD_two_link_update.md`)

## Independent variables (toggles between runs)

1. **Agent autonomy**: A0 (human plans, agent executes) | A1 (agent plans+executes) | A2 (agent plans+executes+updates)
2. **Specification quality**: S0 (minimal prompt) | S1 (structured spec with files, commands, acceptance criteria)
3. **Tooling**: T0 (no internet) | T1 (web search allowed)

## Dependent variables (metrics)

| Metric | Description |
|--------|-------------|
| Time-to-runnable | Minutes until `./run.sh ...` works end-to-end |
| Reproducibility | Y/N: can fresh clone reproduce with README/update? |
| Correctness (1–5) | Training improves reward; eval metrics computed and saved |
| Code quality (1–5) | Structure, config, comments, minimal hacks |
| Doc quality (1–5) | Commands, deps, expected outputs, troubleshooting |
| Failures (#) | Dead ends, broken commands, missing files |

## Controls (fixed)

- Seeds: 0, 1, 2, 3, 4
- Training budget: 200k steps
- Eval: 10 rollouts × 100 steps max per episode
- Same repo scaffold, `run.sh`, MuJoCo version

## Acceptance criteria (pass/fail)

- `./run.sh example_two_link/train_sac.py` and `./run.sh example_two_link/eval.py` run without manual fixes
- `./run.sh example_two_link/validate_matlab_v2_bridge.py` produces bridge diagnostics JSON
- Training completes for target step budget
- Eval produces saved metrics file (`example_two_link/metrics/*.json`)
- Optional Unity replay files are produced in `example_two_link/exports/*.txt|*.csv`
- Update `.md` has exact commands, observed outputs, next steps, scoring table

## Reference commands

```bash
# Bridge diagnostics
./run.sh example_two_link/validate_matlab_v2_bridge.py --samples 50 --param-source matlab_default

# Train
./run.sh example_two_link/train_sac.py --steps 200000 --seed 0 --bridge-check

# Evaluate + export for Unity replay
./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_seed0 --seeds 0,1,2,3,4 --export-trajectory
```

## Final instruction for the agent (each run)

> Create a new markdown file at `project_updates/YYYY-MM-DD_two_link_update.md`.
> Include: (1) summary of changes, (2) how to run (exact commands), (3) experiment config (seeds, steps, env details), (4) results (metrics + short interpretation), (5) issues encountered + fixes, (6) next steps, and (7) a small scoring table (time-to-runnable, reproducibility, correctness, doc quality).
> The update must be sufficient for someone else to reproduce the run from a clean checkout.

## Template

See `project_updates/TEMPLATE.md` for the recommended structure.
