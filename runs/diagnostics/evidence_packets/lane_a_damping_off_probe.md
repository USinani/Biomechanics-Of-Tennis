# Lane A Damping-Off Probe Evidence Packet

## Question tested
Does disabling MuJoCo joint damping in-memory (without editing the canonical XML) reduce or remove the reproduced MuJoCo `mujoco_qdot2_rad_s` event around \(t \approx 0.480\)–\(0.490\) s?

## Command run
```bash
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --mujoco-damping-scale 0.0 \
  --out-csv runs/diagnostics/parity_damping_ablation/swing_benchmark_timeseries_500_damping0.csv \
  --out-json runs/diagnostics/parity_damping_ablation/swing_benchmark_summary_500_damping0.json
```

## Input artifacts
- Baseline derived probe:
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- Canonical model (read-only reference): `example_two_link/two_link_arm.xml`
- Benchmark script (read-only reference): `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`

## Output artifacts
- Damping-off derived outputs:
  - `runs/diagnostics/parity_damping_ablation/swing_benchmark_timeseries_500_damping0.csv`
  - `runs/diagnostics/parity_damping_ablation/swing_benchmark_summary_500_damping0.json`

## Damping provenance (from damping-off summary JSON)
- `mujoco_damping_scale`: **0.0**
- `mujoco_dof_damping_original`: **[0.12, 0.12]**
- `mujoco_dof_damping_effective`: **[0.0, 0.0]**

## Baseline vs damping-off local qdot2 event comparison
Window: \(t \in [0.470, 0.490]\) s (computed from the CSV `mujoco_qdot2_rad_s` series using dt=0.001 and the benchmark’s spike/jerk thresholds).

Baseline (XML damping scale 1.0; from baseline CSV):
- local max consecutive jump in `mujoco_qdot2_rad_s`: **0.9323693041676029**
- local qdot2 spike count (threshold 500 rad/s²): **7**
- local qdot2 jerk outlier count (threshold 5e4 rad/s³): **8**

Damping-off (scale 0.0; from damping-off CSV):
- local max consecutive jump in `mujoco_qdot2_rad_s`: **0.07896663620641675**
- local qdot2 spike count: **0**
- local qdot2 jerk outlier count: **0**

## Baseline vs damping-off whole-run metric comparison (from summary JSON)
Baseline (`runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`):
- `rmse_q_rad`: **2.415615155736079**
- `rmse_qd`: **12.580619180393969**
- `velocity_spike_count`: **7**
- `velocity_jerk_outlier_count`: **9**
- `parity_ready_bridge_gate`: **false**

Damping-off (`runs/diagnostics/parity_damping_ablation/swing_benchmark_summary_500_damping0.json`):
- `rmse_q_rad`: **2.5790369130576414** (worse)
- `rmse_qd`: **15.528854178393258** (worse)
- `velocity_spike_count`: **25** (worse)
- `velocity_jerk_outlier_count`: **25** (worse)
- `parity_ready_bridge_gate`: **false**

## Interpretation (conservative)
- Damping-off **materially reduces/removes the local qdot2 event** around 0.470–0.490s by the local spike/jerk criteria and by max consecutive jump.
- Damping-off **worsens overall bridge-vs-MuJoCo alignment** (RMSE increases) and increases whole-run spike/jerk totals.
- Therefore, damping is **causal/sensitive** for the local event, but **zero damping is not a solution** under the current whole-run metrics and gate.
- Strict parity is **not closed** (gate remains false).

## Limitations
- This is a single “scale=0.0” point; it does not identify an optimal intermediate damping value.
- The local event metric window captures one causal feature (qdot2 transient) but does not guarantee global parity improvements.
- Whole-run spike/jerk totals include both joints and all times; the change could be redistributed elsewhere in the trajectory.

## Next decision
Run a **small derived damping scale sweep** (e.g., 0.25/0.5/0.75) to test whether an intermediate scale can improve both:
1) local qdot2 event behavior, and
2) whole-run RMSE/spike/jerk totals.

