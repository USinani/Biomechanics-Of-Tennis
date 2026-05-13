# Claude project instructions (MuJoCo PhD workspace)

Use with Claude Projects / Desktop; complements repo `AGENTS.md` and Cursor rules.

## Mission control

- Single **mission** and **active hypothesis** at a time. Doctrine and rotation: **`.ai-cowork/mission-control.md`**, overview **`.ai-cowork/README.md`**.
- **One executor** per write scope; other agents read-only unless promoted. Roles: **`.ai-cowork/agent-roles.md`**.
- **Trajectory disagreement is downstream** — smallest local invariants before long-horizon RMSE or spike narratives.

## Lane A / Phase 2 governance

- **Decision board (branches, stop rules, next action):** `docs/research/LANE_A_DECISION_BOARD.md`
- **Supervisor review (options A–E, P2-M1):** `docs/research/PHASE_2_SUPERVISOR_REVIEW_UPDATE.md`
- Do not conflate **contract C** (pre-limit smooth window) with **contract D** (full-horizon diagnostic) or **relaxed** vs **strict** gates.

## Evidence

- Every quantitative claim: artifact path + command + **contract** label (strict / relaxed / diagnostic).
- Evidence packet shape: **`.ai-cowork/evidence-auditor.md`**, template **`.ai-cowork/evidence-packet-template.md`**.

## Permissions (default)

**Allowed without extra approval:** read/search repo; small docs under `docs/research/` or `runs/diagnostics/evidence_packets/` when aligned with active mission; non-destructive inspection commands.

**Requires explicit user approval:** writes to **`systematic_studies/outputs/`** and other canonical KPI JSON paths (see `docs/REPO_LAYOUT.md` and `AGENTS.md`); threshold or simulation/XML/code edits; **`git add` / `commit` / `push`**; deleting or overwriting research artifacts; staging **excluded dirty-tree** paths called out in Phase 2 planning docs.

## Red team

Before publication-facing claims, use **`.ai-cowork/red-team-critic.md`**.

## Project specifics

Authoritative repo rules: **`docs/PHD_DIRECTIONS.md`**, **`docs/REPO_LAYOUT.md`**, **`RUN.md`**, **`run.sh`**.
