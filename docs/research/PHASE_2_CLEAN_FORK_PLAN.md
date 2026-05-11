# Phase 2 Clean Fork Plan

**Planning only:** no repository copy, no deletes, no benchmarks, no simulation/XML/threshold edits, no canonical output writes. This document prepares a **Phase 2** workspace strategy after Lane A consolidation.

**Related:** [`LANE_A_DECISION_BOARD.md`](LANE_A_DECISION_BOARD.md) · [`LANE_A_SUPERVISOR_SUMMARY.md`](LANE_A_SUPERVISOR_SUMMARY.md) · [`LANE_A_REPORTING_NOTE.md`](LANE_A_REPORTING_NOTE.md) · [`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`](LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md) · [`LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md`](LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md)

---

## 1. Purpose

Lane A reached a **stable narrative and evidence chain** (joint-limit cause, **contract C** primary smooth metric, **M1** gravity-sign closure on the passive pre-limit window, **D** as diagnostic). The working tree still carries **broad untracked and mixed-modified paths** (research markdown, diagnostics runs, `.ai-cowork/`, tests/tools, large binary/tool drops per recent `git status --porcelain`). Phase 2 needs a **deliberate workspace boundary** so that:

- **Evidence and decisions** stay **findable and reproducible** without dragging irrelevant scratch.
- **Branch names and clone folders** stay **aligned** with “Lane A closed for cause; Phase 2 = contracts + reporting + optional replication,” avoiding stale “debug spike” branches.
- **Supervisor decisions (A–D)** can land on a **known baseline** (committed or tagged) rather than a moving uncommitted pile.

A **clean branch or sibling folder** is warranted **after** written approvals and a **reviewed** git state—not as an impulsive copy.

---

## 2. Current stable state

- **qdot2 spike/jerk** is **explained** as **MuJoCo shoulder joint-limit constraint** behaviour vs an **unconstrained** bridge in the same harness (**A10** supported on Decision Board).
- **Contract C** (pre-limit / no-contact, `time_s < 0.480` on the documented passive benchmark) is **recommended** as the **primary smooth-dynamics** reporting target; **A** companion, **D** legacy mixed, **B** deferred (`LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md` §5a).
- **Gravity-sign trajectory probe (M1):** with **`bridge_gravity_sign=mujoco`**, **strict swing-style analogue on contract C passes** on the derived passive run (**A12**); baseline **C** strict still fails under default sign (**A11**).
- **Full-horizon contract D** remains **`parity_ready_bridge_gate: false`** and must stay **diagnostic**, not folded into **C** claims.
- **Supervisor decisions A–D** are **provisionally recorded** in **§8a** (Mission Control, 2026-05-11); formal sign-off for harness **defaults** remains separate from this markdown record. For **git/branch readiness**, treat **§8a** as the controlling table alongside `LANE_A_SUPERVISOR_SUMMARY.md` §6 prompt text.
- **`.ai-cowork/`** exists as an **untracked blueprint** (Cursor/Codex commands, Mission Control templates, role stubs)—useful to **preserve** when freezing Phase 2 process.

---

## 3. What to preserve

- **Source code** tracked in git (Python/MATLAB/MJCF as applicable to Phase 2 scope); treat **modified** parity/benchmark files as **high-touch**—only migrate when intentionally part of Phase 2 baseline.
- **`docs/research/`** Lane A set (at minimum): `LANE_A_DECISION_BOARD.md`, `LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`, `LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md`, `LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`, `LANE_A_REPORTING_NOTE.md`, `LANE_A_SUPERVISOR_SUMMARY.md`, **this file** (`PHASE_2_CLEAN_FORK_PLAN.md`).
- **`.ai-cowork/`** (commands, templates, README) for repeatable agent workflow.
- **`.cursor/`** rules and commands **if** the team relies on them for parity discipline (optional copy to fresh folder; do not treat as Lane A evidence).
- **Selected evidence packets:** `runs/diagnostics/evidence_packets/lane_a_*.md` referenced by the Decision Board chain (see §5).
- **Selected derived artifacts** needed to **reproduce cited numbers** without re-simulating: e.g. `runs/diagnostics/parity_prelimit_gravity_sign/prelimit_compare.json`, `runs/diagnostics/parity_prelimit_metrics/prelimit_metrics.json`, and the ablation CSV/summary dirs cited in `lane_a_joint_limit_ablation.md` (paths inside that packet).
- **Tests added during this phase** (e.g. under `tests/test_*parity*`, `tests/test_*reporting*`, `tests/test_bridge_gravity_sign.py`, fixtures under `tests/fixtures/diagnostics/`) and **`tools/diagnostics/`** stdlib helpers **if** they are part of the agreed validation story—preserve **with** the commit that Phase 2 is pinned to.

