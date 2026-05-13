# Lane A Supervisor Summary

Concise research-facing brief: **MuJoCo vs Python bridge** on the **derived passive 500-step swing benchmark**. Evidence lives under `runs/diagnostics/evidence_packets/` and derived JSON; **canonical** dashboard outputs are **not** modified by this document.

**Related:** [`LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md) · [`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`](LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md) · [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md)

---

## 1. Executive summary

- The historical **strict / full-horizon** swing gate **`parity_ready_bridge_gate`** **mixed** (1) **unconstrained ODE** disagreement with (2) **MuJoCo XML joint-limit contact** that has **no counterpart** in the unconstrained bridge—so a single roll-up **conflated two different failure modes**.
- The **qdot2 spike/jerk** signature is **traced** to **MuJoCo shoulder joint-limit constraint activation** (nonzero constraint generalized force on the shoulder DOF while the bridge stays smooth).
- **`--mujoco-joint-limits disabled`** (no-limit ablation) **removes** the local and whole-run **spike/jerk** counters on this benchmark, supporting the **limit-contact** explanation.
- **Contract C** (pre-limit / **no-contact**, here **`time_s < 0.480` s**, **480** samples) **separates** comparable **smooth dynamics** from post-contact **D** behaviour.
- With **`bridge_gravity_sign=mujoco`**, the **strict swing-style analogue on contract C** **passes** on this passive benchmark (derived probe; same window rules as documented in the evidence packet).
- **Contract D** (full-horizon XML-limited vs unconstrained bridge): **`parity_ready_bridge_gate` remains false** and should be read as **legacy / diagnostic mixed contract**, **not** as a pure “smooth ODE is wrong” verdict without that caveat.
- **Contract B** (matched analytical joint limits / contact in the bridge) is **deferred** until an explicit modeling effort exists; **no** publication-grade **full constrained** strict claim is supported yet.

---

## 2. Evidence chain

| Finding | Evidence artifact | Result |
|--------|-------------------|--------|
| Constraint force at event rows | `runs/diagnostics/evidence_packets/lane_a_mujoco_force_decomposition_event_states.md` | Nonzero **`qfrc_constraint`** on shoulder DOF at spike rows; bridge smooth |
| First shoulder crossing / limit context | `runs/diagnostics/evidence_packets/lane_a_joint_limit_contract_inspection.md` | Shoulder first crosses nominal bound at documented step/time on this IC |
| Spike/jerk removed when limits off | `runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md` | No-limit run clears spike/jerk counters; supports **limit law** as spike driver |
| Pre-limit baseline metrics (contract **C**) | `runs/diagnostics/evidence_packets/lane_a_prelimit_metrics_probe.md` | Relaxed window gate **passes**; **strict** RMSE analogue **fails** under default gravity sign |
| Pre-limit + gravity sign (contract **C**) | `runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md` | **`mujoco`** gravity sign: **strict** window analogue **passes**; machine table in `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json` |

---

## 3. Contract recommendation

| Role | Contract | Meaning |
|------|-----------|---------|
| **Primary reporting** | **C** — pre-limit / no-contact smooth dynamics | Score strict relaxed claims for **unconstrained segment** with stated **cutoff** and **`bridge_gravity_sign`**. |
| **Diagnostic companion** | **A** — no-limit MuJoCo | Full-horizon ODE-class MuJoCo vs bridge (`--mujoco-joint-limits disabled`); not shipped limit physics. |
| **Legacy / mixed diagnostic** | **D** — full-horizon XML-limited | Default mixed harness; **integrity / regression**; **not** sole basis for **C** strict claims. |
| **Deferred future** | **B** — constrained parity | Analytical limits/contact matched to MuJoCo; **later project**. |

---

## 4. Key metrics

Contract **C** window: **`time_s < 0.480`**, **480** rows (derived `prelimit_compare.json`, rounded for display). **Bridge:** Python analytical dynamics vs MuJoCo columns on stored series.

| Metric | Baseline pre-limit (C) | Gravity-sign pre-limit (C) | Meaning |
|--------|------------------------:|-----------------------------:|---------|
| `rmse_q_rad` | 2.321372 | 0.621015 | Large default-sign error on **C** collapses with **`mujoco`** sign |
| `rmse_qd` | 12.159637 | 3.387841 | Same |
| Strict swing-style **window** gate | false | true | **Strict** analogue on **C** **passes** only with **`bridge_gravity_sign=mujoco`** here |
| MuJoCo window spike / jerk (`velocity_spike_count` / `velocity_jerk_outlier_count`) | 0 / 0 | 0 / 0 | On **C**, no limit-contact in window; counters zero both cases |
| Full-horizon **`parity_ready_bridge_gate` (D)** | — | — | **Remains false** (including with gravity-sign on mixed runs); **diagnostic**, not **C** |

---

## 5. What this does not claim

- **Not** full **constrained parity** between XML-limited MuJoCo and the bridge (**B** not built).
- **Not** **native MATLAB** strict closure; automated Lane A work here is **bridge**-centric; native replay remains **parked** where noted on the Decision Board.
- **Not** a recommendation to change **defaults** in code (`bridge_gravity_sign`, harness flags) **without** your review—opt-in flag is evidence-backed for **C**, not a silent default switch.
- **Not** a **threshold** or **canonical JSON path** change proposal in this document.
- **Not** proof across **all** initial conditions, tasks, or torques; evidence is anchored on the **documented passive 500-step** benchmark and stated **C** cutoff.

---

## 6. Decision needed

Please confirm or adjust the following (reply with **A–D** choices or edits):

- **A.** Accept **contract C** (with explicit **time cutoff** and sample count) as the **primary Lane A metric** for **smooth unconstrained dynamics** claims on this benchmark family.
- **B.** Treat the current **mixed full-horizon** gate (**D**) as **diagnostic / legacy only**, not as the definition of “ODE parity failed” in prose.
- **C.** **Defer contract B** (analytical joint limits in the bridge) to a **later explicit modeling** phase unless you want it prioritized now.
- **D.** Decide whether **`bridge_gravity_sign=mujoco`** should **remain opt-in** for thesis figures or move toward a **reviewed default** in approved tooling (separate from threshold edits).

---

## 7. Next proposed work

- **Contract C replication:** repeat the **pre-limit + provenance** recipe on **one or two** additional ICs or tasks (passive or mild actuation) to bound generality before any dashboard canonicalization.
- **Dashboard / report annotation (after approval):** add **contract label**, **cutoff**, **`bridge_gravity_sign`**, and **canonical vs derived** fields per `docs/REPO_LAYOUT.md` governance—**no implementation** until you approve scope.
- **Later constrained parity (B):** only if thesis scope requires **limit-contact** agreement end-to-end; otherwise keep **C + A + labeled D** as the staged story.
