# Lane A Reporting Note

Thesis- and report-facing summary of **Lane A** (MuJoCo vs Python **bridge** analytical dynamics on the derived passive swing benchmark). **Canonical** dashboard JSON under `systematic_studies/outputs/` is unchanged by this note; figures below are **derived** unless stated otherwise.

**Related:** [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) · [`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`](LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md) · [`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md)

---

## 1. Purpose

Lane A reporting must **separate** two different questions:

1. **Smooth unconstrained dynamics parity** — agreement where both simulators represent the same ODE class (no hard joint-limit impulses in the reference model).
2. **Limit-contact diagnostics** — disagreement after MuJoCo **XML joint limits** engage, where the bridge has **no** matching constraint force.

Conflating (2) with (1) misstates the science. This note fixes vocabulary (**C / A / D / B**) and points to **evidence** so strict claims attach to the **right contract**.

---

## 2. Contract labels

| Label | Name | What it is |
|-------|------|--------------|
| **C** | Pre-limit / no-contact smooth dynamics parity | Metrics evaluated only **before** first shoulder nominal limit crossing on the benchmark window (here: **`time_s < 0.480` s**, **480** samples on the stored passive 500-step series). Both sides are in a **comparable unconstrained segment** for that horizon. |
| **A** | No-limit MuJoCo diagnostic companion | MuJoCo run with **`--mujoco-joint-limits disabled`** (in-memory): full-horizon **ODE-class** MuJoCo vs unconstrained bridge **without** XML limit impulses. **Not** the shipped MJCF limit law. |
| **D** | Legacy mixed full-horizon XML-limited diagnostic | Default harness: **XML-limited MuJoCo** vs **unconstrained** bridge over the **full** rollout. Legacy dashboard / `parity_ready_bridge_gate` roll-ups reflect this **mixed** contract unless relabeled. |
| **B** | Future constrained parity | Bridge/MATLAB would implement **matched** analytical joint limits / contact (penalty, hard stop, or equivalent to MuJoCo limit law). **Not** available today; **no** full constrained strict claim until **B** exists. |

---

## 3. Current headline findings

- **qdot2 spike/jerk** on the XML-limited MuJoCo trajectory is **explained** by **shoulder joint-limit constraint activation** in MuJoCo vs an **unconstrained** bridge (force decomposition and limit inspection in the evidence chain).
- **No-limit ablation** (`--mujoco-joint-limits disabled`) **removes** local and whole-run **velocity spike / jerk** counters on the derived benchmark; the event is **not** treated as an unexplained unconstrained ODE bug in isolation.
- **Pre-limit baseline (C, default `bridge_gravity_sign`)**: **relaxed** compare_signals-style gate on the window **passes**; **strict** swing-style RMSE analogue on the window **fails**.
- **Pre-limit gravity-sign derived run (C, `bridge_gravity_sign=mujoco`)**: **strict** swing-style analogue on contract **C** **passes** (derived recompute / probe artifacts).
- **Full-horizon XML-limited (D)**: **`parity_ready_bridge_gate` remains false** (limit-contact transients still fail the gate). That outcome must **not** be reported as “smooth dynamics failed” **without** stating that the comparison is **mixed contract D**, not **C**.

**Primary evidence packets (non-exhaustive):**

- `runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md`
- `runs/diagnostics/evidence_packets/lane_a_prelimit_metrics_probe.md`
- `runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md`

**Machine-readable window comparison:** `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json`

---

## 4. Metrics snapshot

Contract **C** window: **`time_s < 0.480`**, **480** rows; MuJoCo **`mujoco_joint_limits`**: XML-limited in these pre-limit recomputations (spike/jerk **on window** already **zero** before and after gravity-sign). **Strict swing-style window gate** uses the same RMSE / spike / jerk rules as the swing benchmark analogue on **window rows only** (see evidence packet).

| Metric / claim | Baseline pre-limit (C) | Gravity-sign pre-limit (C) | Full-horizon XML-limited note (D) |
|----------------|------------------------:|-----------------------------:|-------------------------------------|
| `rmse_q_rad` | 2.321372 | 0.621015 | Whole-run RMSE not a substitute for **C**; **D** gate still driven by post-contact behaviour |
| `rmse_qd` (combined / as in JSON) | 12.159637 | 3.387841 | Same caveat |
| `velocity_spike_count_mujoco` (window) | 0 | 0 | Full horizon: nonzero spike counts on baseline XML-limited runs (see ablation packet) |
| `velocity_jerk_outlier_count_mujoco` (window) | 0 | 0 | Full horizon: nonzero on baseline XML-limited |
| Strict swing-style **window** gate | false | true | N/A for window |
| `parity_ready_bridge_gate` (full-horizon roll-up) | — | — | **false** (remains **false** with gravity-sign on **D**; do not read as **C** failure) |

Values in the **C** columns are from `prelimit_compare.json` (`baseline_prelimit` vs `gravsign_prelimit`), rounded for display to six decimals where applicable.

---

## 5. Provenance requirements

Any Lane A line in a thesis, paper, or future dashboard row should state at minimum:

- **Contract label** (**C**, **A**, **D**, or **B** when it exists)
- **Time window / cutoff** (e.g. `time_s < 0.480` or `first_shoulder_crossing`)
- **Sample count** (e.g. **480** for this **C** window)
- **`bridge_gravity_sign`** (`default` vs `mujoco` / opt-in flag)
- **`mujoco_joint_limits`** (`xml` / `disabled` for **A**)
- **Whether limit contact occurs** in the reported window (for **C**: **no** on this benchmark definition)
- **Artifact paths** (repo-relative JSON/CSV + evidence packet markdown)
- **Canonical vs derived** (`systematic_studies/outputs/…` vs `runs/diagnostics/…`)

---

## 6. Reporting guidance

- Use **contract C** for **smooth unconstrained dynamics** strict claims on this passive benchmark, with **explicit** cutoff and **`bridge_gravity_sign`** in the prose.
- Use **contract A** as a **diagnostic companion** for full-horizon ODE-class MuJoCo vs bridge (limits off).
- Treat **contract D** as **legacy / full-horizon diagnostic** only; label it **mixed** and do not fold it into **C** conclusions.
- Do **not** claim **constrained parity B** until an analytical joint-limit / contact model is implemented and validated.
- Do **not** change **thresholds** or **canonical dashboard fields** without explicit approval (`docs/REPO_LAYOUT.md` dashboard paths; supervisor alignment per `docs/PHD_DIRECTIONS.md`).

---

## 7. Open questions

- Should **`bridge_gravity_sign=mujoco`** become the **default** in harnesses, or remain **opt-in** pending thesis/supervisor review?
- Should the **weekly dashboard** (or other tooling) add **explicit contract labels** and provenance fields rather than a single unlabeled roll-up?
- Should **constrained parity B** be scheduled as a later modeling project after **C** (+ **A**) narratives are frozen?
- Should **pre-limit contract C** (with stated cutoff) become the **canonical** Lane A metric in JSON/HTML, or stay **derived-only** until approval?

---

## 8. Next recommended action

**Plan supervisor-facing Lane A summary** — a short spoken or one-page brief using this note’s contract labels, the metrics table, and the rule that **D ≠ C**.