---

## 4. What to exclude or archive

- **`__pycache__/`**, `*.pyc`, editor/OS noise (e.g. `.DS_Store`) from any **export** tarball or non-git copy (and add/keep ignore rules; do not commit junk).
- **Scratch outputs** not referenced by Decision Board or evidence packets (ad-hoc plots, one-off CSVs, duplicate probe dirs).
- **Redundant intermediate CSVs** if the **evidence packet** already points to the **canonical-within-diagnostics** path for that claim (archive elsewhere, not in the “lean Phase 2” tree).
- **Stale or untracked clutter** from `git status --porcelain`: e.g. large **`tools/gh_*.zip` / extracted `tools/gh_*` trees**, **`assets/skill-zips/`**, unrelated skill trees under `codex/skills/*-updated/` unless Phase 2 explicitly needs them—**exclude from curated copy** or keep only in **full** archive.
- **Anything not referenced** by Decision Board, supervisor summary, reporting note, or an evidence packet **should not** be in the **minimal** Phase 2 carry set (full repo backup is a separate decision).

---

## 5. Curated evidence set

Paths below are under `runs/diagnostics/evidence_packets/` unless noted.

| Evidence | Keep? | Why |
|----------|--------|-----|
| `lane_a_joint_limit_ablation.md` | **Yes** | Core **A10**: ablation removes spike/jerk; defines limit vs ODE split |
| `lane_a_prelimit_metrics_probe.md` | **Yes** | **Contract C** baseline: relaxed passes, strict fails under default sign (**A11**) |
| `lane_a_prelimit_gravity_sign_trajectory_probe.md` | **Yes** | **M1 / A12**: strict **C** passes with `bridge_gravity_sign=mujoco` |
| `lane_a_mujoco_force_decomposition_event_states.md` | **Yes** | **`qfrc_constraint`** at event rows; causal link to limits |
| `lane_a_joint_limit_contract_inspection.md` | **Yes** | First crossing / timing context for **C** window |
| `lane_a_static_gravity_qacc_reconciliation.md` | **Yes** | Static sign convention evidence; supports opt-in gravity sign narrative |
| `lane_a_prelimit_rmse_closure_tranche_m4_m3_m2.md` | **Yes** | M4/M3/M2 closure tranche; correlation fix, local `qacc`, damping/mass context |

**Also keep (referenced on Decision Board, not in table above):** `lane_a_integrator_ablation_qdot2_event.md`, `lane_a_sysid_parameter_replay.md`, `lane_a_damping_sweep.md`, `lane_a_damping_off_probe.md`, and native replay manifest dir `runs/diagnostics/native_strict_replay_provenance/` **if** native strict story must travel with Phase 2.

---

## 6. Phase 2 starting hypothesis

**With provisional A–D recorded (§8a)**, Phase 2 assumes:

- **Primary scientific and reporting target:** **contract C** smooth-dynamics parity (explicit cutoff, sample count, **`bridge_gravity_sign`** in prose and any future JSON).
- **Governance:** **`bridge_gravity_sign=mujoco` remains opt-in** in tooling until **contract C replication** on additional ICs/tasks and **explicit supervisor sign-off** for any default flip (**D** provisional).

Phase 2 work then branches into **(i)** replication on extra ICs/tasks under **C** (first scientific track: use **`.ai-cowork/`** Move Generator / Red Team process), **(ii)** optional dashboard/report annotation **after approval**, **(iii)** long-lead **B** only if required by thesis scope (**C** provisional: deferred).

---

## 7. Migration strategy

