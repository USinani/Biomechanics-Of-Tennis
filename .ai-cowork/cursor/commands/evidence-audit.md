# Cursor command: Evidence audit

Use before accepting quantitative or parity claims.

## Prompt body

```text
Evidence audit (read `.ai-cowork/evidence-auditor.md`):

For artifact(s): {{PATHS}}
1. Question / hypothesis stated?
2. Inputs + method + outputs listed with paths?
3. Strict vs relaxed gates named if applicable?
4. Limitations + single next action?

Verdict: adopt | adopt with label | reject — one paragraph.
```
