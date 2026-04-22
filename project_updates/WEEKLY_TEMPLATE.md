# Weekly Update Template

Copy the block below into the top of
[weekly_updates.md](weekly_updates.md) every Monday. Keep the newest
week at the top; never rewrite an older week in place (prefer carrying
items forward into the new week's `Carried from past weeks` list).

ISO week convention: use `YYYY-Www` (e.g. `2026-W17`). For the week
ending date, use the following Sunday in `YYYY-MM-DD`.

Checkbox conventions:

- `- [x]` means done; include a completion date, e.g. `(completed 2026-04-22)`.
- `- [ ]` means pending; include an explicit target date, e.g. `(target 2026-04-29)` and an owner in square brackets, e.g. `[PI]`.
- Items that cross week boundaries get a `(carried since YYYY-Www)` suffix in the `Carried` subsection.

Optional tags in square brackets (use at end of line, before the owner):

- `[parity]` - MATLAB-vs-MuJoCo parity workstream.
- `[viz]` - systematic-studies visualisation / figures.
- `[rl]` - SAC training / eval.
- `[repo]` - repo structure, tooling, docs.
- `[phd]` - research-grade direction from [docs/PHD_DIRECTIONS.md](../docs/PHD_DIRECTIONS.md).

---

## Week YYYY-Www (ending YYYY-MM-DD)

### Done this week

- [x] <deliverable 1> (completed YYYY-MM-DD) [tag] [owner]
- [x] <deliverable 2> (completed YYYY-MM-DD) [tag] [owner]

### Next week

- [ ] <planned item 1> (target YYYY-MM-DD) [tag] [owner]
- [ ] <planned item 2> (target YYYY-MM-DD) [tag] [owner]

### Carried from past weeks

- [ ] <item still pending> (carried since YYYY-Www) (target YYYY-MM-DD) [tag] [owner]

### Notes

- Link to the supporting project update, e.g. [2026-04-22_project_consolidation_and_racket_viz.md](2026-04-22_project_consolidation_and_racket_viz.md).
- Call out any new blockers or parity-gate deltas explicitly.