| Option | Pros | Cons | Risk | Recommended use |
|--------|------|------|------|------------------|
| **A. Git branch** (from a clean commit) | Full history; easy diff/PR; reversible | Does not shrink disk by itself; dirty tree still confusing until committed | Medium if branch cut from **dirty** or **untracked** state | **Default:** create **`phase2/...`** branch after committing or explicitly stashing what Phase 2 needs |
| **B. Fresh folder copy** | Mental clarity; can **exclude** heavy dirs via `rsync` filters | Two copies drift; easy to forget which is canonical | High if edits happen in **both** | **Optional** sibling checkout after **A** is pinned; good for “presentation clean” tree |
| **C. New repo initialized from curated copy** | Maximum isolation; smallest surface for collaborators | Loses easy `git blame` across full history unless subtree filter or mirror discipline | High (provenance fragmentation) | Only if policy requires separate artifact repo—**not** first choice here |

---

## 8. Recommended approach

**Create a new git branch from a deliberately chosen baseline commit** (after supervisor decisions and a **clean or documented** commit of `docs/research/`, curated `runs/diagnostics/...`, `.ai-cowork/`, and agreed tests/tools). **Then**, if a physically separate tree is still needed for focus, add a **git worktree** or **rsync-filtered sibling folder** from that branch tip—**not** before the branch story is clear.

---

## 8a. Provisional supervisor / user decisions (recorded)

**Status:** **provisional** user/supervisor alignment captured for Phase 2 readiness **without** implying all repo stakeholders have signed in person. **No** harness default was changed. **Contradiction check:** consistent with `LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md` §5a (C primary, A companion, D legacy, B deferred) and `LANE_A_DECISION_BOARD.md` claim rows **A11–A12**.

| ID | Topic | Provisional decision | Notes |
|----|--------|----------------------|--------|
| **A** | Accept **contract C** as **primary** smooth-dynamics Lane A metric | **YES (provisional)** | Explicit **time cutoff** and **sample count** remain mandatory in all claims |
| **B** | Treat **contract D** full-horizon XML-limited as **diagnostic-only** | **YES** | Do not narrate **D** `parity_ready_bridge_gate` as unconstrained ODE failure without caveat |
| **C** | Defer constrained parity **B** | **YES** | Analytical joint-limit/contact model is **later** explicit project |
| **D** | **`bridge_gravity_sign=mujoco`** default policy | **Opt-in for now** | **Review as possible default only after** contract **C** replication on **1–2** additional ICs/tasks **and** **supervisor sign-off** |

---

## 8b. Proposed Phase 2 git branch — **not created**

| Field | Value |
|-------|--------|
| **Branch name** | `phase-2-contract-c` (**user-approved** for Phase 2 baseline; branch **not** created yet) |
| **Parent branch** | `chore/agent-pack` (recorded at planning time) |
| **Parent `HEAD` (short)** | `cebb4477` (re-verify immediately before first `git checkout -b`) |
| **Purpose** | Phase 2 **clean development** from a **contract-C** reporting/scoring baseline: separate smooth unconstrained claims from mixed **D**, preserve Lane A evidence, proceed under provisional **A–D**. |
| **First Phase 2 scientific track** | Replicate **contract C** + **gravity-sign** (`mujoco`) result on **one or two** additional ICs/tasks using **`.ai-cowork/`** Move Generator / Red Team workflow (evidence packets + derived artifacts per existing Lane A hygiene). |

**Important:** Branch tip **must** be created only **after** user approves name, parent, and first-commit scope; **`git checkout -b`** has **not** been run for this plan.

---

## 8c. Proposed first `git add` / commit scope (pending approval)

| Category | Paths / pattern (illustrative) |
|----------|--------------------------------|
| **Include** | `docs/research/**` (Lane A + Phase 2 markdown); `.ai-cowork/`; `runs/diagnostics/evidence_packets/`; curated `runs/diagnostics/parity_*` dirs cited on Decision Board (prelimit gravity/metrics, joint limit ablation, etc.); `tests/test_*` and `tests/fixtures/diagnostics/` agreed for diagnostics; `tools/diagnostics/*.py` |
| **Exclude** | `**/__pycache__/**`, `*.pyc`, `.DS_Store`; `tools/gh*` archives and extracted trees; `assets/skill-zips/`; ad-hoc `codex/skills/*` drops not part of thesis repo policy; binary `Matlab_v2/swing_3d.mp4` unless explicitly wanted in git |
| **Needs user review** | **All** currently **modified tracked** files (`Matlab_v2/three_d/*`, `example_two_link/matlab_v2_dynamics.py`, `systematic_studies/swing_benchmark_mujoco_vs_bridge.py`, `systematic_studies/run_native_matlab_parity.py`, `docs/MUSCLE_HILL_PIPELINE.md`, etc.)—decide whether Phase 2 baseline commit is **docs+diagnostics only** or a **wider** snapshot; untracked `Matlab_v2/` additions; `tools/gh` symlink/binary; `runs/diagnostics/one_step_acceleration_probe/` and other probe dirs not on Decision Board evidence chain |

