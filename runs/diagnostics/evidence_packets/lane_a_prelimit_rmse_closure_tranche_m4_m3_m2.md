# Lane A Evidence Packet — Pre-Limit RMSE Closure Tranche (M4 → M3 → M2)

Date: 2026-05-11

## Goal
Execute first closure tranche: **M4** (IC/column/units/sampling), **M3** (parameter / mass matrix), **M2** (sparse one-step `qacc` vs bridge `qdd`), **without** new trajectory benchmarks or code edits.

## Method / commands
- Script: `runs/diagnostics/parity_prelimit_rmse_closure/run_m4_m3_m2.py`
- Command: `./.venv/bin/python3 runs/diagnostics/parity_prelimit_rmse_closure/run_m4_m3_m2.py`
- **Exit code:** 0

## Artifacts
- `runs/diagnostics/parity_prelimit_rmse_closure/m4_ic_column_audit.json`
- `runs/diagnostics/parity_prelimit_rmse_closure/m3_mass_matrix_audit.json`
- `runs/diagnostics/parity_prelimit_rmse_closure/m2_sparse_qacc.json`
- `runs/diagnostics/parity_prelimit_rmse_closure/tranche_summary.json`

## M4 — IC / column / unit / sampling
- **Verdict:** **pass** (no blocking harness bug).
- **Columns:** Required `mujoco_*` / `bridge_*` rad and qdot columns present; `mj_q*_deg` consistent with rad (row 0 err 0).
- **First-step reproduction:** Re-running first `mj_step` + bridge `integrate_step` from documented ICs (`q1=5°`, `q2=55°`, `qd=0`, passive torques) matches CSV row 0 **exactly** (L2 error 0 for both).
- **q1/q2 swap:** Cross-correlation test **does not** support a column swap (`swap_plausible_by_crosscorr: false`). Strong **negative** `corr(bridge_q1, mujoco_q1)` on pre-limit reflects **anti-aligned drift**, not swapped indices.
- **Time semantics:** `time_s = k*dt` is **start-of-step** label; recorded `q`/`qd` are **post-step** for **both** simulators — **pairwise comparable**, but **not** equal to continuous-time samples at `time_s` alone.

## M3 — Parameter / mass matrix
- **Verdict:** **plausible mismatch** (expected, not a blocking bug).
- **Masses:** `params_from_mujoco_xml` masses match MuJoCo `body_mass` for `shoulder` / `elbow` bodies (numeric match).
- **Mass matrix `M`:** `mj_fullM` 2×2 block vs analytical `M` from `two_link_tennis_model` shows **~21–25% relative Frobenius** difference at sampled pre-limit rows; condition numbers same order (MuJoCo somewhat stiffer condition). Consistent with **approximate inertia** in `params_from_mujoco_xml` vs full MJCF inertia compilation — **confounds local `qacc` comparison** alongside **missing bridge damping** vs MuJoCo `dof_damping`.

## M2 — Sparse one-step `qacc` / `qdd` (pre-limit rows only)
States: **`q00`**, CSV rows **0, 120, 240, 360, 470** (all `time_s < 0.480`). Torque from `swing_torques` at row `time_s` (passive = 0). Bridge: `compute_forward_dynamics` default vs `gravity_sign=mujoco`. MuJoCo: `mj_forward` after setting `qpos`, `qvel`, `ctrl`.

**Note:** Analytical `qdd` omits **viscous damping** present in MuJoCo; expect residual even when sign aligns.

## Result classification
**Supports:** gravity-sign flip **materially reduces** `‖qacc_mj − qdd_bridge‖` at **q00**, **row0**, **row120**, **row470**; **mixed** at **row240** / **row360** (default closer there).

## Decision impact
- **M4/M3:** do **not** block **M1** on trivial harness bugs; **do** label **M** / **damping** as confounders for strict local acceleration matching.
- **M1 (pre-limit trajectory + `bridge_gravity_sign=mujoco`)** is **more justified** than before for testing **trajectory-level** RMSE under contract **C**, with explicit caveat that **parameter/damping parity** may still dominate after sign.

## Next action
Request **approval** for **pre-limit filtered trajectory** re-run (experiment **M1**) with `--bridge-gravity-sign mujoco` on stored benchmark settings, outputs under `runs/diagnostics/…` only.
