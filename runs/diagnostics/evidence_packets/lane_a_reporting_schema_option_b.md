# Evidence packet — Lane A reporting schema Option B (derived JSON)

## Question

Does a **derived-only**, **contract-labeled** JSON snapshot under `runs/diagnostics/` correctly materialize [`LANE_A_REPORTING_SCHEMA_PLAN.md`](../../../docs/research/LANE_A_REPORTING_SCHEMA_PLAN.md) without touching dashboard code or canonical outputs?

## Approved scope (Option B)

Per [`LANE_A_DASHBOARD_IMPLEMENTATION_APPROVAL_PACKET.md`](../../../docs/research/LANE_A_DASHBOARD_IMPLEMENTATION_APPROVAL_PACKET.md) **option B**:

- Read existing derived JSON/CSV only.
- Write **`runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json`**, this packet, `README.md`, and optional builder script under the same directory.
- **No** `weekly_dashboard.py`, **no** `systematic_studies/outputs/`, **no** thresholds, **no** harness default changes, **no** benchmarks.

Option B remains **derived / non-canonical** (top-level `derived_or_canonical: "derived"`). After the provenance patch: **Record 1** documents that `t_cut` is aligned to the baseline contract-C window / evidence chain, not read as `t_cut_s` from the `gravsign_prelimit` block of `parity_prelimit_gravity_sign/prelimit_compare.json`. **Record 3 (D)** includes `diagnostic_warning` for verbatim Option C dashboard display.

## Inputs

| Path | Role |
|------|------|
| `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json` | Contract **C** window metrics — original passive, `gravsign_prelimit` block |
| `runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_timeseries_500_gravsign.csv` | IC state row 0 for original passive **C** row |
| `runs/diagnostics/parity_prelimit_gravity_sign/swing_benchmark_summary_500_gravsign.json` | Referenced in report `notes` for original passive full-horizon **D** (not duplicated as third row) |
| `runs/diagnostics/phase2_contract_c_replication/ic_2/prelimit_compare.json` | Contract **C** window — IC-2, `gravsign_prelimit` + `t_cut` metadata |
| `runs/diagnostics/phase2_contract_c_replication/ic_2/gravsign_mujoco/swing_benchmark_summary_500.json` | Contract **D** full-horizon — IC-2, `parity_ready_bridge_gate`, RMSE, spike counts |

## Outputs

| Path | Role |
|------|------|
| `runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json` | Contract-labeled aggregate (`schema_version`, `governance`, `records[]`) |
| `runs/diagnostics/lane_a_reporting_schema/README.md` | Scope / non-canonical / regenerate instructions |
| `runs/diagnostics/lane_a_reporting_schema/build_lane_a_contract_report.py` | Deterministic rebuild from inputs |
| `runs/diagnostics/evidence_packets/lane_a_reporting_schema_option_b.md` | This packet |

## Schema summary (implemented)

- Top-level: `schema_version`, `created_at`, `created_by`, `derived_or_canonical` = `"derived"`, `implementation_option` = `"B"`, `governance` (C primary provisional, D diagnostic, B deferred, gravity-sign opt-in policy), `records` (length 3), `notes`.
- Each **record**: `contract_label`, `metric_scope`, `horizon_type`, `ic_label`, `run_id`, `source_artifacts`, `evidence_packet`, `t_cut` / `t_cut_rule` (C only), **`t_cut_source`**, **`t_cut_rule_source`**, **`t_cut_provenance_note`** (C rows), counts, `bridge_gravity_sign`, `mujoco_joint_limits`, gates, RMSE, MuJoCo spike/jerk on scope, `interpretation_label`, **`diagnostic_warning`** (D row only), `not_claimed[]`.

## Result classification

**Supports** — Option B can ship a schema-validated derived report without canonical or dashboard edits.

## Limitations

- **D** row is **one** exemplar (IC-2 `gravsign_mujoco` full-horizon summary); original passive full-horizon **D** is cited in `notes` / `not_claimed` only.
- **C** rows use **`bridge_gravity_sign=mujoco`** branch only (not default-sign **C** failure row in the same JSON).
- No content-hash of inputs stored in v1 JSON (could add in a later schema revision).
- Does not validate HTML rendering or `weekly_dashboard.py` ingestion.

## Next action (exactly one)

Re-run **Evidence Auditor** on the patched JSON, **or** prepare **Option C** approval packet if weekly HTML should read this JSON (use `diagnostic_warning` verbatim for D rows).
