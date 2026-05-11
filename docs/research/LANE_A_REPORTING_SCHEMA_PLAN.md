# Lane A Reporting Schema Plan

Design-only: defines **field names**, **contracts**, **provenance**, and **display intent** for Lane A swing parity reporting **before** any `weekly_dashboard.py` or canonical JSON changes. Aligns with [`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md), [`LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md), [`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`](LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md), [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md), and [`PHASE_2_SUPERVISOR_REVIEW_UPDATE.md`](PHASE_2_SUPERVISOR_REVIEW_UPDATE.md).

---

## 1. Purpose

This document specifies a **reporting schema** (data shape and semantics) for Lane A metrics so that thesis text, future HTML dashboards, and machine-readable exports **cannot silently mix** incompatible comparison regimes. It is **not** implementation: it does **not** authorize edits to `systematic_studies/weekly_dashboard.py`, canonical paths under `docs/REPO_LAYOUT.md` section 7, thresholds, harness defaults, or simulation/XML. Numeric examples below cite **existing derived JSON** where shown; any full-horizon **D** roll-up in examples is **illustrative** unless a specific `swing_benchmark_summary*.json` path is attached in a later revision.

---

## 2. Reporting contracts

| Label | Name | Definition |
|-------|------|------------|
| **C** | Pre-limit / no-contact smooth-dynamics parity | Metrics on **`time_s < t_cut`** where **`t_cut`** is **IC-specific**: first MuJoCo **`baseline_default`** CSV row with **`mj_q1_deg >= 120`**, fixed **before** RMSE tuning. Both bridge and MuJoCo are interpreted on the **same unconstrained segment** (no shoulder limit contact inside the window on the benchmark definitions used to date). **Primary** lane for strict unconstrained claims on the passive swing family. |
| **A** | No-limit MuJoCo diagnostic companion | MuJoCo with **`--mujoco-joint-limits disabled`** (in-memory), full horizon vs unconstrained bridge: **ODE-class** diagnostic; **not** shipped XML limit law. |
| **D** | Full-horizon XML-limited diagnostic | Default harness: **XML-limited MuJoCo** vs **unconstrained** bridge over the **full** rollout. Legacy dashboard / `parity_ready_bridge_gate` style roll-ups are **D** unless relabeled. **Not** interchangeable with **C** for strict smooth-dynamics publication claims. |
| **B** | Future constrained parity | Bridge (and native MATLAB, if in scope) implement a **matched** analytical joint-limit / contact model to MuJoCo’s limit law. **Deferred**; no **B** metrics should appear as “ready” until that model exists and is validated. |

---

## 3. Required provenance fields

