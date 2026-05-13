# Phase 2 Post-Merge Decision Packet

**Purpose:** Record consolidation decisions after **PR #1** (“Phase 2 contract C publish”) merged the clean publish line into **`commit-changes`**. This packet is **governance / research ops only**; it does not authorize new features, benchmarks, canonical output writes, or simulation edits.

**Related:** [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) · [`PHASE_2_PR_READINESS_PACKET.md`](PHASE_2_PR_READINESS_PACKET.md) · [`LANE_A_REPORTING_SCHEMA_PLAN.md`](LANE_A_REPORTING_SCHEMA_PLAN.md)

---

## 1. Merge status

| Item | Value |
|------|--------|
| **PR** | #1 — Phase 2 contract C publish (title on GitHub as merged) |
| **Target branch** | `commit-changes` |
| **Merged tip** | `837f7913` — `Merge pull request #1 from USinani/phase-2-contract-c-publish` |
| **Source branch** | `phase-2-contract-c-publish` |
| **Publish stack through** | `f30b1108` — `docs(phase-2): add PR readiness packet` |

---

## 2. What is now mainline

The following are **on `origin/commit-changes` at `837f7913`** (first-parent history includes the publish cherry-pick stack):

- **Mission Control / agent guardrails:** `.cursor/rules/` (010–040), `AGENTS.md`, `CLAUDE.md`, `.ai-cowork/` doctrine and templates (per merged commits).
- **Lane A governance docs:** Decision board, reporting schema plan, reporting contract notes, supervisor review cross-links, Phase 2 clean-fork / supervisor packets as merged.
- **Option B — derived / non-canonical contract-labeled JSON:** `runs/diagnostics/lane_a_reporting_schema/lane_a_contract_report.json`, builder `build_lane_a_contract_report.py`, README, evidence packet under `runs/diagnostics/evidence_packets/`.
- **Option C — dashboard reader:** `systematic_studies/lane_a_contract_report_html.py` and **read-only** wiring in `systematic_studies/weekly_dashboard.py` (HTML subsection + CSS firewall from canonical `JSON_SPECS` tables).
- **PR readiness packet:** `docs/research/PHASE_2_PR_READINESS_PACKET.md`.
- **Tests:** `tests/test_lane_a_option_b_reader.py`, fixture `tests/fixtures/lane_a_contract_report_min.json`, plus Lane A gate tests and diagnostics tests introduced in the baseline merge (paths per merged tree).

---

## 3. Scientific / reporting stance now accepted

These align with the merged **Option B** governance block in `lane_a_contract_report.json` and existing Decision Board / schema plan language:

- **Contract C** is **primary / provisional** for **smooth-dynamics** reporting on the **two passive ICs** evidenced in the Lane A chain (see Decision Board and pre-registered replication packets under `runs/diagnostics/`).
- **Contract D** remains **diagnostic-only** (full-horizon XML-limited vs unconstrained bridge; not interchangeable with **C** for strict smooth-dynamics publication claims).
- **Contract B** (matched analytical limits) remains **deferred**.
- **`bridge_gravity_sign=mujoco`** remains **opt-in** in harness defaults; merged code preserves **default** behaviour unless the flag is set.
- **P2-M2 / non-passive replication** remains **deferred** unless **examiner robustness** is explicitly requested (supervisor option framing; see `PHASE_2_SUPERVISOR_REVIEW_UPDATE.md`).
- **No canonical output, threshold, XML, or harness-default change** was approved **by** the merge narrative: the PR added **derived** diagnostics, **read/display** dashboard HTML, tests, and governance markdown — not edits to live `systematic_studies/outputs/*.json` KPI files.

---

## 4. Verified tests

Evidence gathered on the **merged tree at `837f7913`** (post-merge verification run; not re-run as part of authoring this markdown unless recorded below).

Commands:

```bash
python -m unittest tests.test_lane_a_option_b_reader -v
```

**Result:** **8 tests, OK.**

```bash
python -m unittest tests.test_bridge_gravity_sign \
  tests.test_swing_benchmark_mujoco_damping_scale \
  tests.test_swing_benchmark_mujoco_integrator_override \
  tests.test_swing_benchmark_mujoco_joint_limits_override \
  tests.test_lane_a_option_b_reader -v
```

