# Lane A Reporting Contract Update Plan

Planning only: consolidates Lane A evidence into **reporting layers** and defines **provenance** and **dashboard options**. **No** `weekly_dashboard.py` edits, **no** canonical JSON writes, **no** threshold or default-flag changes in this document (`docs/PHD_DIRECTIONS.md` strict vs relaxed gates remain supervisor-governed).

---

## 1. Purpose

Readers and automation currently see a **single** swing benchmark roll-up (`parity_ready_bridge_gate`, RMSE, spike counts) that **mixes** (D) **XML-limited MuJoCo** with an **unconstrained** bridge over the **full horizon**. That **conflates**:

1. **Limit-contact** artefacts (spike/jerk on MuJoCo after shoulder limit engagement), and  
2. **Unconstrained ODE** disagreement (RMSE before contact, gravity convention, parameters).

Reporting must **label the contract** (C / A / D / future B) so thesis and dashboard consumers do not treat **D** numbers as **C** claims—or vice versa. `docs/REPO_LAYOUT.md` section 7 lists **canonical** dashboard paths; Lane A derived evidence lives under `runs/diagnostics/…` until an explicit approval extends the HTML contract.

---

## 2. Evidence summary

| Finding | Artifact / path |
|--------|-------------------|
| **Joint-limit ablation** removed MuJoCo **qdot2 spike/jerk** (local and whole-run counters) when `--mujoco-joint-limits disabled` | `lane_a_joint_limit_ablation.md`, `parity_joint_limit_ablation/*` |
| **Pre-limit baseline** (`t < 0.480`, bridge default): **relaxed** compare_signals-style gate **passes**; **strict** swing-style RMSE gate **fails** (~2.32 rad, ~12.16 rad/s) | `lane_a_prelimit_metrics_probe.md`, `prelimit_metrics.json` |
| **Pre-limit + `--bridge-gravity-sign mujoco`**: RMSE **materially** improves vs baseline pre-limit on same window | `lane_a_prelimit_gravity_sign_trajectory_probe.md`, `prelimit_compare.json` |
| **Pre-limit strict swing-style gate** **closes** with gravity-sign on derived 500-step passive run | same |
| **Full-horizon** XML-limited: `parity_ready_bridge_gate` **still false** (spike/jerk from limit contact); full-run RMSE improves with gravity-sign but gate dominated by MuJoCo transients | `swing_benchmark_summary_500_gravsign.json` vs baseline summaries |

---

## 3. Proposed reporting layers

| Layer | Contract | Input artifact | Intended claim | Status | Caveats |
|-------|-----------|----------------|----------------|--------|---------|
| **C** | Pre-limit / no-contact smooth dynamics | Derived CSV + `prelimit_compare.json` or recomputation `t < t_cut` | **Strict unconstrained** agreement for passive swing **before** shoulder limit contact, with explicit `bridge_gravity_sign` | **Supported** for this IC/horizon with `mujoco` sign | Window is **IC-dependent**; not limit-contact validation |
| **A** | No-limit MuJoCo diagnostic | `--mujoco-joint-limits disabled` + summary JSON | Full-horizon **ODE-class** MuJoCo vs bridge without joint impulses | **Available** | Not shipped MJCF physics |
| **D** | Legacy mixed full-horizon | Default `swing_benchmark_summary.json` (canonical path) | **Regression / integrity** signal; **not** publication-grade strict **C** claim | **Legacy** | Spike/jerk largely **contract** artefact vs unconstrained bridge |
| **B** | Future constrained parity | TBD analytical limits | End-to-end limit-contact agreement | **Deferred** | High modeling cost |

---

## 4. Required provenance fields

Any future dashboard row or Lane A report line for swing parity should expose at minimum:

| Field | Example | Why |
|-------|---------|-----|
| **horizon / window** | `full` \| `pre_limit` | Distinguishes C from D |
| **cutoff time** | `0.480` s or `first_crossing` | Reproducibility for C |
| **`bridge_gravity_sign`** | `default` \| `mujoco` | Major trajectory lever (M1) |
| **`mujoco_joint_limits`** | `xml` \| `disabled` | Limit vs ODE diagnostic (A) |
| **sample count** | `480` | Window size |
| **limit contact in window** | `false` / `true` | Validity of unconstrained interpretation |
| **metric class** | `canonical` \| `derived` | Canonical = `systematic_studies/outputs/…`; derived = `runs/diagnostics/…` |
| **artifact path** | repo-relative path | Audit trail |

---

## 5. Dashboard / code update options (planning only)

| Option | Pros | Cons | Risk | Recommended use |
|--------|------|------|------|-----------------|
| **A. Markdown-only Lane A report section** | Zero code risk; fast; versioned in `docs/research/`; aligns with PhD narrative | Not visible in HTML dashboard until linked manually | Low | **First** deliverable |
| **B. Derived JSON report** under `runs/diagnostics/` only | Machine-readable; CI can grep; no canonical contract change | Duplicates some KPI semantics; another file to maintain | Low | Optional companion to A |
| **C. Canonical dashboard fields** (after approval) | Single source in weekly HTML; aligns team | Touches `weekly_dashboard.py` + possibly JSON contract per `REPO_LAYOUT.md` §7 | **Medium–high** (path/threshold discipline) | **Post** supervisor approval |
| **D. Leave dashboard unchanged** | No regression risk | Readers misread D as C | Medium (misclaim) | Interim until A or C done |

---

## 6. Recommended next reporting move

**Create a markdown-only Lane A reporting note** (implement **option A**): e.g. `docs/research/LANE_A_REPORTING_NOTE.md` or a subsection in an existing project update—summarizing layers C/A/D/B, linking to evidence packets and `prelimit_compare.json`, and stating that **canonical** `swing_benchmark_summary.json` remains **contract D** until code change is approved.

---

## 7. Governance / approval boundary

- **No** edits to `systematic_studies/weekly_dashboard.py` or canonical KPI JSON paths until **explicitly approved** (see `REPO_LAYOUT.md` section 7).
- **No** threshold changes without supervisor alignment (`docs/PHD_DIRECTIONS.md`).
- **No** default switch of `bridge_gravity_sign` to `mujoco` in harness without review (opt-in flag remains the safe default for backward compatibility).
- **No** “strict parity closed” publication claim for **full constrained** behavior until **B** (analytical limits) exists or **D** is explicitly defended.

---

## 8. Decision impact

- **Decision Board** should record: **contract C + `bridge_gravity_sign=mujoco`** is **supported** for **pre-limit strict closure** on the **derived passive 500-step** benchmark; **contract D** strict full-horizon remains **not closed**.
- **Next reporting move:** markdown-only note (**section 6**); dashboard code only after approval.