**Canonical outputs:** no commit should target `systematic_studies/outputs/*` dashboard JSON unless a **separate** approval explicitly covers canonical writes (not part of this branch-readiness step).

---

## 9. First command sequence after approval

**Do not run until §10 stop rules are satisfied.** Illustrative sequence (**branch name pinned to user proposal**; **parent** = recorded branch + `HEAD` at planning time):

```bash
cd /path/to/Mujoco
git status --porcelain
git fetch origin   # if using remotes
git checkout chore/agent-pack
git rev-parse --short HEAD   # expect cebb4477 at time of plan; verify before branch
# git pull --ff-only origin chore/agent-pack   # only if team policy requires
# --- First commit (example; paths MUST match §8c approval) ---
# git add docs/research .ai-cowork runs/diagnostics/evidence_packets \
#   runs/diagnostics/parity_prelimit_gravity_sign runs/diagnostics/parity_prelimit_metrics \
#   runs/diagnostics/parity_joint_limit_ablation tests tools/diagnostics
# git commit -m "Phase 2 baseline: Lane A research docs, curated diagnostics, ai-cowork"
git checkout -b phase-2-contract-c
# Optional: git push -u origin phase-2-contract-c
# Optional second working tree:
# git worktree add ../Mujoco-phase-2-contract-c phase-2-contract-c
```

Exact **`git add`** scope must match **§8c** and user approval. **Do not** run `git checkout -b` until approvals in **§10** are explicit.

---

## 10. Stop rules

Do **not** `git checkout -b`, fork, copy, or `git worktree add` until:

1. **`git status --porcelain`** has been **reviewed** with the user (large untracked sets: `docs/research/`, `runs/diagnostics/*`, `.ai-cowork/`, `tools/gh*`, skill zips, etc.—decide what **enters** the baseline commit vs stays out). **Latest snapshot (planning time):** parent branch **`chore/agent-pack`**, **`HEAD`** **`cebb4477`**; many `??` paths remain.
2. **Provisional A–D** are **recorded** in **§8a** and mirrored on **`LANE_A_DECISION_BOARD.md`**; **formal** supervisor sign-off is still required before treating **D** as “policy locked” or changing **defaults** in code.
3. **`LANE_A_DECISION_BOARD.md`** links to the **latest** Lane A docs (reporting note, supervisor summary, **this Phase 2 plan**—link present in repo header block).
4. The user **explicitly confirms**: **branch name** (`phase-2-contract-c` or edit), **parent branch/commit** (re-verify `HEAD` short SHA at click time), **first `git add` scope** (**§8c**), and whether decisions **A–D** are **accepted as governance** or **recorded as provisional-only** for planning.

---

## 11. Approval checklist (Mission Control)

Ask the user to reply with:

1. **Confirm** branch name **`phase-2-contract-c`** or supply a replacement.  
2. **Confirm** first-commit **`git add`** scope (**docs+diagnostics+ai-cowork+tests+tools** vs **include selected tracked code edits**).  
3. **Confirm** whether **A–D** are **binding** for the repo narrative or **provisional** until a live supervisor review—this plan **records** them as **provisional** unless the user elevates them in writing.

---

## 12. Phase 2 baseline staging plan (curated; **no** `git add` / commit / branch executed)

**Mission Control snapshot date:** 2026-05-11. **Policy:** first baseline is **curated**, not the whole dirty tree. **A–D:** **provisional Phase 2 working governance** pending live supervisor review (`§8a`). **Branch name:** **`phase-2-contract-c`** approved; **parent** **`chore/agent-pack`** @ **`cebb4477`**.

### 12.1 Approved branch metadata

| Field | Value |
|-------|--------|
| **Branch name** | `phase-2-contract-c` |
| **Parent branch** | `chore/agent-pack` |
| **Current `HEAD` (short, at staging plan time)** | `cebb4477` |

### 12.2 A–D governance status (provisional wording)

