# Lane A contract reporting (Option B — derived only)

This directory holds **machine-readable, contract-labeled** Lane A reporting artifacts built **only** from existing files under `runs/diagnostics/`.

## What this is

- **`lane_a_contract_report.json`** — Aggregated rows for **contract C** (pre-limit window, `bridge_gravity_sign=mujoco`) on two passive ICs plus one **contract D** full-horizon diagnostic row (IC-2 exemplar).
- **`build_lane_a_contract_report.py`** — Regenerates the JSON from the same derived inputs (no simulation, no canonical writes).

## What this is not

- **Not** canonical dashboard output. Option B remains **derived / non-canonical**: nothing here is read from or written to `systematic_studies/outputs/` or the KPI paths in `docs/REPO_LAYOUT.md` section 7.
- **Not** a substitute for `weekly_dashboard.py` or HTML reporting until a separate **Option C+** approval exists.

## Provenance and diagnostics (JSON)

- **Record 1 (original passive C):** `t_cut_source`, `t_cut_rule_source`, and `t_cut_provenance_note` state explicitly that `t_cut=0.480` follows the established contract-C baseline window / evidence chain, not a `t_cut_s` key inside the `gravsign_prelimit` object of `parity_prelimit_gravity_sign/prelimit_compare.json`.
- **Record 2 (IC-2 C):** the same three fields tie `t_cut` / `t_cut_rule` to `ic_2/prelimit_compare.json`.
- **Record 3 (D):** `diagnostic_warning` carries fixed wording for future Option C HTML so full-horizon D is never mistaken for contract-C smooth parity.

## Purpose

Validate the field layout and governance labels in [`LANE_A_REPORTING_SCHEMA_PLAN.md`](../../../docs/research/LANE_A_REPORTING_SCHEMA_PLAN.md) before any dashboard code work.

## Contracts

- **C** — Smooth pre-limit window metrics only; strict claims apply **only** with stated `t_cut`, `bridge_gravity_sign`, and IC (here: original passive + IC-2).
- **D** — Full-horizon mixed XML-limited vs unconstrained bridge; **`parity_ready_bridge_gate`** remains **diagnostic**; do not read as **C** failure.
- **B** — Still deferred; not represented as a metric row.

## Regenerate

From repo root:

```bash
python3 runs/diagnostics/lane_a_reporting_schema/build_lane_a_contract_report.py
```

## Evidence

Option B evidence packet: [`../evidence_packets/lane_a_reporting_schema_option_b.md`](../evidence_packets/lane_a_reporting_schema_option_b.md).
