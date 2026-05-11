# Lane A Model-Contract Decision Brief

## 1. Purpose
This brief exists because the **MuJoCo qdot2 spike/jerk** signature on the derived 500-step passive swing benchmark is now **explained**: it arises from **XML joint-limit constraint dynamics in MuJoCo** compared against an **unconstrained** Python bridge (and MATLAB-native dynamics without equivalent hard limits). **Strict parity and whole-run RMSE** against the current mixed setup remain **open** and must not drive more ad-hoc debugging without an explicit **model contract**. Lane A needs a written choice (or staged sequence) among comparability regimes so that evidence, gates, and thesis claims stay aligned with `docs/PHD_DIRECTIONS.md` (bridge vs native MATLAB; strict vs relaxed gates).

**Related planning (no dashboard code in these files):** [`LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md`](LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md) · [`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md)

## 2. Current evidence state
Evidence-backed consolidation (artifacts under `runs/diagnostics/evidence_packets/` and derived CSV/JSON):

- **qdot2 event reproduces** on the baseline XML-limited derived 500-step run (integrator ablation packet; historical window match).
- **Force decomposition** at event rows shows **nonzero `qfrc_constraint`** on the shoulder DOF while the bridge remains smooth (`lane_a_mujoco_force_decomposition_event_states.md`).
- **Joint-limit inspection** shows the shoulder **first crosses the nominal +120° bound at step 480** (0.48 s) with elbow limits never violated on that horizon (`lane_a_joint_limit_contract_inspection.md`).
- **No-limit ablation** (`--mujoco-joint-limits disabled`) **removes** local (0.47–0.49 s) spike/jerk and clears **whole-run** `velocity_spike_count` / `velocity_jerk_outlier_count`, while **`parity_ready_bridge_gate` stays false** due to **RMSE** (`lane_a_joint_limit_ablation.md`).
- **Gravity sign vs limits:** ablation shows **limit-contact** drives the **qdot2 spike/jerk** magnitude, not bridge gravity sign alone. For **contract C** trajectory RMSE, **`bridge_gravity_sign=mujoco`** materially improves agreement and **closes pre-limit strict** gate on the derived passive benchmark (M1; `lane_a_prelimit_gravity_sign_trajectory_probe.md`). Static `qacc` sign reconciliation remains in `lane_a_static_gravity_qacc_reconciliation.md`.
- **Damping / SysID / integrator / COM inertia** branches are **parked or bounded**: damping sweep and SysID improve pieces of error but did not resolve the spike under XML limits; RK4 reduces magnitude only; COM swap negative (`lane_a_damping_sweep.md` and decision board rows A5–A8).

### 2a. Pre-limit baseline metrics probe (completed; default gravity sign)
Derived recomputation on **stored** CSVs only (`runs/diagnostics/evidence_packets/lane_a_prelimit_metrics_probe.md`, machine-readable `runs/diagnostics/parity_prelimit_metrics/prelimit_metrics.json`):

- **Window:** `time_s < 0.480` (strict); **480 rows** per series; time range **0.0–0.479 s** (pre shoulder nominal +120° crossing on this benchmark).
- **Relaxed `compare_signals`-style gate** (parity smoke / full thresholds on **max abs** q and qdot deviations **plus** zero MuJoCo and bridge spike/jerk counts **on window rows only**): **passes** on pre-limit baseline and pre-limit no-limit.
- **Strict swing `parity_ready_bridge_gate` analogue** (same RMSE and spike/jerk rules as `swing_benchmark_mujoco_vs_bridge.py`, evaluated on window rows only): **fails** under **default** bridge gravity sign — RMSE q ≈ **2.32 rad** and RMSE qdot ≈ **12.16 rad/s** remain far above strict **0.75 / 10** even before contact.
- **MuJoCo** whole-window spike and jerk counts (**summed joints**): drop from **7 / 9** (full 500-step XML-limited) to **0 / 0** pre-limit; **max |Δqdot2|/dt** drops from **~932** to **~45** rad/s² on the window.
- **Baseline vs no-limit** trajectories are **identical** on the pre-contact window (metrics match at floating precision), as expected before limit forces diverge.

**Answer (baseline):** pre-limit **RMSE q** improves only modestly vs full mixed horizon (~**2.32** vs ~**2.42** rad); the dominant qualitative change vs full **D** is **removal of spike/jerk** and **passing relaxed max-dev gate**; **strict** RMSE on **C** required **`bridge_gravity_sign=mujoco`** (section 2b).

### 2b. Pre-limit gravity-sign trajectory probe (M1; completed)
Same **contract C** window and rules, with **`--bridge-gravity-sign mujoco`** on the derived passive 500-step inputs (`runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md`, `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json`):

- **Strict** swing-style analogue on the window: **passes** — RMSE q ≈ **0.62 rad**, RMSE qdot ≈ **3.39 rad/s** (within strict **0.75 / 10**).
- **Full-horizon XML-limited (D)** summary with gravity-sign still reports **`parity_ready_bridge_gate: false`** (limit-contact spike/jerk unchanged)—**do not** read M1 as full-run strict closure.

**Answer (M1):** under **C** with **`mujoco`** gravity sign, **pre-limit strict** gate **closes** on this benchmark; **D** remains a separate **legacy/diagnostic** story.

## 3. Core contract problem
The current **strict-style comparison** in the swing benchmark **mixes** **constrained MuJoCo** (joint `range` + `limited`) with **unconstrained analytical** bridge/MATLAB dynamics. Under passive gravity rollouts, the trajectories are comparable only until **limit contact**; beyond that, MuJoCo injects **constraint forces** that have **no counterpart** in the analytical ODE. Treating disagreement there as “dynamics bug” without naming the contract is **methodologically invalid** for publication-grade **strict** claims.

## 4. Candidate Lane A contracts

| Option | Contract | What it measures | Pros | Cons | Evidence needed | Recommended use |
|--------|-----------|------------------|------|------|-----------------|-----------------|
| **A. Unconstrained dynamics parity** | MuJoCo **joint limits off** in-memory for agreed probes (`--mujoco-joint-limits disabled`); bridge unchanged | Smooth **ODE** agreement (q, qdot, hand proxy) without limit impulses | Isolates **integrator, parameters, gravity sign, damping** mismatch; spike/jerk counters no longer dominated by limit artefact | **Not** the shipped MJCF physics; unlimited angles may be unphysical for thesis biomechanics | RMSE and local errors on same IC/torque schedule; document provenance JSON fields | **Diagnostic companion lane** alongside a primary scientific contract |
| **B. Constrained parity** | Bridge/MATLAB implement **equivalent limits** (smooth penalties, hard stops, or hybrid) matching MuJoCo limit law | Full **limit-contact** agreement including impulses / constraint forces | Matches **production XML** intent; strict gates become interpretable end-to-end | **High implementation cost**; must define limit law equivalence (stiffness, restitution, soft vs hard) | Side-by-side `qfrc_constraint` or penalty torque parity; phase-plane tests | **Later explicit modeling project**; not the immediate unblocker for ODE mismatch |
| **C. Pre-limit / no-contact parity** | Evaluate metrics **only for times before first shoulder limit contact** (e.g. **t < 0.480 s** on current derived benchmark) or redesign IC/horizon to **stay inside** limits | **Unconstrained segment** agreement where both simulators represent the same ODE class | **Scientifically targeted** for Paper 1-style “smooth dynamics” claims; avoids conflating contact with ODE error | Does not validate limit behavior; window length depends on IC | Pre-limit RMSE, velocity traces, optional gravity-sign slice | **Primary next scientific target** for strict-style **unconstrained** claims |
| **D. Current mixed contract** | XML-limited MuJoCo vs unconstrained bridge/MATLAB in one gate | Mixed **ODE + contact** disagreement | Zero extra work; reproduces legacy dashboard numbers | **Invalid** as **publication-grade strict parity** for the full horizon; spike/jerk “failure” largely **artefact of contract** | Already satisfied: ablation + decomposition | **Diagnostic / legacy only**; label clearly in reports |

## 5. Recommended contract for next phase
### 5a. Reporting / scoring contract (explicit)
Lane A **primary reporting and scoring** target for **unconstrained** bridge-vs-MuJoCo agreement on the passive swing benchmark:

| Role | Contract | Label |
|------|-----------|--------|
| **Primary** | **C — Pre-limit / no-contact unconstrained parity** | Score RMSE, deviations, and (if desired) relaxed gates on **`time_s < 0.480`** (or IC-defined equivalent), documented per run. |
| **Diagnostic companion** | **A — No-limit full-horizon MuJoCo** | `--mujoco-joint-limits disabled` with full CSV/JSON provenance; isolates ODE class over **entire** horizon vs unconstrained bridge. |
| **Deferred** | **B — Constrained parity** | Mirror joint limits / contact in analytics; **explicit later project**, not the gate for current ODE mismatch. |
| **Legacy / diagnostic only** | **D — Mixed** | XML-limited MuJoCo vs unconstrained bridge full horizon; **do not** treat spike/jerk failures here as unexplained ODE bugs. |

**Primary recommendation (unchanged in substance):** **C** is the **authoritative lane** for **scientific** unconstrained claims; **A** is the **companion diagnostic**; **B** is **deferred** until **C** (and optionally **A**) characterize remaining error.

### 5b. Rationale (one paragraph)
Pre-limit evidence shows **limit-contact** dominated **full-run spike/jerk**. Under **default** bridge gravity sign, **strict RMSE** on **C** still **failed**; with **`bridge_gravity_sign=mujoco`**, **pre-limit strict** gate **passes** on the derived passive benchmark (M1). Reporting must **label contract** (**C / A / D / B**), **horizon/window**, **`bridge_gravity_sign`**, and **artifact path** so readers do not treat **D** roll-ups as **C** claims—see **`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`**.

## 6. Dashboard / gate implication
- The historical **`velocity_spike_count` / `velocity_jerk_outlier_count` failure** on the **XML-limited** swing benchmark is **primarily explained** by **limit-contact mismatch**, not by unexplained unconstrained dynamics alone.
- **RMSE remains open** and should be read under an **explicit contract** (pre-limit C, or diagnostic no-limit A). Whole-run RMSE under **D** mixes regimes and is easy to **misinterpret**.
- **`systematic_studies/weekly_dashboard.py`** and the JSON paths in `docs/REPO_LAYOUT.md` (section 7, dashboard contract) should eventually **annotate or split** metrics by contract (e.g. “mixed / diagnostic”, “pre-limit unconstrained”, “no-limit MuJoCo”, **`bridge_gravity_sign`**) so **unconstrained** mismatch is not conflated with **constraint-contact** mismatch. **Planning only** until approval: **`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`**. **No threshold or path edits are made in this brief.**
- Until contracts are wired into tooling, treat existing dashboard **strict** numbers that include the post-contact segment as **legacy / diagnostic** for Lane A spike discussion.

## 7. Proposed next experiments
**1** (pre-limit derived recompute) and **M1** (pre-limit trajectory with **`--bridge-gravity-sign mujoco`**) are **complete** on stored / already-produced derived artifacts. **Optional when runs are approved:** crossed **A** + gravity-sign full-horizon benchmark. **Reporting (no new physics):** execute **`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md` §6** (markdown-first Lane A note) before any dashboard wiring.

| # | Experiment | Information value | Cost | Risk | What a clear result would mean |
|---|------------|-------------------|------|------|----------------------------------|
| **1** | **Derived pre-limit metric recomputation** — baseline **default** gravity sign | Baseline **C** under default sign | **Low** | IC-dependent window | Done: strict **failed** (~2.32 / ~12.16); relaxed passed |
| **M1** | **Pre-limit trajectory with `--bridge-gravity-sign mujoco`** | Closes **strict** question for **C** on this passive benchmark | **Low** (derived recompute / approved run already reflected in diagnostics) | Must label sign in all **C** KPIs | Done: pre-limit **strict passes** (~0.62 / ~3.39); **D** still false |
| **2 (optional)** | **No-limit (`A`) + gravity-sign** full-horizon rerun | Separates **sign** from **limits** over **entire** horizon under **A** | **Medium** (new sim if not already archived) | Factor interaction | Useful companion; **C** primary already has M1 |
| **3** | **Model-contract reporting** — markdown (then optional derived JSON) describing **D vs C vs A vs B** | High **communication** value; prevents misclaim | **Low** if text-only | Skipped ⇒ misread risk | **Next** per reporting plan §6 |

**Experiment 1:** **done** — section 2a, `lane_a_prelimit_metrics_probe.md`.

**M1:** **done** — section 2b, `lane_a_prelimit_gravity_sign_trajectory_probe.md`.

**Recommended next (no new benchmark required for narrative closure):** **3** — markdown-only Lane A reporting note, then governance review before canonical dashboard fields.

## 8. Recommended next action
**Markdown-first Lane A reporting** per **`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md` §6**: add a short **`docs/research/`** note linking contracts **C/A/D/B**, provenance fields, and derived artifacts (`prelimit_compare.json`, M1 packet). **No** `weekly_dashboard.py` or canonical JSON path edits until explicit approval. Remaining science (optional): **M3** local `qacc` / mass–damping alignment; **D** full-horizon strict still **not closed**; **B** deferred.

## 9. Stop rules
- **Stop** treating the **mixed-contract (D)** full-horizon swing benchmark as **publication-grade strict parity** for Lane A until relabeled or split.
- **Do not** change **thresholds** until the **active contract** for each KPI is declared and supervisor-aligned (`docs/PHD_DIRECTIONS.md` methodological risks).
- **Do not** implement **constrained bridge limits (B)** until **unconstrained** mismatch is **characterized** under **C** (and diagnostics **A** as needed).
- **Do not** run **full** `parity_smoke.sh` / `parity_full.sh` as the primary Lane A unblocker until **pre-limit** (or explicitly agreed **A/B**) contract language is in place.

## 10. Open questions
- ~~Does **pre-limit** RMSE (`C`) improve **materially** vs whole-run mixed RMSE (`D`) on the same artifacts?~~ **Resolved (modest):** RMSE q drops ~**4%**; spike/jerk and relaxed max-dev gate change **qualitatively** (see section 2a).
- ~~Under **contract C**, does **`--bridge-gravity-sign mujoco`** close **pre-limit strict**?~~ **Resolved:** **yes** on derived passive benchmark (M1; section 2b). **Open:** whether **A** full-horizon needs an additional crossed run for thesis scope.
- Should the **thesis** present **limit-contact** behavior as a **separate** robustness / constraints subsection rather than burying it inside “parity failed”?
- What becomes the **canonical Lane A parity contract** for the dashboard and Paper 1: **C**, **A**, staged **B**, or a labeled combination?

## 11. Decision impact (Decision Board)
This brief should drive **`docs/research/LANE_A_DECISION_BOARD.md`** to:
- **Link** prominently to **`docs/research/LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`** as the authoritative contract options and stop rules, and to **`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`** for dashboard/reporting layers.
- **Record** pre-limit baseline (section 2a), **M1** gravity-sign trajectory closure on **C** (section 2b), and the **explicit reporting contract** (section 5a).
- **Set recommended next action** to **markdown-first reporting** (section 8 / reporting plan §6), not further spike hunting.
- **Keep** joint-limit hypothesis **supported** and spike/jerk **explained**; **add** explicit language that **dashboard strict KPIs** on the **mixed** full horizon are **legacy/diagnostic** for spike interpretation until annotated.
- **State** **C + `bridge_gravity_sign=mujoco`** supports **pre-limit strict** closure on this passive benchmark (**A12**); **D** strict full-horizon remains **not closed**; **B** deferred.
