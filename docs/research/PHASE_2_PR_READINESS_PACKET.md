# Phase 2 PR Readiness Packet

**Purpose:** Summarize what belongs on a **push/PR** for branch `phase-2-contract-c` after Option B (derived JSON) and Option C (dashboard reader) work, and what must stay **out of scope**. This file is **planning only**; it does not authorize `git push`, CI changes, or canonical output edits.

**Related:** [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) · [`LANE_A_OPTION_C_DASHBOARD_READER_APPROVAL_PACKET.md`](LANE_A_OPTION_C_DASHBOARD_READER_APPROVAL_PACKET.md) · [`docs/REPO_LAYOUT.md`](../REPO_LAYOUT.md) section 7 (canonical KPI paths)

---

## 1. Branch and commits

| Item | Value |
|------|--------|
| **Branch** | `phase-2-contract-c` |

**Recent Phase 2 Lane A / governance / dashboard reader stack (chronological):**

| Hash | Summary |
|------|---------|
| `e7ba1993` | `chore(phase-2): curated Lane A baseline (research, diagnostics, ai-cowork)` |
| `3bd3db37` | `chore(phase-2): add agent guardrails and reporting schema plan` |
| `793ff0b1` | `chore(phase-2): add derived Lane A contract report` |
| `c7c43661` | `feat(phase-2): render Lane A contract report in dashboard` |

*(Tip: `git log --oneline -10` on this branch for full parent chain.)*

---

## 2. Included scope

- **Lane A contract governance (C / D / B framing):** Decision board, reporting schema plan, reporting contract notes, supervisor review cross-links; contract **C** primary provisional, **D** diagnostic-only, **B** deferred, **`bridge_gravity_sign=mujoco`** opt-in until separate sign-off.
- **`.ai-cowork/` and agent rules:** Introduced/curated under baseline commit `e7ba1993` and guardrails commit `3bd3db37` (paths per those commits; do not expand scope in this PR without listing paths).
- **Option B — derived contract JSON:** `runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json`, builder, README, evidence packet (`793ff0b1`); schema plan section 3a documents extension fields (`t_cut_*` provenance, `diagnostic_warning`).
- **Option C — dashboard reader:** `systematic_studies/lane_a_contract_report_html.py` + `weekly_dashboard.py` integration (`c7c43661`); read/display-only Lane A HTML subsection; firewall from `JSON_SPECS` canonical KV tables.
- **Tests:** `tests/test_lane_a_option_b_reader.py` + `tests/fixtures/lane_a_contract_report_min.json`.

---

## 3. Excluded scope

- **Canonical KPI JSON writes** under `docs/REPO_LAYOUT.md` section 7 (`systematic_studies/outputs/*.json`, `example_two_link/metrics/eval_sac_two_link_arm.json` contract paths) — not part of Option B/C commits.
- **Threshold / default / harness flag changes** (including `bridge_gravity_sign` default flip) — deferred per Decision Board / supervisor option **E**.
- **Simulation / XML / benchmark generator edits** — out of scope for this PR narrative unless a separate approval exists.
- **Native MATLAB parity** runs or runner debugging — parked unless explicitly resumed.
- **P2-M2 / extra ICs / torque-driven (non-passive) replications** — supervisor-deferred unless requested for examiner robustness.
- **Unrelated dirty-tree artifacts** (see section 6) — do not bulk-add with `git add .`.

---

## 4. Tests run

**From committed Option C work (evidence at merge time):**

- `python -m unittest tests.test_lane_a_option_b_reader -v` — **8 tests, OK** (fixture HTML, guardrail, derived banner, missing JSON, no canonical KPI JSON mutation on fixture copies, helper isolation from `JSON_SPECS` / `_flatten_json`, wiring order in `weekly_dashboard.py`).

**Not required for this packet (historical / optional):**

- `scripts/parity_smoke.sh` / `scripts/parity_full.sh` — **not** run as part of Option C implementation sign-off (per Mission Control constraints on that tranche).
- Broader suite (e.g. `tests/test_parity_*`) — run at maintainer discretion before merge if CI does not already cover regressions on `weekly_dashboard.py` import path.

---

## 5. Safety checks

- **No `systematic_studies/outputs/*.json` changes** were part of Option B/C commits; pre-commit checks used `git diff --name-only` on those paths (empty). PR should keep that discipline: no accidental KPI JSON in the same PR as unrelated local edits.
- **No benchmarks / parity scripts** were run for Option C dashboard reader implementation (per approval packet).
- **Dashboard reader** only **reads** `runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json` and injects HTML; it does **not** write canonical metrics JSON or pass Option B `records[]` through `render_json_table` / `_flatten_json`.

---

## 6. Remaining dirty tree

After removing **only** root-level directories matching `tests.test_lane_a_option_b_reader*` (accidental temp roots from `Path(self.id())` in tests), a typical local tree may still show **unrelated** items, for example:

- `Matlab_v2/` modified and untracked media/scripts
- `tools/gh*` archives and binaries
- `assets/skill-zips/`, `codex/skills/` untracked
- Various `docs/research/*.md` modified or untracked (approval packets, governance, notes)
- `runs/diagnostics/...` untracked evidence (not the committed Option B JSON path unless separately committed)
- `.DS_Store`, `__pycache__`, `MUJOCO_LOG.TXT`, `systematic_studies/run_native_matlab_parity.py`, etc.

**None of the above** should be swept into a focused Phase 2 Lane A PR without explicit path-scoped staging.

---

## 7. Recommended PR title / body

**Title:** `phase-2: Lane A derived contract report + dashboard reader`

**Body (draft):**

```markdown
## Summary
- Phase 2 Lane A: contract-labeled governance docs and derived Option B aggregate under `runs/diagnostics/`.
- Option C: weekly dashboard reads Option B JSON and renders a separate derived Lane A HTML section (read/display only; no canonical KPI JSON writes).

## Key commits
- e7ba1993 — Phase 2 curated baseline (research / diagnostics / ai-cowork)
- 3bd3db37 — Agent guardrails + reporting schema plan
- 793ff0b1 — Option B derived `lane_a_contract_report.json` + builder + README + evidence
- c7c43661 — Option C `lane_a_contract_report_html` + `weekly_dashboard` integration + tests

## Tests
- `python -m unittest tests.test_lane_a_option_b_reader -v`

## Out of scope / not in this PR
- Canonical `systematic_studies/outputs/*.json` changes
- Thresholds, defaults, simulation/XML, benchmarks, parity_smoke/full, native MATLAB parity

## Docs
See `docs/research/PHASE_2_PR_READINESS_PACKET.md` on branch for full checklist.
```

---

## 8. Pre-push checklist

- [ ] Run `git status` — confirm no accidental `git add .`
- [ ] Run `python -m unittest tests.test_lane_a_option_b_reader -v` (and any extra tests your CI runs on touched modules)
- [ ] `git diff --name-only` / `git diff --cached --name-only` — **no** unexpected `systematic_studies/outputs/*.json` or eval KPI path
- [ ] If staging: **explicit paths only** (Mission Control allowlist), never `git add .`
- [ ] Optional: open generated HTML locally **once** with `--no-open` workflow if you need visual confirmation (does not write canonical JSON)

---

## 9. Next action

**Ask user approval to push branch** — confirm remote target, whether dirty-tree docs should land in the same PR or a follow-up, and CI expectations before `git push`.