Working governance for Phase 2 planning and commits: **A** **contract C** primary smooth metric — **YES (provisional)**; **B** **contract D** diagnostic-only — **YES (provisional)**; **C** defer **B** — **YES (provisional)**; **D** **`bridge_gravity_sign=mujoco` remains opt-in** until replication + supervisor sign-off — **YES (provisional)**. Elevate to **binding** only after explicit supervisor sign-off recorded in markdown.

### 12.3 Proposed **include** list (by category)

**1. Research governance / docs (`docs/research/`)** — all seven current files:

- `docs/research/LANE_A_DECISION_BOARD.md`
- `docs/research/LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md`
- `docs/research/LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md`
- `docs/research/LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md`
- `docs/research/LANE_A_REPORTING_NOTE.md`
- `docs/research/LANE_A_SUPERVISOR_SUMMARY.md`
- `docs/research/PHASE_2_CLEAN_FORK_PLAN.md`

**2. `.ai-cowork/` blueprint** — entire tree (commands + templates + `README.md`).

**3. Evidence packets** — entire directory:

- `runs/diagnostics/evidence_packets/`

**4. Derived artifacts (curated `runs/diagnostics/` parity dirs)** — Lane A / Decision Board–adjacent probes:

- `runs/diagnostics/parity_500step_probe/`
- `runs/diagnostics/parity_com_inertia_probe/`
- `runs/diagnostics/parity_damping_ablation/`
- `runs/diagnostics/parity_damping_sweep/`
- `runs/diagnostics/parity_gravity_sign_probe/`
- `runs/diagnostics/parity_integrator_ablation/`
- `runs/diagnostics/parity_joint_limit_ablation/`
- `runs/diagnostics/parity_prelimit_gravity_sign/`
- `runs/diagnostics/parity_prelimit_metrics/`
- `runs/diagnostics/parity_prelimit_rmse_closure/`
- `runs/diagnostics/parity_sysid_replay/`
- `runs/diagnostics/native_strict_replay_provenance/`

**5. Diagnostics tests / fixtures / tools**

- `tests/test_artifact_contract_check.py`
- `tests/test_bridge_gravity_sign.py`
- `tests/test_diagnosis_stub.py`
- `tests/test_parity_lane_health.py`
- `tests/test_parity_schema_audit.py`
- `tests/test_reporting_lane_health.py`
- `tests/test_run_native_matlab_parity_provenance.py`
- `tests/test_swing_benchmark_mujoco_damping_scale.py`
- `tests/test_swing_benchmark_mujoco_integrator_override.py`
- `tests/test_swing_benchmark_mujoco_joint_limits_override.py`
- `tests/fixtures/diagnostics/artifact_contract/`
- `tests/fixtures/diagnostics/inventory_reports/`
- `tests/fixtures/diagnostics/parity_lane_health/`
- `tests/fixtures/diagnostics/parity_schema_audit/`
- `tests/fixtures/diagnostics/reporting_lane_health/`
- `tools/diagnostics/artifact_contract_check.py`
- `tools/diagnostics/diagnosis_stub.py`
- `tools/diagnostics/parity_lane_health.py`
- `tools/diagnostics/parity_schema_audit.py`
- `tools/diagnostics/reporting_lane_health.py`

**6. Required source-code support for derived probes (minimal Python; *default curated baseline*)**

- `example_two_link/matlab_v2_dynamics.py` — bridge dynamics / gravity-sign convention support for reproducible **C** probes.
- `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` — swing benchmark harness (flags such as `--bridge-gravity-sign`, joint-limit overrides) used to produce derived CSV/JSON.

**Optional “extended baseline” (needs explicit opt-in):** add `systematic_studies/run_native_matlab_parity.py` if you want native-replay provenance tooling in the **same** first commit; otherwise **exclude** to keep Phase 2 Lane A baseline **bridge-centric**.

### 12.4 Proposed **exclude** list (by reason)

