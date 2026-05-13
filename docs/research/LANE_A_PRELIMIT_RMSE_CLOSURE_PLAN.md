# Lane A Pre-Limit RMSE Closure Plan

Planning only (per mission control: one hypothesis, scored moves, red team). **No simulations, code, thresholds, or canonical outputs in this document.**

References: `.ai-cowork/mission-control.md`, `.ai-cowork/move-scorecard-template.md`, `.ai-cowork/red-team-critic.md`.

---

## 1. Active hypothesis

**Under contract C** (`time_s < 0.480`, no shoulder limit contact on this benchmark), a **material fraction** of the remaining **strict RMSE** (and max velocity deviation) between MuJoCo and the Python bridge is **explained by the same gravity / generalized-force sign convention gap** already visible in **static** `qacc` reconciliation, and is **testable** by **local one-step** dynamics agreement at **multiple** `(q, qdot, tau)` states sampled along the **stored** pre-limit trajectory—**before** re-interpreting the mismatch as generic “parameter tuning only.”

---

## 2. Current evidence

- **Pre-limit metrics** (`lane_a_prelimit_metrics_probe.md`, `prelimit_metrics.json`): on **`t < 0.480`**, **480** rows; **RMSE q ≈ 2.32 rad**, **RMSE qdot ≈ 12.16 rad/s**; MuJoCo **spike/jerk = 0**; relaxed `compare_signals`-style gate **passes**; **strict** swing-style RMSE gate **still fails**; baseline vs no-limit **identical** on this window (limits inactive pre-contact).
- **Static gravity / `qacc`** (`lane_a_static_gravity_qacc_reconciliation.md`, `gravity_sign_one_step.csv`): at **`q=[0,0]`**, `qdot=0`, `tau=0`, MuJoCo and bridge **`qacc`/`qdd` opposite sign**; a **bridge-side gravity sign flip** aligns **sign** (magnitudes still differ); rows **step470** show moderate disagreement; **step480/486** are **post-cutoff** and **contaminated** by limit dynamics—**not** valid for contract **C** conclusions.
- **Contract** (`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md` §5a): **Primary C** (pre-limit), companion **A** (no-limit full horizon), **B** deferred.

---

## 3. Candidate move scorecards

Scales (1–5): **information / goal alignment** = higher is better; **cost / risk** = higher is worse (more cost / more risk). **Reversibility**: 5 = fully reversible (derived artifacts only).

---

### Move M1 — Pre-limit gravity-sign **trajectory** probe (re-run benchmark, filter C)

| Field | Content |
|--------|--------|
| **Hypothesis tested** | If bridge `gravity_sign=mujoco` is the “right” convention for this MJCF, **pre-limit RMSE** should **drop materially** vs default bridge on the **same** IC and `t<0.480` filter. |
| **If true** | Pre-limit strict RMSE moves toward swing thresholds (or a documented fraction); supports labeling bridge default as wrong for strict MuJoCo comparison. |
| **If false** | Pre-limit RMSE unchanged or worsened; falsifies “sign alone closes pre-limit RMSE” and pushes weight to parameters / damping / integrator path. |
| **Information value** | 5 |
| **Cost** | 4 (requires **new** benchmark runs + derived CSV/JSON writes; not read-only). |
| **Risk** | 3 (confounds with other bridge options unless crossed carefully). |
| **Reversibility** | 5 (new files under `runs/diagnostics/`). |
| **Goal alignment** | 5 |
| **Artifact impact** | New timeseries + summary under `runs/diagnostics/…`; no canonical. |
| **Decision impact** | High: directly answers strict RMSE under **C** with one knob. |
| **Stop rule** | Stop after one crossed pair (default vs mujoco) if RMSE delta is negligible **and** M2 already shows local qacc cannot be aligned. |
| **Verdict** | **Defer** until **M2** (or M4) narrows whether the remaining error is locally convention-shaped. |

---

### Move M2 — Pre-limit **sparse one-step `qacc` / `qdd`** grid (stored states × gravity-sign modes)