| Field | Type | Required for | Meaning |
|-------|------|--------------|---------|
| `contract_label` | enum `C` \| `A` \| `D` \| `B` | **All** rows | Which comparison regime this row represents. |
| `metric_scope` | enum `window` \| `full_horizon` | **All** | **C** uses `window` (pre-limit). **A** typically `full_horizon`. **D** uses `full_horizon` for legacy roll-ups. |
| `horizon_type` | enum `pre_limit` \| `no_limit_mujoco` \| `xml_limited_mixed` \| `future_matched_limits` | **All** | Fine-grained horizon tag; must be consistent with `contract_label`. |
| `source_csv` | string (repo-relative path) | **All** | Primary MuJoCo (and/or bridge) timeseries CSV used to compute the row, if applicable. |
| `source_summary_json` | string (repo-relative path) | **All** when available | Summary or compare JSON (e.g. `prelimit_compare.json`, future `swing_benchmark_summary.json`). |
| `evidence_packet` | string (repo-relative path) | **C**, **D** claims in prose | Markdown evidence packet backing interpretation. |
| `run_id` | string | **All** | Stable id for this benchmark run (probe batch, git SHA + tag, or tool-generated id). |
| `ic_label` | string | **All** | Human-readable IC id (e.g. `original_passive`, `IC-2`). |
| `q1_deg` | float | **All** for passive IC rows | Initial shoulder angle (deg). |
| `q2_deg` | float | **All** for passive IC rows | Initial elbow angle (deg). |
| `qd1_rad_s` | float | **All** for passive IC rows | Initial shoulder velocity (rad/s). |
| `qd2_rad_s` | float | **All** for passive IC rows | Initial elbow velocity (rad/s). |
| `tau_amp` | float | **All** for passive IC rows | Passive baseline uses `0`. |
| `bridge_gravity_sign` | enum `default` \| `mujoco` | **All** rows involving bridge dynamics | Harness flag; **C** strict claims with `mujoco` must declare this explicitly. |
| `mujoco_joint_limits` | enum `xml` \| `disabled` | **All** | `xml` for production-style **C** / **D**; `disabled` for **A**. |
| `t_cut` | float (s) or null | **C** required | End of **C** window (exclusive upper bound on `time_s` per current convention). **Null** for pure **A**/**D** full-horizon-only rows if no window is defined. |
| `t_cut_rule` | string | **C** required | Verbatim rule (e.g. first `mj_q1_deg >= 120` on `baseline_default` MuJoCo CSV; `time_s < t_cut`). |
| `sample_count` | int | **C** required; **D** recommended | Row count in the evaluated interval. |
| `time_start_s` | float | **C**, **D** | Start time of evaluated interval (often `0.0`). |
| `time_end_s` | float | **C**, **D** | End time of last included sample in window (e.g. `0.479` s for 480-row **C** on original IC). |
| `limit_contact_present` | bool | **C** required | Whether shoulder (or relevant) limit contact occurs **inside** the reported window; **false** for current **C** definitions on file. |
| `derived_or_canonical` | enum `derived` \| `canonical` | **All** | `derived` = under `runs/diagnostics/…`; `canonical` = `systematic_studies/outputs/…` contract paths until policy changes. |
| `created_by` | string | **All** | Human username, agent id, or script name that produced the row. |
| `notes` | string | Optional | Free text (e.g. “P2-M1 replication”, “planning pseudo-row”). |

### 3a. Option B derived-report extensions (`runs/diagnostics/…`)

Option B ships a machine-readable aggregate at [`runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json`](../../runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json) (see [`lane_a_reporting_schema_option_b.md`](../../runs/diagnostics/evidence_packets/lane_a_reporting_schema_option_b.md)). That JSON extends the row shape with the fields below. They are **derived-report safe**: they clarify **t_cut** provenance and surface a **D** warning for UI consumers; they **do not** imply canonical dashboard KPI output, writes to `systematic_studies/outputs/`, or approval to edit `weekly_dashboard.py`.

| Field | Type | Required for | Meaning |
|-------|------|--------------|---------|
| `t_cut_source` | string | **C** (Option B rows) | Stable anchor for where **`t_cut`** comes from (e.g. repo-relative path with fragment `#t_cut_s`, or a narrative id when **`t_cut`** aligns to the established contract-**C** baseline window / evidence chain rather than a `t_cut_s` key inside `gravsign_prelimit` in a given `prelimit_compare.json` object). |
| `t_cut_rule_source` | string | **C** (Option B rows) | Stable anchor for **`t_cut_rule`** text (e.g. `#t_cut_rule` on the IC-2 `prelimit_compare.json`, or explicit note that rule text matches the shared primary rule documented on the IC-2 probe). |
| `t_cut_provenance_note` | string | **C** (Option B rows) | Human-readable explanation so **C** rows carry **explicit t_cut provenance** and readers do not infer a false byte-for-byte copy from a summary block that only carries window aggregates. |
| `diagnostic_warning` | string | **D** (Option B rows) | Fixed warning string for markdown/HTML consumers; **D** rows must carry an **explicit diagnostic warning** so full-horizon mixed-contract metrics are **not** interpreted as contract-**C** smooth-dynamics parity. |

**Policy:** **C** records in Option B (and recommended future derived exports) should populate `t_cut_source`, `t_cut_rule_source`, and `t_cut_provenance_note` wherever **`t_cut`** is not trivially copied from the same JSON object as the window metrics. **D** records should populate `diagnostic_warning` verbatim where tooling expects a single audit-friendly string (e.g. before Option C dashboard reads).

---

## 4. Metric fields

| Field | Type | Contract relevance | Meaning |
|-------|------|-------------------|---------|
| `rmse_q_rad` | float | **C**, **A**, **D** | RMS joint angle error (rad) over evaluated scope. |
| `rmse_qd` | float | **C**, **A**, **D** | Combined or defined RMS velocity error (rad/s) per tool contract. |
| `max_abs_dev_q1_rad` | float | **C**, **A**, **D** | Max absolute q1 deviation on scope. |
| `max_abs_dev_q2_rad` | float | **C**, **A**, **D** | Max absolute q2 deviation on scope. |
| `max_abs_dev_qdot1_rad_s` | float | **C**, **A**, **D** | Max absolute qdot1 deviation on scope. |
| `max_abs_dev_qdot2_rad_s` | float | **C**, **A**, **D** | Max absolute qdot2 deviation on scope. |
| `velocity_spike_count_mujoco` | int | **C**, **D** (and **A** when defined) | MuJoCo spike count on scope (tool definition). |
| `velocity_jerk_outlier_count_mujoco` | int | **C**, **D** (and **A** when defined) | MuJoCo jerk outlier count on scope. |
| `strict_swing_window_gate` | bool | **C** (window analogue) | Strict swing-style gate evaluated **on window rows only** (same rule family as benchmark analogue). |
| `relaxed_compare_signals_window_gate` | bool | **C** | Relaxed compare_signals-style gate on window, when computed. |
| `parity_ready_bridge_gate_full_horizon` | bool or null | **D** primary; **null** for pure **C**-only rows | Legacy mixed full-horizon gate; **must not** be read as **C** without `contract_label=D` and diagnostic labeling. |
| `interpretation_label` | string | **All** | Short controlled tag for UI (e.g. `c_smooth_strict_pass`, `d_diagnostic_gate_fail`, `not_claimed`). |

---

## 5. Example records (pseudo-rows; provenance from repo)

Values for **C** + `mujoco` match derived JSON: [`runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json`](../../runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json) (`gravsign_prelimit`) and [`runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json`](../../runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json) (`gravsign_prelimit`). **D** example states **`parity_ready_bridge_gate_full_horizon: false`** per reporting consensus; attach a concrete summary path when promoting to archival rows.

### 5a. Original passive baseline — contract **C**, `bridge_gravity_sign=mujoco`

```yaml
contract_label: C
metric_scope: window
horizon_type: pre_limit
source_csv: "<path to baseline_default 500-step CSV for original IC>"
source_summary_json: runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json
evidence_packet: runs/diagnostics/evidence_packets/lane_a_prelimit_gravity_sign_trajectory_probe.md
run_id: derived_m1_prelimit_gravsign
ic_label: original_passive
q1_deg: <from benchmark IC; not repeated in prelimit_compare.json>
q2_deg: <from benchmark IC>
qd1_rad_s: <from benchmark IC>
qd2_rad_s: <from benchmark IC>
tau_amp: 0
bridge_gravity_sign: mujoco
mujoco_joint_limits: xml
t_cut: 0.480
t_cut_rule: "PRIMARY: first row where mj_q1_deg >= 120 on baseline_default MuJoCo CSV; window time_s < t_cut"
sample_count: 480
time_start_s: 0.0
time_end_s: 0.479
limit_contact_present: false
derived_or_canonical: derived
created_by: schema_plan_example
notes: "RMSE from gravsign_prelimit block in prelimit_compare.json"
rmse_q_rad: 0.621015
rmse_qd: 3.387841
strict_swing_window_gate: true
relaxed_compare_signals_window_gate: true
parity_ready_bridge_gate_full_horizon: null
interpretation_label: c_smooth_strict_pass
```

### 5b. P2-M1 IC-2 — contract **C**, `bridge_gravity_sign=mujoco`

```yaml
contract_label: C
metric_scope: window
horizon_type: pre_limit
source_csv: runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_timeseries_500.csv
source_summary_json: runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json
evidence_packet: runs/diagnostics/evidence_packets/lane_a_phase2_p2m1_ic2_contract_c_replication.md
run_id: P2-M1_ic2
ic_label: IC-2
q1_deg: 2.0
q2_deg: 50.0
qd1_rad_s: 0.02
qd2_rad_s: -0.03
tau_amp: 0
bridge_gravity_sign: mujoco
mujoco_joint_limits: xml
t_cut: 0.477
t_cut_rule: "PRIMARY: first row (min time_s) where mj_q1_deg >= 120.0 on baseline_default MuJoCo CSV; window time_s < t_cut"
sample_count: 477
time_start_s: 0.0
time_end_s: 0.476
limit_contact_present: false
derived_or_canonical: derived
created_by: schema_plan_example
notes: "gravsign_prelimit block in ic_2/prelimit_compare.json"
rmse_q_rad: 0.576505
rmse_qd: 3.279675
strict_swing_window_gate: true
relaxed_compare_signals_window_gate: true
parity_ready_bridge_gate_full_horizon: null
interpretation_label: c_smooth_strict_pass
```

### 5c. Contract **D** — full-horizon XML-limited diagnostic (illustrative)

```yaml
contract_label: D
metric_scope: full_horizon
horizon_type: xml_limited_mixed
source_csv: "<paired MuJoCo XML-limited 500-step CSV>"
source_summary_json: "<e.g. systematic_studies/outputs/swing_benchmark_summary*.json when cited>"
evidence_packet: runs/diagnostics/evidence_packets/lane_a_joint_limit_ablation.md
run_id: example_full_horizon_d
ic_label: IC-2
q1_deg: 2.0
q2_deg: 50.0
qd1_rad_s: 0.02
qd2_rad_s: -0.03
tau_amp: 0
bridge_gravity_sign: mujoco   # illustrative; declare actual flag per run
mujoco_joint_limits: xml
t_cut: null
t_cut_rule: "N/A — full horizon"
sample_count: 500
time_start_s: 0.0
time_end_s: 0.499
limit_contact_present: true   # expect contact in XML-limited long horizon on this benchmark family
derived_or_canonical: derived   # or canonical if reading shipped summary JSON
created_by: schema_plan_example
notes: "Gate false on mixed contract per Lane A reporting note"
rmse_q_rad: "<from summary JSON>"
rmse_qd: "<from summary JSON>"
strict_swing_window_gate: null
relaxed_compare_signals_window_gate: null
parity_ready_bridge_gate_full_horizon: false
interpretation_label: d_diagnostic_gate_fail
```

---

## 6. Dashboard display recommendation (markdown or future HTML)

Suggested **layout blocks** (top to bottom):

1. **Contract C headline card** — “Smooth pre-limit (**C**)” with **strict** / **relaxed** window gates, **RMSE q / qd**, **`t_cut`**, **`sample_count`**, **`bridge_gravity_sign`**, **`ic_label`**. Visual emphasis: **primary** scientific claim for passive swing unconstrained segment.
2. **Contract D diagnostic warning card** — bordered **warning** style: “**Mixed XML-limited vs unconstrained bridge (D)** — **not** **C**.” Show `parity_ready_bridge_gate_full_horizon` only here with spike/jerk context. No language implying **D** failure equals unconstrained ODE bug.
3. **Provenance block** — collapsible table or monospace list: `source_summary_json`, `source_csv`, `run_id`, `derived_or_canonical`, `created_by`, `t_cut_rule`.
4. **Evidence links** — bullets to `evidence_packet` markdown and key derived JSON paths.
5. **“Not claimed” block** — static checklist: **B** not implemented; **A** optional companion; native MATLAB replay parked unless resumed; **default** `bridge_gravity_sign` remains **opt-in** until separate governance (**E** not yet per supervisor record).

---

## 7. Implementation boundary

This schema plan is **markdown design only**. It is **not** approval to edit **`weekly_dashboard.py`**, canonical KPI JSON under **`docs/REPO_LAYOUT.md`** section 7, simulation/XML, thresholds, or harness defaults. **Implementation** (code, new canonical fields, or promotion of derived rows into canonical outputs) requires a **separate explicit approval** aligned with [`PHASE_2_SUPERVISOR_REVIEW_UPDATE.md`](PHASE_2_SUPERVISOR_REVIEW_UPDATE.md) and the Decision Board permission packet.

---

## 8. Validation rules before implementation

- Every exported or dashboard-backed **metric** must include **`contract_label`** consistent with **`horizon_type`** and **`metric_scope`**.
- Every **C** metric must include **`t_cut`**, **`t_cut_rule`**, and **`sample_count`** consistent with the stated window.
- Every **D** metric must surface a **diagnostic-only** warning in UI or adjacent markdown (**mixed contract**).
- Every row that depends on **`bridge_gravity_sign`** must state **`bridge_gravity_sign`** explicitly (no silent default assumption in copy).
- **No** canonical metric row may be produced by **promoting** derived diagnostics **without** an explicit governance step (path review, contract labels frozen, and approval recorded).

---

## 9. Recommended next action (exactly one)

**Obtain user approval** to **stage and commit** only the agreed documentation paths (for example `docs/research/LANE_A_REPORTING_SCHEMA_PLAN.md` and any paired `docs/research/LANE_A_DECISION_BOARD.md` link edits) when the user is ready—**before** any dashboard implementation or canonical JSON work.

---

**Related:** [`LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md) · [`LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`](LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md)