| Reason | Paths / patterns |
|--------|-------------------|
| **Generated / cache** | `example_two_link/__pycache__/`, `systematic_studies/__pycache__/`, any `*.pyc` |
| **OS noise** | `.DS_Store` |
| **Large binary / media** | `Matlab_v2/swing_3d.mp4` |
| **Unrelated MATLAB 3-D workstream (untracked + modified)** | `Matlab_v2/main_3d_master.m`, `Matlab_v2/three_d/animate_swing_timeline_3d.m`, `Matlab_v2/three_d/ball/ball_machine_params_3d.m`, `Matlab_v2/three_d/export_hill_integration_slide.m`, `Matlab_v2/three_d/load_latest_3d_run.m`, `Matlab_v2/three_d/load_swing_jsonl.m`, `Matlab_v2/three_d/timeline_two_link_torque_proxy.m`, and **modified** `Matlab_v2/three_d/animate_swing_3d.m`, `default_params_3d.m`, `export/export_swing_video_3d.m`, `run_3d_forward_swing.m` |
| **Unrelated thesis pipeline doc** | `docs/MUSCLE_HILL_PIPELINE.md` (exclude from **Lane A Phase 2 baseline** unless you explicitly bundle thesis docs) |
| **Skill archives / installed skill trees** | `assets/skill-zips/`, `codex/skills/ai-systems-robustness-os/`, `codex/skills/outdoor-rig-engineer-os-updated/` |
| **Tooling binaries** | `tools/gh`, `tools/gh_2.54.0_macOS_arm64.tar.gz`, `tools/gh_2.54.0_macOS_arm64.zip`, `tools/gh_2.54.0_macOS_arm64/` |
| **Uncertain / not on Decision Board chain for minimal carry** | `runs/diagnostics/one_step_acceleration_probe/` — keep **out** of minimal baseline unless you add a Decision Board citation |

### 12.5 Source-code diff review (modified tracked files only)

| Path | Include in **default** curated baseline? | Why | Risk if mishandled | User review? |
|------|------------------------------------------|-----|----------------------|---------------|
| `example_two_link/matlab_v2_dynamics.py` | **Yes** (recommended) | Bridge-side dynamics used by probes; gravity-sign narrative | Wrong sign default could confuse thesis | **Yes** |
| `systematic_studies/swing_benchmark_mujoco_vs_bridge.py` | **Yes** (recommended) | Harness for derived passive runs / CLI flags | Large diff; touches benchmark semantics | **Yes** |
| `systematic_studies/run_native_matlab_parity.py` | **No** (default) | Native MATLAB lane; not required to reproduce **bridge contract C** artifacts | Blends native vs bridge governance if bundled casually | **Yes** (opt-in) |
| `Matlab_v2/three_d/animate_swing_3d.m` | **No** | 3-D visualization / unrelated Phase 2 baseline | Scope creep | **Yes** |
| `Matlab_v2/three_d/default_params_3d.m` | **No** | same | same | **Yes** |
| `Matlab_v2/three_d/export/export_swing_video_3d.m` | **No** | same | same | **Yes** |
| `Matlab_v2/three_d/run_3d_forward_swing.m` | **No** | same | same | **Yes** |
| `docs/MUSCLE_HILL_PIPELINE.md` | **No** | Muscle/Hill pipeline doc; not Lane A contract baseline | Mixes workstreams | **Yes** |
| `example_two_link/__pycache__/matlab_v2_dynamics.cpython-311.pyc` | **No** | Generated | Pollutes repo / wrong binary hygiene | **No** (never) |
| `systematic_studies/__pycache__/run_native_matlab_parity.cpython-311.pyc` | **No** | Generated | same | **No** (never) |
| `.DS_Store` | **No** | OS metadata | Noise | **No** (never) |

**Diff magnitude (tracked, excluding pyc):** `example_two_link/matlab_v2_dynamics.py` **31** lines touched; `swing_benchmark_mujoco_vs_bridge.py` **+143** / **−** lines; `run_native_matlab_parity.py` **+214** / large insertions; MATLAB + pipeline docs **+539** insertions total across eight non-pyc files (see `git diff --stat`).

### 12.6 Exact `git add` commands after approval (**explicit paths**; not `git add .`)

**Recommended workflow:** create branch **first**, then stage + commit on `phase-2-contract-c` so the baseline commit does not land on `chore/agent-pack` unless you intend that.

