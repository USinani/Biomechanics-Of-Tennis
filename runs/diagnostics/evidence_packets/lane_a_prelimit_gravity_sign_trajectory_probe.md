# Lane A Evidence Packet — Pre-Limit Gravity-Sign Trajectory Probe (M1)

Date: 2026-05-11

## Goal (contract C)
Test whether **`--bridge-gravity-sign mujoco`** materially improves **pre-limit** (`time_s < 0.480`) bridge-vs-MuJoCo RMSE versus baseline **`bridge_gravity_sign=default`**, after M4/M2 tranche.

## Command
```bash
./run.sh systematic_studies/swing_benchmark_mujoco_vs_bridge.py \
  --steps 500 \
  --bridge-gravity-sign mujoco \
  --out-csv runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_timeseries_500_gravsign.csv \
  --out-json runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json
```
**Exit code:** 0

## Outputs
- `runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_timeseries_500_gravsign.csv`
- `runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json`
- `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json` (pre-limit recomputation vs baseline CSV)

## Window
- **Cutoff:** `time_s < 0.480` (strict)
- **Rows:** 480; **time:** 0.0–0.479 s
- **Rationale:** Lane A contract **C** (no shoulder limit contact on this passive benchmark)

## Key results (pre-limit)
| Metric | Baseline (bridge default) | Gravity-sign (`mujoco`) |
|--------|--------------------------:|--------------------------:|
| rmse_q_rad | 2.321372 | **0.621015** |
| rmse_qd | 12.159637 | **3.387841** |
| max_abs_dev_q1_rad | 3.919083 | **0.248314** |
| max_abs_dev_q2_rad | 1.302475 | **1.011071** |
| max_abs_dev_qdot1_rad_s | 12.161998 | **1.351752** |
| max_abs_dev_qdot2_rad_s | 16.941524 | **5.739636** |
| MuJoCo velocity_spike_count (window) | 0 | 0 |
| MuJoCo velocity_jerk_outlier_count (window) | 0 | 0 |
| max \|Δqdot2\|/dt (MuJoCo) | 44.925 | 44.925 |
| Relaxed compare_signals-style (window) | true | true |
| **Strict swing-style gate (window)** | **false** | **true** |

Strict window gate: `rmse_q ≤ 0.75`, `rmse_qd ≤ 10`, MuJoCo spikes=0, jerks=0 on window rows.

## Full-run summary (diagnostic only; contract D / mixed)
From JSON summaries: baseline full-run `rmse_q_rad` 2.416, `parity_ready_bridge_gate` false; gravity-sign full-run `rmse_q_rad` 0.629, `parity_ready_bridge_gate` **still false** because **velocity_spike_count=7**, **velocity_jerk_outlier_count=9** (MuJoCo XML limits + post-0.48 contact unchanged).

## Interpretation
**Gravity-sign trajectory materially improves pre-limit RMSE** and **closes the pre-limit strict swing-style gate** on this derived 500-step passive run. MuJoCo trajectory on the pre-limit window is unchanged in **qdot2** extrema (same physics); improvement is entirely **bridge trajectory** alignment.

## What this does / does not prove
- **Supports:** default bridge gravity generalized-force sign was a **major** contributor to **contract C** RMSE vs MuJoCo on this harness.
- **Does not prove:** full-horizon or XML-limited parity; **mass-matrix / damping** mismatch can still matter for **local qacc** (M3); native MATLAB; other ICs.

## Decision impact
- Keep **`--bridge-gravity-sign mujoco`** as a **first-class opt-in** for Lane A **C**-contract runs and reporting.
- **Begin guarded discussion** whether **default** for *this* MJCF comparison should flip (needs supervisor + thesis framing; full-run gate still fails without limit contract work).

## Next smallest safe action
Plan **dashboard / reporting** annotation for **contract C** KPIs (pre-limit slice + gravity-sign provenance) **without** renaming canonical JSON paths until `weekly_dashboard.py` change is approved.
