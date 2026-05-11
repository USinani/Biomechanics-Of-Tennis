# Lane A Integrator Ablation Evidence Packet — qdot2 Event

## Question tested
Is the reproduced MuJoCo `mujoco_qdot2_rad_s` step/ramp around \(t \approx 0.480\)–\(0.486\) s specific to the MuJoCo XML integrator (`implicitfast`), or does it persist under MuJoCo RK4 when everything else is held constant?

## Commands run
- Baseline derived benchmark (implicitfast integrator from XML):
  - `./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py --steps 500 --out-csv runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv --out-json runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- RK4 derived benchmark (MuJoCo integrator override, same XML):
  - `./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py --steps 500 --mujoco-integrator rk4 --out-csv runs/diagnostics/parity_integrator_ablation/swing_benchmark_timeseries_500_rk4.csv --out-json runs/diagnostics/parity_integrator_ablation/swing_benchmark_summary_500_rk4.json`

## Input artifacts
- MuJoCo model XML: `example_two_link/two_link_arm.xml` (contains `<option ... integrator="implicitfast"/>`)
- Benchmark script: `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`

## Output artifacts
- Baseline (implicitfast-from-XML) derived outputs:
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json`
- RK4 derived outputs:
  - `runs/diagnostics/parity_integrator_ablation/swing_benchmark_timeseries_500_rk4.csv`
  - `runs/diagnostics/parity_integrator_ablation/swing_benchmark_summary_500_rk4.json`

## Git status summary (canonical output safety)
- `git status --porcelain` after the RK4 probe showed derived diagnostics outputs were created, and **no files under `systematic_studies/outputs/`** were modified.

## Event metrics (baseline implicitfast)
Window: \(t \in [0.470, 0.490]\) s, computed from `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv` using the benchmark’s detector logic (dt=0.001, spike threshold=500 rad/s², jerk threshold=5e4 rad/s³).

- max consecutive jump in `mujoco_qdot2_rad_s` (window): **0.9323693041676029**
- spike count (qdot2 only, window): **7**
- jerk outlier count (qdot2 only, window): **8**

`mujoco_qdot2_rad_s` in the event slice \(t \in [0.480, 0.486]\) s:
- 0.480: 1.0056325520694707
- 0.481: 1.9380018562370736
- 0.482: 2.788142401539682
- 0.483: 3.561766520958404
- 0.484: 4.264232258282969
- 0.485: 4.900560204810979
- 0.486: 5.475450931746508

## Event metrics (MuJoCo RK4)
Window: \(t \in [0.470, 0.490]\) s, computed from `runs/diagnostics/parity_integrator_ablation/swing_benchmark_timeseries_500_rk4.csv` with the same detector logic.

From `runs/diagnostics/parity_integrator_ablation/swing_benchmark_summary_500_rk4.json`:
- `mujoco_integrator_requested`: `rk4`
- `mujoco_integrator_effective`: `rk4`

- max consecutive jump in `mujoco_qdot2_rad_s` (window): **0.8413412244376863**
- spike count (qdot2 only, window): **7**
- jerk outlier count (qdot2 only, window): **8**

`mujoco_qdot2_rad_s` in the event slice \(t \in [0.480, 0.486]\) s:
- 0.480: 1.0045889554438854
- 0.481: 1.7671861959407693
- 0.482: 2.6085274203784556
- 0.483: 3.3770461642882386
- 0.484: 4.07758893971162
- 0.485: 4.71471700143281
- 0.486: 5.292719336607157

## Interpretation (conservative)
- RK4 **reduces the qdot2 event magnitude** (lower max consecutive jump) in this window.
- RK4 **does not eliminate** the spike/jerk detector failures (counts unchanged in-window under the current thresholds).
- Therefore, **integrator choice alone is insufficient** to clear the current “no spikes / no jerk outliers” gate.

## Limitations
- This is a single configuration probe; it does not establish causality for the event mechanism.
- The baseline derived summary JSON predates integrator provenance fields, so it does not explicitly record “implicitfast effective integrator” (inferred from the XML, not recorded in JSON).
- These metrics reflect the current detector thresholds; detector sensitivity is not explored here.

## Next decision
Inspect whether the passive divergence and velocity event are driven primarily by **parameter / damping / actuation-model mismatch** between MuJoCo and the bridge dynamics assumptions, before attempting any parity-gate or threshold changes.