```bash
cd /path/to/Mujoco
git checkout chore/agent-pack
git rev-parse --short HEAD
git checkout -b phase-2-contract-c
git add \
  docs/research/LANE_A_DECISION_BOARD.md \
  docs/research/LANE_A_MODEL_CONTRACT_DECISION_BRIEF.md \
  docs/research/LANE_A_PRELIMIT_RMSE_CLOSURE_PLAN.md \
  docs/research/LANE_A_REPORTING_CONTRACT_UPDATE_PLAN.md \
  docs/research/LANE_A_REPORTING_NOTE.md \
  docs/research/LANE_A_SUPERVISOR_SUMMARY.md \
  docs/research/PHASE_2_CLEAN_FORK_PLAN.md \
  .ai-cowork/ \
  runs/diagnostics/evidence_packets/ \
  runs/diagnostics/parity_500step_probe/ \
  runs/diagnostics/parity_com_inertia_probe/ \
  runs/diagnostics/parity_damping_ablation/ \
  runs/diagnostics/parity_damping_sweep/ \
  runs/diagnostics/parity_gravity_sign_probe/ \
  runs/diagnostics/parity_integrator_ablation/ \
  runs/diagnostics/parity_joint_limit_ablation/ \
  runs/diagnostics/parity_prelimit_gravity_sign/ \
  runs/diagnostics/parity_prelimit_metrics/ \
  runs/diagnostics/parity_prelimit_rmse_closure/ \
  runs/diagnostics/parity_sysid_replay/ \
  runs/diagnostics/native_strict_replay_provenance/ \
  tests/test_artifact_contract_check.py \
  tests/test_bridge_gravity_sign.py \
  tests/test_diagnosis_stub.py \
  tests/test_parity_lane_health.py \
  tests/test_parity_schema_audit.py \
  tests/test_reporting_lane_health.py \
  tests/test_run_native_matlab_parity_provenance.py \
  tests/test_swing_benchmark_mujoco_damping_scale.py \
  tests/test_swing_benchmark_mujoco_integrator_override.py \
  tests/test_swing_benchmark_mujoco_joint_limits_override.py \
  tests/fixtures/diagnostics/artifact_contract/ \
  tests/fixtures/diagnostics/inventory_reports/ \
  tests/fixtures/diagnostics/parity_lane_health/ \
  tests/fixtures/diagnostics/parity_schema_audit/ \
  tests/fixtures/diagnostics/reporting_lane_health/ \
  tools/diagnostics/artifact_contract_check.py \
  tools/diagnostics/diagnosis_stub.py \
  tools/diagnostics/parity_lane_health.py \
  tools/diagnostics/parity_schema_audit.py \
  tools/diagnostics/reporting_lane_health.py \
  example_two_link/matlab_v2_dynamics.py \
  systematic_studies/swing_benchmark_mujoco_vs_bridge.py
# Optional second commit or amended add if user opts in:
# git add systematic_studies/run_native_matlab_parity.py
```

### 12.7 Exact `git commit` command after approval (message suggestion)

```bash
git commit -m "chore(phase-2): curated Lane A baseline (research, diagnostics, ai-cowork)

- Record provisional A–D governance and contract C/D/B framing in docs/research
- Add evidence packets + curated runs/diagnostics parity artifacts
- Add .ai-cowork blueprint; diagnostics tools/tests/fixtures
- Include bridge swing harness + matlab_v2_dynamics for reproducible derived probes
- Exclude Matlab_v2 3-D stream, native parity script (default), caches, gh tooling"
```

### 12.8 Branch / follow-up commands

**Preferred sequence:** `git checkout -b phase-2-contract-c` **before** `git add` / `git commit` (§12.6)—no separate branch command is needed **after** commit.

**After** the baseline commit (optional remote):

```bash
git push -u origin phase-2-contract-c
```

**Alternative (commit on parent first, not recommended for isolation):** after `git add` + `git commit` on `chore/agent-pack`, create/point the branch with `git branch phase-2-contract-c` or `git checkout -b phase-2-contract-c` at that commit.

### 12.9 Approval needed (staging-specific)

1. **Approve** §12.3 **include** list (add/remove parity dirs; include `one_step_acceleration_probe/` yes/no).  
2. **Approve** §12.4 **exclude** list (especially **MATLAB 3-D** and **`run_native_matlab_parity.py`** default exclusion).  
3. **Approve** §12.5 **source** files: confirm **`matlab_v2_dynamics.py`** + **`swing_benchmark_mujoco_vs_bridge.py`** only, or opt-in **`run_native_matlab_parity.py`**.  
4. **Choose workflow:** **(recommended)** branch **`phase-2-contract-c` first**, then stage + commit **on** that branch **vs** commit on **`chore/agent-pack`** then create branch pointer.
