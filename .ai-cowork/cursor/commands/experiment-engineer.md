# Cursor command: Experiment engineer

Use before approving a run, benchmark, or A/B change.

## Prompt body

```text
Experiment gate (read `.ai-cowork/experiment-engineer.md`):

Proposed move: {{DESCRIPTION}}
1. Which Decision Board row or hypothesis does this falsify or support?
2. Can a read-only recomputation answer the same question? (Y/N)
3. Output paths: canonical (Y/N) vs derived (list).
4. If proceed: evidence packet filename + stop condition.

Reject if the experiment cannot change a decision.
```
