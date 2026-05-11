# Codex Agent Instructions

Scope: this whole repository is Uljan's PhD MuJoCo plus MATLAB research workspace.

## Mission control (`.ai-cowork/`, Phase 2)

- **Doctrine:** `.ai-cowork/README.md`, `.ai-cowork/mission-control.md` — one mission, one active hypothesis, one executor; parallel agents default **read-only** (`.ai-cowork/agent-roles.md`).
- **Lane A board + stop rules + permissions:** `docs/research/LANE_A_DECISION_BOARD.md`
- **Supervisor review (P2-M1, options A–E):** `docs/research/PHASE_2_SUPERVISOR_REVIEW_UPDATE.md`
- **Handoff packet** for cross-agent work — include mission, hypothesis, artifacts, failures, **single** next action; align with `.ai-cowork/codex/AGENTS.template.md`.
- **Artifact governance:** do not write canonical `systematic_studies/outputs/` (and related KPI paths below) without approval; prefer `runs/diagnostics/...` for approved probes; do not `git add`/`commit`/`push` unless separately approved; do not normalize **excluded dirty-tree** paths per Phase 2 planning docs without explicit scope.
- **Cursor rules:** `.cursor/rules/010-mission-control.mdc` through `040-phase2-lane-a.mdc` layer Mission Control on existing project rules — follow both.

## Project Operating Rules

Start from the research decision, not the immediate edit. Before changing files on serious tasks, identify what the user is trying to decide, prove, compare, implement, or publish.

Authoritative context:

- `docs/PHD_DIRECTIONS.md` for thesis direction and methodological risks.
- `docs/REPO_LAYOUT.md` for repository layout, work lanes, dashboard paths, and validation commands.
- `RUN.md` and `run.sh` for executable entrypoints.
- `EXPERIMENT_PARADIGM.md` for experiment acceptance gates.
- `prompts/phd_mastermind.md` for multi-role research handoffs.

## Codex Skill Map

Project-local Codex skills live in `codex/skills/`:

- `$phd-research-os`: always consider for this repo's MuJoCo/MATLAB/SAC/parity/thesis work.
- `$judgment-question-engine-os`: use for vague prompts, question briefs, decision bases, and safer AI task framing.
- `$judgment-infrastructure-os`: use for permission packets, red-team reviews, AI output review, approval, and sign-off status.
- `$phd-research-writing-evidence`: use for thesis text, literature reviews, citation discipline, project updates, and paper framing.
- `$research-experiments-code-data`: use for research code, notebooks, datasets, metrics, figures, and reproducible experiment plans.
- `$research-agent-permission-boundaries`: use for autonomy limits, destructive actions, external services, and multi-file agent tasks.

If a skill is not auto-discovered by the runtime, read its `SKILL.md` from `codex/skills/<skill-name>/SKILL.md` when it matches the task.

## Evidence Discipline

- Every quantitative claim must tie to artifacts: JSON/CSV path, command, seeds/parameters, and commit when relevant.
- Say `pending` or `unknown` rather than filling missing metric cells.
- Do not fabricate citations, paper details, experiment results, dates, metrics, quotations, or benchmark claims.
- Do not treat AI-generated output as evidence unless checked against files, sources, or executable results.

## MuJoCo / MATLAB Nuance

- Most automated comparisons use the Python bridge (`example_two_link/matlab_v2_dynamics.py`), not necessarily native MATLAB.
- Summaries must name `bridge`, `native MATLAB`, `both`, or `n/a`.
- Strict and relaxed parity gates are distinct. Relaxed parity may support iteration, but publication framing must not rest on relaxed metrics alone.

## Validation Defaults

- After dynamics, parameter, parity, or `systematic_studies` parity edits: prefer `scripts/parity_smoke.sh`.
- For fuller ablations or pre-meeting evidence: consider `scripts/parity_full.sh`.
- For dashboard/reporting changes: run `./run.sh systematic_studies/weekly_dashboard.py --no-open`.
- For viewer work: route through `./run.sh` so macOS `mjpython` handling is preserved.

## Dashboard Contract

Do not rename these paths without paired edits to `systematic_studies/weekly_dashboard.py`:

- `systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json`
- `systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json`
- `systematic_studies/outputs/swing_benchmark_summary.json`
- `systematic_studies/outputs/racket_trajectory_summary.json`
- `example_two_link/metrics/eval_sac_two_link_arm.json`

## Permission Boundaries

Allowed without extra confirmation: read/search files, create small requested notes/docs/scripts/tests, run non-destructive inspection/test/format commands, and make reviewable implementation edits.

Requires explicit user approval: deleting files or folders, overwriting raw data or thesis drafts, installing major dependencies, uploading/calling external services, changing git history, force-pushing, modifying remotes, or publishing/submitting research material.

End serious recommendations with one permission status: `Allowed`, `Allowed with conditions`, `Needs review`, `Not allowed`, or `Insufficient evidence`.
