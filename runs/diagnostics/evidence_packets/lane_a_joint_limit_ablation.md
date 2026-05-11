# Lane A Joint-Limit Ablation Evidence Packet

## 1. Question
Did disabling MuJoCo joint limits remove the qdot2 spike/jerk event?

## 2. Hypothesis
MuJoCo shoulder joint-limit constraint forces, absent from bridge/MATLAB, dominate the qdot2 spike/jerk event.

## 3. Command
Exact no-limit command (run once; exit code 0):

```bash
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --mujoco-joint-limits disabled \
  --out-csv runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_timeseries_500_nolimits.csv \
  --out-json runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_summary_500_nolimits.json
```

## 4. Inputs
- Baseline (XML joint limits, default benchmark harness):  
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`  
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- Prior contract / force context:  
  - `runs/diagnostics/evidence_packets/lane_a_joint_limit_contract_inspection.md`  
  - `runs/diagnostics/evidence_packets/lane_a_mujoco_force_decomposition_event_states.md`

## 5. Outputs
- `runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_timeseries_500_nolimits.csv`
- `runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_summary_500_nolimits.json`

## 6. Metrics
Local window **t ∈ [0.470, 0.490] s**, MuJoCo **qdot2** only, using benchmark defaults **|Δqdot2/dt| > 500** rad/s² for spike count and **|Δ(Δqdot2/dt)/dt| > 5×10⁴** rad/s³ for jerk outliers (same thresholds as `swing_benchmark_mujoco_vs_bridge.py` defaults).

| Metric | Baseline (XML limits) | No-limit (`mujoco_joint_limits: disabled`) |
|--------|----------------------:|-------------------------------------------:|
| Local qdot2 max \|Δqdot2\|/dt (rad/s²) | 932.37 | 3.61 |
| Local qdot2 spike count | 7 | 0 |
| Local qdot2 jerk outlier count | 8 | 0 |
| Whole-run velocity_spike_count | 7 | 0 |
| Whole-run velocity_jerk_outlier_count | 9 | 0 |
| rmse_q_rad | 2.415615 | 2.416052 |
| rmse_qd | 12.580619 | 12.324343 |
| parity_ready_bridge_gate | false | false |

## 7. Result classification
**supports hypothesis**

## 8. Interpretation
- **No-limit removes the MuJoCo qdot2 spike/jerk event** in the 0.47–0.49 s window and clears whole-run velocity spike/jerk counters on this passive 500-step derived benchmark.
- **Joint-limit mismatch is the dominant cause of that event** (MuJoCo constrained dynamics vs unconstrained bridge integration in the same harness).
- **Strict parity remains open:** `parity_ready_bridge_gate` is still **false** (driven by RMSE vs thresholds, not spike/jerk counts on the no-limit run).
- **No-limit is a diagnostic ablation**, not a decision to ship unlimited joints as the reference physical model.

## 9. Limitations
- Does **not** prove full trajectory parity or analytical correctness.
- Does **not** decide whether production work should **disable** limits, **mirror** limits in analytics, or **exclude** limit-adjacent times from strict gates.
- Does **not** resolve the **whole-run RMSE** mismatch between MuJoCo and bridge on this benchmark.

## 10. Decision impact
Lane A should be treated as **two comparability layers**:
1. **Unconstrained dynamics parity** — smooth ODE regime away from limit contact; RMSE and convention issues (e.g. gravity sign) live here.
2. **Constrained / limit-contact behavior parity** — requires either matching joint limits in the analytical path, explicit no-limit MuJoCo lane, or excluding contact windows from strict agreement claims.

## 11. Next action
**Plan Lane A model-contract decision** — write a short decision brief that chooses or sequences: matched limits in analytics, diagnostic no-limit MuJoCo lane, or explicit gate exclusions for limit contact, without conflating with relaxed-only closure.