| Field | Content |
|--------|--------|
| **Hypothesis tested** | At representative **dynamic** states along the pre-limit path, **sign and magnitude** of instantaneous acceleration from MuJoCo (`mj_forward`) vs bridge (`two_link_tennis_model` / equivalent) match better under **`gravity_sign=mujoco`** than default—linking **trajectory RMSE** to **local** generalized-force convention. |
| **If true** | Systematic sign (and partial magnitude) alignment at sampled `(q,qd,tau)` before 0.48 s; justifies M1 or thesis wording on convention. |
| **If false** | Mismatch persists or is erratic at same states; shifts focus to **M**, **damping**, **integrator**, or **state definition** (M3/M4). |
| **Information value** | 5 |
| **Cost** | 3 (small read-only or approved diagnostic script; MuJoCo + bridge calls at O(10–50) states). |
| **Risk** | 2 |
| **Reversibility** | 5 |
| **Goal alignment** | 5 |
| **Artifact impact** | One CSV + one evidence packet under `runs/diagnostics/…`. |
| **Decision impact** | High: connects **global pre-limit RMSE** to **local invariant** (mission-control lesson). |
| **Stop rule** | Stop sampling once **≥8** well-spread times show a stable pattern (all sign-correct under flip vs mixed) **or** no improvement after **20** states. |
| **Verdict** | **Proceed** (first executed move after planning). |

---

### Move M3 — **Parameter / mass-matrix** consistency under pre-limit states

| Field | Content |
|--------|--------|
| **Hypothesis tested** | `params_from_mujoco_xml` (masses, lengths, damping) matches compiled `MjModel` used in benchmark within tolerance; residual RMSE is **not** from stale parameter import. |
| **If true** | Parameters are aligned; do not spend SysID cycles on obvious mismatch. |
| **If false** | Identified field drift explains part of RMSE; fix import or XML mapping **with approval** (out of scope for this markdown-only step). |
| **Information value** | 3 |
| **Cost** | 2 |
| **Risk** | 1 |
| **Reversibility** | 5 |
| **Goal alignment** | 4 |
| **Artifact impact** | Small table in evidence packet. |
| **Decision impact** | Medium; often a **one-shot** gate before deeper dynamics work. |
| **Stop rule** | Single audit pass; if all within tolerance, **park** M3 unless model changes. |
| **Verdict** | **Proceed** as a **short parallel** prerequisite to M2 (read-only file inspection). |

---

### Move M4 — **IC / state convention** audit (row 0 + column semantics)

| Field | Content |
|--------|--------|
| **Hypothesis tested** | Benchmark ICs (`--q1-deg`, `--q2-deg`, `qd*`) are **identically** represented in MuJoCo vs bridge columns at `step=0`, and `bridge_q*` / `mujoco_q*` columns mean the same configuration (rad, same zero pose). |
| **If true** | No RMSE from trivial offset; proceed to dynamics probes. |
| **If false** | Documented offset or unit bug; fix harness **with approval** (out of scope here). |
| **Information value** | 3 |
| **Cost** | 1 |
| **Risk** | 1 |
| **Reversibility** | 5 |
| **Goal alignment** | 3 |
| **Artifact impact** | None or a few lines in an evidence packet. |
| **Decision impact** | High if failure found; low if pass (cheap insurance). |
| **Stop rule** | One pass on stored CSV row 0 + header contract. |
| **Verdict** | **Proceed** immediately (read-only); run **before or in same session as M2**. |

---

### Move M5 — **No-limit + gravity-sign** combined derived probe

