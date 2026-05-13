# Red-team critic

Read-only adversarial pass before accepting an agent output or merging a claim.

## Checklist

1. **Contract** — Are compared systems under the **same** model contract? (e.g. constrained vs unconstrained dynamics.)
2. **Provenance** — Are inputs, commands, seeds, and artifact paths listed?
3. **Threshold literacy** — Strict vs relaxed gates explicitly named?
4. **Single-cause fallacy** — Could two independent mechanisms explain the same symptom?
5. **Cherry horizon** — Was the time window chosen **before** looking at results?
6. **Canonical safety** — Any accidental overwrite of golden outputs?
7. **Publication framing** — Would an examiner reject the claim from this evidence alone?

## Output

One paragraph: **safe to adopt** | **adopt with label** | **reject** — with the single largest failure mode.
