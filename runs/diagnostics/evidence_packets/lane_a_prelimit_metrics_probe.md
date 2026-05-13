# Lane A Pre-Limit Metrics Probe Evidence Packet

Date: 2026-05-11

## Goal
Recompute bridge-vs-MuJoCo metrics **only** for rows with **`time_s < 0.480`** on stored derived CSVs, to separate **unconstrained ODE-level** mismatch from the **joint-limit / contact** artefact on the full horizon.

## Method
- **Script:** `runs/diagnostics/parity_prelimit_metrics/compute_prelimit_metrics.py`
- **Inputs (read-only):**  
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_timeseries_500.csv`  
  - `runs/diagnostics/parity_joint_limit_ablation/swing_benchmark_timeseries_500_nolimits.csv`  
  - `runs/diagnostics/parity_500step_probe/swing_benchmark_summary_500.json` (full-run summary reference)
- **Output:** `runs/diagnostics/parity_prelimit_metrics/prelimit_metrics.json`
- **Exit code:** 0

## Cutoff
- **Criterion:** `time_s < 0.480` (strict).
- **Included rows:** 480 per series (steps through **t = 0.479 s**).
- **Rationale:** Shoulder first crosses nominal **+120°** at **t = 0.48 s** on the baseline run; pre-limit window is **no-contact** for that limit on this benchmark.

## Key results (see JSON for full floats)

| Series | rmse_q_rad | rmse_qd | MuJoCo spike count | MuJoCo jerk outliers | max \|Δqdot2\|/dt (MuJoCo) | Relaxed gate¹ |
|--------|------------|---------|--------------------|----------------------|----------------------------|---------------|
| Full baseline (500 rows, CSV) | 2.415615 | 12.580620 | 7 | 9 | 932.37 | **false** |
| Pre-limit baseline (480 rows) | 2.321372 | 12.159637 | 0 | 0 | 44.93 | **true** |
| Pre-limit no-limit (480 rows) | 2.321372 | 12.159637 | 0 | 0 | 44.93 | **true** |

¹ **`compare_signals` relaxed** thresholds from `scripts/parity_smoke.sh` / `parity_full.sh`: `max_q_dev_rad <= 5.0`, `max_qdot_dev_rad_s <= 25.0`, **zero** MuJoCo and bridge spikes/jerk outliers **on the evaluated rows only**. This is **not** the swing benchmark `parity_ready_bridge_gate` (strict RMSE thresholds).

**Identity check:** Pre-limit **baseline** and **no-limit** metrics match to floating precision — expected, since joint limits do not diverge trajectories before contact.

## Interpretation
- **Contact / limit segment** drives the **full-run MuJoCo spike and jerk counters** and the huge **qdot2** acceleration spike; the **pre-limit** window has **none** of those under the same spike/jerk definitions.
- **RMSE and max abs deviations remain substantial** pre-limit (ODE-level mismatch is **not** negligible), but the **relaxed compare_signals-style gate** **passes** on the pre-limit window.

## Contract link
Supports **`docs/research/LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`** option **C** (pre-limit / no-contact parity) as the right place to score **unconstrained** agreement, while keeping full mixed-horizon metrics **diagnostic** for limit artefacts.
