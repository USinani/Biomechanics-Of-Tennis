# Lane A SysID Parameter Replay Evidence Packet

## Question tested
Does replaying the benchmark with the existing SysID parameter bundle (`sysid_bridge_params.json`) materially reduce bridge-vs-MuJoCo divergence and/or the MuJoCo-side `mujoco_qdot2_rad_s` event, without changing the MuJoCo trajectory or canonical outputs?

## Command run
```bash
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --param-source from_json \
  --params-json systematic_studies/outputs/sysid_bridge_params.json \
  --out-csv runs/diagnostics/parity_sysid_replay/swing_benchmark_timeseries_500_sysid.csv \
  --out-json runs/diagnostics/parity_sysid_replay/swing_benchmark_summary_500_sysid.json
```

## Input artifacts
- SysID parameter bundle: `systematic_studies/outputs/sysid_bridge_params.json`
- Baseline derived probe:
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- SysID replay outputs (for inspection/comparison):
  - `runs/diagnostics/parity_sysid_replay/swing_benchmark_timeseries_500_sysid.csv`
  - `runs/diagnostics/parity_sysid_replay/swing_benchmark_summary_500_sysid.json`

## Output artifacts
- `runs/diagnostics/parity_sysid_replay/swing_benchmark_timeseries_500_sysid.csv`
- `runs/diagnostics/parity_sysid_replay/swing_benchmark_summary_500_sysid.json`

## Canonical output safety check
- `git status --porcelain` after the run showed **no modifications under `systematic_studies/outputs/`** (derived-only outputs were created under `runs/diagnostics/parity_sysid_replay/`).

## Baseline vs SysID RMSE comparison (from summary JSON)
Baseline (`runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`, `param_source=from_xml`):
- `rmse_q_rad`: **2.415615155736079**
- `rmse_qd`: **12.580619180393969**

SysID replay (`runs/diagnostics/parity_sysid_replay/swing_benchmark_summary_500_sysid.json`, `param_source=from_json`):
- `rmse_q_rad`: **1.503146698714053**
- `rmse_qd`: **8.321240601109407**

## Baseline vs SysID qdot2 event comparison
Window: \(t \in [0.470, 0.490]\) s (computed from the CSV columns for `mujoco_qdot2_rad_s` with dt=0.001 and the benchmark detector thresholds).

MuJoCo-side event metrics (in-window):
- max consecutive jump in `mujoco_qdot2_rad_s`:
  - baseline: **0.9323693041676029**
  - sysID: **0.9323693041676029** (unchanged)
- qdot2 spike count (threshold 500 rad/s²):
  - baseline: **7**
  - sysID: **7** (unchanged)
- qdot2 jerk outlier count (threshold 5e4 rad/s³):
  - baseline: **8**
  - sysID: **8** (unchanged)

Event slice \(t \in [0.480, 0.486]\) s:
- MuJoCo `mujoco_qdot2_rad_s`: **identical baseline vs SysID**, because MuJoCo trajectory is unchanged by the analytical parameter set.
- Bridge `bridge_qdot2_rad_s`: changes materially (SysID shifts the bridge trajectory), e.g. at t=0.480:
  - baseline: **-14.171150767341372**
  - sysID: **-8.512409141129016**

Gate-related totals from summary JSON:
- `velocity_spike_count`: baseline **7**, sysID **7** (unchanged)
- `velocity_jerk_outlier_count`: baseline **9**, sysID **9** (unchanged)
- `parity_ready_bridge_gate`: baseline **false**, sysID **false** (unchanged)

## Interpretation (conservative)
- SysID parameters **materially reduce bridge-vs-MuJoCo RMSE** (`rmse_q_rad` and `rmse_qd` improved).
- SysID parameters **do not affect MuJoCo qdot2 values** because the MuJoCo trajectory is unchanged by analytical parameter choice.
- SysID **does not remove spike/jerk detector failures** in the current benchmark gating outputs.
- SysID alone **does not close strict parity** (gate remains false).

## Limitations
- The summary JSON does not embed the full SysID parameter dict; parameter provenance is inferred from the CLI invocation and the `param_source=from_json` code path.
- This probe does not isolate damping vs inertia vs gravity convention contributions; it tests a bundled parameter change.
- This is not native MATLAB strict parity; it is a benchmark bridge-vs-MuJoCo replay.

## Next decision
Use the derived 500-step benchmark CSV as a **frozen, hashed input artifact** and plan a controlled native MATLAB strict parity replay that preserves provenance (copy/hash of input CSV + command + git status), without overwriting canonical outputs.

