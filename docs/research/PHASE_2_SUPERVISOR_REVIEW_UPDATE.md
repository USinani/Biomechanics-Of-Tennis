# Phase 2 Supervisor Review Update

**Purpose:** **P2-M1** outcomes, metrics, and **supervisor/user decisions (A–E, 2026-05-11)** in one place. **No** new benchmarks and **no** canonical output changes in this file. Cross-linked board: [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md).

**Related:** [`PHASE_2_SUPERVISOR_GOVERNANCE_PACKET.md`](PHASE_2_SUPERVISOR_GOVERNANCE_PACKET.md) · [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) · [`LANE_A_SUPERVISOR_SUMMARY.md`](LANE_A_SUPERVISOR_SUMMARY.md) · [`LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md)

**Evidence:** `runs/diagnostics/evidence_packets/lane_a_phase2_p2m1_ic2_contract_c_replication.md` · `runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json`

---

## 1. What P2-M1 tested

**P2-M1** asked whether the **contract C** strict swing-style result with **`bridge_gravity_sign=mujoco`** on the **original** passive benchmark (M1) **replicates** on one additional pre-registered **IC-2**, with **`t_cut`** from **MuJoCo shoulder angle only** (first `mj_q1_deg >= 120°`) **before** any bridge–MuJoCo error metrics. **Governance** (options **A–E**, next action) is recorded in **§6–§7** (2026-05-11); **P2-M2** is **deferred** there unless scope explicitly reopens (examiner-robustness request).

---

## 2. Result summary

| Item | Outcome |
|------|---------|
| **IC** | **IC-2** was **pre-registered** in governance **§8** (`q1_deg=2.0`, `q2_deg=50.0`, `qd1=0.020`, `qd2=-0.030` rad/s, passive `tau_amp=0`, 500 steps). |
| **`t_cut` rule** | **Primary:** first row on **`baseline_default`** MuJoCo CSV where **`mj_q1_deg >= 120.0`**; **before** any RMSE-based tuning. |
| **Contract C window** | **`time_s < t_cut`** with **`t_cut = 0.47700000000000004` s** (first crossing step **477** on IC-2); **477** rows; time range **0.0–0.476** s. |
| **Default `bridge_gravity_sign`** | **Strict** swing-style **window** gate **false** (`rmse_q_rad` **2.267646**, `rmse_qd` **11.738249**). |
| **`bridge_gravity_sign=mujoco`** | **Strict** window gate **true** (`rmse_q_rad` **0.576505**, `rmse_qd` **3.279675**). |
| **MuJoCo spike/jerk (window)** | **0 / 0** for both signs. |
| **Canonical outputs** | **Unchanged** — all artifacts under `runs/diagnostics/…` only. |

---

## 3. Metric table

| Metric | Default sign | MuJoCo sign | Interpretation |
|--------|---------------|-------------|----------------|
| `rmse_q_rad` | 2.267646 | 0.576505 | **Large** default-sign error; **`mujoco`** aligns within strict **0.75** rad. |
| `rmse_qd` | 11.738249 | 3.279675 | **Large** default error; **`mujoco`** within strict **10** rad/s. |
| Strict swing-style window gate | **false** | **true** | Same pattern as M1 on baseline IC. |
| Relaxed compare_signals-style window gate | **true** | **true** | Unchanged. |
| MuJoCo `velocity_spike_count` / `velocity_jerk_outlier_count` (window) | **0 / 0** | **0 / 0** | No limit-contact spike/jerk **inside** **C** window. |

---

## 4. Evidence status after P2-M1

- **Contract C + gravity sign:** narrative is now supported on **two** passive ICs — (1) original benchmark with **`t_cut ≈ 0.480`** / 480 rows (M1 packet), (2) **IC-2** with **`t_cut = 0.477`** / 477 rows (**P2-M1**). Both use **IC-specific** `t_cut` from MuJoCo shoulder rule.
- **Contract D:** full-horizon **`parity_ready_bridge_gate`** still **false** on IC-2 paired runs (post-contact spikes unchanged); remains **diagnostic-only**.
- **Contract B:** still **deferred** (no analytical joint limits in bridge).
- **Default gravity sign:** **opt-in** for **`mujoco`** — formal default review (**E**) **not yet**; see **§6**.

---

## 5. Decision options for supervisor / user

| Option | Description |
|--------|-------------|
| **A** | Accept current evidence as **sufficient** for thesis / reporting **contract C** narrative (two passive ICs + explicit `t_cut` discipline). |
| **B** | Request **one more IC** replication (**P2-M2**) for additional breadth before freezing prose. |
| **C** | Defer **torque-driven** or **non-passive** replication to a **later** scoped phase (separate contract note). |
| **D** | Approve **planning only** for dashboard / reporting **schema** (markdown or design doc); **no** `weekly_dashboard.py` or canonical JSON implementation yet. |
| **E** | Approve **formal review** of whether **`bridge_gravity_sign=mujoco`** could become a **reviewed default** later (still separate from threshold edits). |

---

## 6. Supervisor / user decisions recorded (2026-05-11)

| Option | Decision |
|--------|----------|
| **A** — Accept current evidence for **contract C** narrative | **YES, provisional** |
| **B** — Request **P2-M2** / one more IC | **DEFER** unless supervisor specifically asks for examiner robustness |
| **C** — Torque-driven / non-passive replication | **DEFER** |
| **D** — Dashboard / reporting **schema** planning (markdown or design doc only) | **YES, planning only** — still **no** `weekly_dashboard.py` or canonical JSON without a separate implementation approval |
| **E** — Review **`bridge_gravity_sign=mujoco`** as possible default | **NOT YET** — keep **opt-in** pending broader replication and sign-off |

---

## 7. Recommended next action (exactly one)

**Dashboard / reporting schema planning in markdown only** — [`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md). **No** `weekly_dashboard.py`, contract-path JSON writes, or threshold changes until implementation is separately approved.