| Field | Content |
|--------|--------|
| **Hypothesis tested** | Under **A** (full horizon, limits off) **and** `gravity_sign=mujoco`, whole-run and pre-limit slices both improve—testing interaction of **contract A** with sign. |
| **If true** | Useful for **diagnostic** ODE lane; not required for **C** if M1/M2 already answer pre-limit. |
| **If false** | Limits irrelevant to conclusion; saves runs. |
| **Information value** | 3 |
| **Cost** | 4 |
| **Risk** | 4 (two factors; broader scope). |
| **Reversibility** | 5 |
| **Goal alignment** | 3 |
| **Artifact impact** | Multiple benchmark outputs. |
| **Decision impact** | Medium for **A**; secondary for **C**. |
| **Stop rule** | Run **only if** M2 implicates sign but M1 (C-only trajectory) is inconclusive, or if thesis needs full-horizon unconstrained story. |
| **Verdict** | **Defer** (justified only after M1/M2 pattern is unclear or **A** explicitly needed). |

---

## 4. Red Team critique

| Check | Result |
|--------|--------|
| **Tests active hypothesis?** | M2 and M1 most directly; M3/M4 are **falsifiers** for confounders (parameters, IC). |
| **Either result change a decision?** | M4 pass → little change; M4 fail → **high** impact. M2 true → prioritizes convention in thesis + contract docs; M2 false → **deprioritize** sign narrative for pre-limit RMSE. |
| **Cheaper local invariant?** | **M4** is cheaper than M2; **M3** is comparable cost to M4. Static `qacc` already exists—**M2** is the smallest **dynamic** extension along the **same** trajectory. |
| **Redundant?** | M5 with M1 is partially redundant if M1 already crosses limit+sign; keep M5 **last**. M1 before M2 risks **expensive** runs without knowing local dynamic sign pattern—**defer M1** after M2. |
| **Broaden scope?** | M5 broadens most; keep deferred. |

**Synthesis:** **Adopt with label** — proceed with **M4 → M3** (read-only audits) immediately, then **M2** as the first **executable** science move that targets the active hypothesis. **Defer M1** until M2 indicates trajectory-level sign flip is worth the run cost. **Reject** executing M5 in the same tranche as M2.

---

## 5. Recommended next move

**M2 — Pre-limit sparse one-step `qacc` / `qdd` comparison** at states sampled from `swing_benchmark_timeseries_500.csv` with **`time_s < 0.480`**, for bridge **`gravity_sign=default`** and **`gravity_sign=mujoco`**, against MuJoCo `mj_forward` at identical `(qpos, qvel, ctrl)`—written to **`runs/diagnostics/…`** + one evidence packet.

**Prerequisite (same executor session, zero marginal scope):** run **M4** (and if time allows **M3**) first so M2 is not explaining a trivial IC/parameter bug.

---

## 6. Permission packet (for M2 + M4/M3)

**Allowed:** Read repo sources and stored CSV/JSON; write **only** under `runs/diagnostics/` (evidence packet + small derived CSV/JSON); small **read-only or diagnostic** Python **only when explicitly approved** for M2/M3 (this plan does not execute it).

**Forbidden:** Editing simulation harness, XML, thresholds, or canonical `systematic_studies/outputs/`; `parity_smoke.sh` / `parity_full.sh`; native MATLAB parity; skill edits.

**Approval required:** Any change to `swing_benchmark_mujoco_vs_bridge.py`, `matlab_v2_dynamics.py`, or other production code paths; any new default threshold; any write to dashboard contract JSON paths under `systematic_studies/outputs/` unless policy updated.

---

## 7. Stop rule (for this branch)

Stop the **pre-limit strict RMSE closure** branch when **one** of the following holds:

1. **M2** shows a **consistent** local acceleration story (sign/magnitude) that either **supports** or **refutes** the active hypothesis across the sampled pre-limit states, **and** the Decision Board is updated with a claim row; or  
2. **M4/M3** reveals a **configuration bug**; fix is scoped and **parked** until code approval; or  
3. **M1** (if later run) moves pre-limit strict RMSE by less than an **pre-declared epsilon** (define in evidence packet before run) **and** M2 already refuted the convention story—then **park** “sign-only closure” and pivot to integrator/parameter ablation under **C**.

Do **not** expand to full SysID or dashboard rewrites until **C** + local probes are exhausted or superseded by a new hypothesis on the Board.
