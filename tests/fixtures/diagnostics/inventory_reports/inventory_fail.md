# Run/log inventory (read-only)

Generated: `2026-05-11T00:00Z` UTC
Repo root: `/Users/uljan/Desktop/Mujoco`

## Scan roots

- `tests/fixtures/diagnostics/sample_runs/run_fail`

## `tests/fixtures/diagnostics/sample_runs/run_fail`

- Files scanned: **1**
- Failure hits: **1**

### Failure hits (evidence excerpts)

- **File**: `tests/fixtures/diagnostics/sample_runs/run_fail/stderr.log`
  - **Matched**: `\\bTraceback\\b`
  - **Excerpt**:

```
Traceback (most recent call last):
  File \"systematic_studies/compare_signals.py\", line 123, in <module>
    raise RuntimeError(\"synthetic failure for fixture\")
RuntimeError: synthetic failure for fixture
```

## Summary

- Total files scanned: **1**
- Total failure hits: **1**

