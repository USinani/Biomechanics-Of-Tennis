# Lane A Damping Sweep Evidence Packet

## Question tested
Does an intermediate MuJoCo joint damping scale reduce the local qdot2 transient (0.470–0.490s) without worsening whole-run bridge-vs-MuJoCo metrics compared with the baseline XML damping?

## Commands run
```bash
mkdir -p runs/diagnostics/parity_damping_sweep/

./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --mujoco-damping-scale 0.25 \
  --out-csv runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p25.csv \
  --out-json runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p25.json

./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --mujoco-damping-scale 0.5 \
  --out-csv runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p5.csv \
  --out-json runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p5.json

./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --mujoco-damping-scale 0.75 \
  --out-csv runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p75.csv \
  --out-json runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p75.json
```

## Input artifacts
- Baseline (scale 1.0) derived probe:
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- Damping-off (scale 0.0) derived probe:
  - `runs/diagnostics/parity_damping_ablation/swing_benchmark_timeseries_500_damping0.csv`
  - `runs/diagnostics/parity_damping_ablation/swing_benchmark_summary_500_damping0.json`
- Sweep outputs (this packet):
  - `runs/diagnostics/parity_damping_sweep/*`

## Output artifacts
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p25.csv`
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p25.json`
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p5.csv`
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p5.json`
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_timeseries_500_damping0p75.csv`
- `runs/diagnostics/parity_damping_sweep/swing_benchmark_summary_500_damping0p75.json`

## Sweep table
Window for local metrics: \(t \in [0.470, 0.490]\) s, computed on `mujoco_qdot2_rad_s` with dt=0.001 and the benchmark spike/jerk thresholds.

| scale | rmse_q_rad | rmse_qd | whole-run velocity_spike_count | whole-run velocity_jerk_outlier_count | local qdot2 max jump (0.470–0.490) | local qdot2 spike count | local qdot2 jerk outlier count | parity_ready_bridge_gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0.0 | 2.5790 | 15.5289 | 25 | 25 | 0.0790 | 0 | 0 | false |
| 0.25 | 2.5436 | 14.6658 | 18 | 18 | 0.0879 | 0 | 0 | false |
| 0.5 | 2.5058 | 13.9202 | 11 | 13 | 0.3462 | 0 | 0 | false |
| 0.75 | 2.4663 | 13.2896 | 8 | 11 | 0.9366 | 7 | 7 | false |
| 1.0 | 2.4156 | 12.5806 | 7 | 9 | 0.9324 | 7 | 8 | false |

## Best RMSE scale
- Best (lowest) whole-run RMSE observed: **scale 1.0** (baseline).

## Best local qdot2 event scale
- Best local qdot2 transient behavior observed: **scale 0.0** (smallest local max jump; zero local spikes/jerk outliers). Scales **0.25** and **0.5** also eliminated local spikes/jerk outliers.

## Interpretation (conservative)
- Damping scale strongly affects the local qdot2 transient.
- Reduced damping (0.0–0.5) removes the *local* qdot2 spike/jerk failures in the 0.470–0.490s window.
- Baseline damping (1.0) gives the best whole-run RMSE among tested scales.
- No tested damping scale improves both local event behavior and whole-run metrics relative to baseline.
- Damping alone does not close parity (gate remains false for all scales).

## Limitations
- The sweep is sparse (only 0.25, 0.5, 0.75 in addition to 0.0/1.0).
- Whole-run spike/jerk totals aggregate both joints and all times; they may hide where new outliers appear when damping changes.
- This does not test analytical-lane damping (bridge/MATLAB), only MuJoCo damping scaling.

## Next decision
Inspect compiled MuJoCo inertial properties (masses/inertias/COM) vs the analytical bridge’s simplified assumptions to determine whether inertia/model-structure mismatch is now the dominant bottleneck for whole-run parity.

