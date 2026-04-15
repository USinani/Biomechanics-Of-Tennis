# Two-Link MuJoCo Experiment Update — YYYY-MM-DD

## 1) What changed
- Added/modified:
  - `...`
- Purpose:
  - ...

## 2) How to run (from project root)
### Setup
- Create venv / install deps:
  - `python -m venv .venv && .venv/bin/pip install mujoco gymnasium stable-baselines3`

### Train
- Command:
  - `./run.sh example_two_link/train_sac.py --steps 200000 --seed 0`

### Evaluate
- Command:
  - `./run.sh example_two_link/eval.py --checkpoint example_two_link/checkpoints/sac_two_link_seed0 --seeds 0,1,2,3,4`

### View rollout (optional)
- Command:
  - `./run.sh example_two_link/view.py --checkpoint example_two_link/checkpoints/sac_two_link_seed0`

## 3) Experiment details
- Environment: two-link arm (MuJoCo)
- Reward: distance + velocity-toward-target + effort + smoothness + limit penalties
- Action space: Box(-60, 60, shape=(2,)) Nm
- Observations: sin/cos(q), qd, hand_xyz, target_xyz, delta_xyz (15 dims)
- Seeds: 0,1,2,3,4
- Train steps: 200000
- Eval episodes / horizon: 10 rollouts, 100 steps max per episode
- Hardware / OS: ...

## 4) Results
- Key metrics:
  - Mean return (± std):
  - Success rate:
- Notes:
  - ...

## 5) Problems + fixes
- Issue:
- Fix:
- Prevention:

## 6) Next steps
- [ ] ...
- [ ] ...

## 7) Run scoring (research tracking)
| Metric | Value | Notes |
|---|---:|---|
| Time-to-runnable (min) |  |  |
| Reproducible from clean checkout | Y/N |  |
| Correctness (1–5) |  |  |
| Code quality (1–5) |  |  |
| Doc quality (1–5) |  |  |
| Failures encountered (#) |  |  |