**Result:** **24 tests, OK.**

---

## 5. Safety boundaries preserved

- **No live canonical** `systematic_studies/outputs/*.json` **rewrites** are claimed by this merge line; Option B JSON lives under **`runs/diagnostics/`** and is labeled **`derived_or_canonical: "derived"`** in the shipped aggregate.
- **Option C** remains **read/display-only**: module docstring states no JSON writes and no canonical KPI path writes; Lane A subsection is **not** fed through `JSON_SPECS` flattening.
- **Dashboard reader does not interleave** Option B rows into **`JSON_SPECS`** / canonical KPI tables — separate HTML section and CSS firewall (see `weekly_dashboard.py` comments on merge).
- **`.venv` avoided** for GitHub by using the **clean publish branch** (`phase-2-contract-c-publish`); merged **`commit-changes`** tip has **no tracked `.venv`** at HEAD (`git ls-files .venv` → empty on clean checkout).
- **Dirty local artifacts** on other working copies (e.g. primary tree still on `phase-2-contract-c`) are **not** part of the merged GitHub line unless separately committed.

---

## 6. Remaining local workspace issue

- **Primary working copy** (`/Users/uljan/Desktop/Mujoco`) may remain on **`phase-2-contract-c`** with a **dirty** tree (local MATLAB, docs, `__pycache__`, replication dirs, etc.).
- **Local branch `commit-changes`** may still be **behind** **`origin/commit-changes`** until the user checks out and fast-forwards.
- **`git checkout commit-changes`** can **fail** if local modifications would be **overwritten** — this is a **local workspace hygiene / branch-sync** issue, **not** a defect in the merged GitHub line.
- **Resolution (out of scope for this packet):** stash, second clone, or selective clean — only with **explicit user approval**; do not bulk-clean dirty research artifacts without a separate hygiene packet.

---

## 7. Open research / development decisions

| ID | Decision | Notes |
|----|----------|--------|
| D1 | **Manual HTML preview** of the weekly dashboard Lane A section | String/unit tests exist; **no** browser/visual QA recorded on mainline yet. |
| D2 | **Stricter required-field validation** for Option B JSON in the reader | Trade-off: fail-hard vs soft degrade for partial hand-built JSON. |
| D3 | **P2-M2** scope | Only if examiner robustness explicitly requested (supervisor framing). |
| D4 | **Promote any derived metric to canonical** | Requires **separate approval** and `docs/REPO_LAYOUT.md` / dashboard contract updates — **not** implied by PR #1. |
| D5 | **Clean or archive dirty local experimental artifacts** | Separate **hygiene / provenance** packet; do not conflate with Lane A science gates. |

**Note on Decision Board links:** [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) references `LANE_A_DASHBOARD_IMPLEMENTATION_APPROVAL_PACKET.md` and `LANE_A_OPTION_C_DASHBOARD_READER_APPROVAL_PACKET.md`. Those files are **not** present under `docs/research/` on the merged tree at **`837f7913`** (ten markdown files only). Treat as **broken links / drafts elsewhere** until added or relinked in a future doc-only change.

---

## 8. Recommended next action

Choose **exactly one:**

- ~~create post-merge research decision packet~~ **(this packet completes that step)**  
- **manual HTML preview packet** — **recommended next**  
- required-field hardening packet  
- local workspace sync/hygiene packet  
- stop and ask user  

**Recommendation:** **manual HTML preview packet** first — the merged dashboard reader has **string/unit tests** but **no** recorded **visual / browser QA**; a short preview checklist (screenshots or “expected section headers”) does **not** require new science, benchmarks, or canonical output changes.

---

## 9. Non-goals

- **No new features** beyond documentation-driven QA checklists unless a separate approval exists.
- **No benchmarks** / parity scripts / native MATLAB replay as part of this consolidation tranche.
- **No canonical outputs** under `systematic_studies/outputs/` or `example_two_link/metrics/` contract paths.
- **No XML / threshold / default** changes to harness or simulation from this packet.
- **No dirty-tree cleanup** in this packet.
- **No `git push`** implied by this file — push remains a separate Mission Control step.

---

**Permission status (this document):** research markdown only; **Allowed** for `docs/research/` consolidation. **Needs review** before any code or canonical-path edits.
