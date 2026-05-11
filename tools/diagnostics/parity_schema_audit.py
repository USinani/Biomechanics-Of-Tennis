#!/usr/bin/env python3
"""
Lane A parity schema audit (stdlib only; read-only by default).

Inspects the strict and relaxed parity metrics JSON artifacts and reports:
- candidate gate fields (boolean-like evidence)
- candidate metric fields (numeric evidence)
- candidate threshold/tolerance fields (threshold evidence)

Rules:
- Never infer parity closure from numeric values alone.
- Only report pass/fail gate evidence when an explicit boolean field exists.
- If schema is unclear, report UNKNOWN.

Default: print Markdown to stdout.
Optional: write under runs/diagnostics/ with --write (guarded; refuses overwrite).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence


ArtifactStatus = Literal["present", "missing", "unreadable", "wrong_type"]
SchemaConfidence = Literal["explicit", "partial", "unknown"]
ValueType = Literal["bool", "number", "string", "null", "other"]


STRICT_PATH = "systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json"
RELAXED_PATH = "systematic_studies/outputs/compare_signals_bridge_relaxed_metrics.json"


KEYWORD_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pat, re.IGNORECASE)
    for pat in (
        r"parity",
        r"ready",
        r"gate",
        r"pass",
        r"fail",
        r"threshold",
        r"tolerance",
        r"rmse",
        r"max_abs",
        r"max_",
        r"error",
        r"\bok\b",
    )
)

THRESHOLD_HINTS = ("threshold", "tolerance", "tol", "limit", "max_", "min_")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


CODE_ROOT = _repo_root()


def _load_module(repo_root: Path, rel_path: str, module_name: str):
    path = repo_root / rel_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"could not load module {module_name} from {rel_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_write_guard():
    return _load_module(CODE_ROOT, "tools/diagnostics/run_log_inventory.py", "run_log_inventory")


def _load_artifact_checker():
    return _load_module(CODE_ROOT, "tools/diagnostics/artifact_contract_check.py", "artifact_contract_check")


def _value_type(v: Any) -> ValueType:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return "number"
    if isinstance(v, str):
        return "string"
    if v is None:
        return "null"
    return "other"


def _stringify_value(v: Any, max_len: int = 140) -> str:
    s = repr(v)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _path_str(path: Sequence[str | int]) -> str:
    # JSONPath-ish, but minimal: $.a.b[0].c
    out = "$"
    for p in path:
        if isinstance(p, int):
            out += f"[{p}]"
        else:
            # safe for display; keep raw key
            out += f".{p}"
    return out


@dataclass(frozen=True)
class KeyRecord:
    artifact: str
    key_path: str
    value_type: ValueType
    value: str
    interpretation: str


def iter_scalar_fields(obj: Any, *, max_list_items: int = 50) -> Iterable[tuple[list[str | int], Any]]:
    """
    Yield (path, scalar_value) pairs for scalars found recursively.
    Scalars: bool/number/string/null.
    """
    stack: list[tuple[list[str | int], Any]] = [([], obj)]
    while stack:
        path, cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if isinstance(k, str):
                    stack.append((path + [k], v))
        elif isinstance(cur, list):
            for idx, v in enumerate(cur[:max_list_items]):
                stack.append((path + [idx], v))
        else:
            t = _value_type(cur)
            if t in ("bool", "number", "string", "null"):
                yield path, cur


def _key_matches(path: list[str | int]) -> bool:
    # join only string segments
    s = ".".join([p for p in path if isinstance(p, str)])
    return any(p.search(s) for p in KEYWORD_PATTERNS)


def _is_threshold_like(path: list[str | int]) -> bool:
    s = ".".join([p.lower() for p in path if isinstance(p, str)])
    return any(h in s for h in THRESHOLD_HINTS)


def audit_json(artifact_name: str, data: Any) -> tuple[list[KeyRecord], list[KeyRecord], list[KeyRecord], SchemaConfidence]:
    """
    Returns (gate_records, metric_records, threshold_records, confidence).
    """
    gate: list[KeyRecord] = []
    metric: list[KeyRecord] = []
    threshold: list[KeyRecord] = []

    if not isinstance(data, dict):
        return gate, metric, threshold, "unknown"

    for path, value in iter_scalar_fields(data):
        if not _key_matches(path):
            continue
        vtype = _value_type(value)
        key_path = _path_str(path)

        if vtype == "bool":
            gate.append(
                KeyRecord(
                    artifact=artifact_name,
                    key_path=key_path,
                    value_type=vtype,
                    value=_stringify_value(value),
                    interpretation="explicit boolean gate evidence",
                )
            )
        elif vtype == "number":
            rec = KeyRecord(
                artifact=artifact_name,
                key_path=key_path,
                value_type=vtype,
                value=_stringify_value(value),
                interpretation="numeric metric evidence (not pass/fail without thresholds)",
            )
            if _is_threshold_like(path):
                threshold.append(
                    KeyRecord(
                        artifact=artifact_name,
                        key_path=key_path,
                        value_type=vtype,
                        value=_stringify_value(value),
                        interpretation="threshold/tolerance evidence",
                    )
                )
            else:
                metric.append(rec)
        elif vtype == "string":
            # Don't treat as gate; still can be informative.
            metric.append(
                KeyRecord(
                    artifact=artifact_name,
                    key_path=key_path,
                    value_type=vtype,
                    value=_stringify_value(value),
                    interpretation="string evidence (informational; not pass/fail)",
                )
            )
        else:
            # null/other ignored for now
            continue

    if gate:
        conf: SchemaConfidence = "explicit"
    elif metric or threshold:
        conf = "partial"
    else:
        conf = "unknown"

    return gate, metric, threshold, conf


def _artifact_status(repo_root: Path, rel_path: str) -> tuple[ArtifactStatus, str]:
    acc = _load_artifact_checker()
    r = acc.check_artifact(repo_root, rel_path)
    return r.status, r.evidence


def _read_json_object(repo_root: Path, rel_path: str) -> Any:
    p = repo_root / rel_path
    txt = p.read_text(encoding="utf-8", errors="replace")
    return json.loads(txt)


def render_report(
    strict_status: ArtifactStatus,
    relaxed_status: ArtifactStatus,
    strict_conf: SchemaConfidence,
    relaxed_conf: SchemaConfidence,
    gate_rows: list[KeyRecord],
    metric_rows: list[KeyRecord],
    thresh_rows: list[KeyRecord],
) -> str:
    lines: list[str] = [
        "# Lane A Parity Schema Audit",
        "",
        "## Summary",
        f"- strict artifact: {strict_status}",
        f"- relaxed artifact: {relaxed_status}",
        f"- strict schema confidence: {strict_conf}",
        f"- relaxed schema confidence: {relaxed_conf}",
        "",
        "## Candidate gate fields",
        "",
        "| Artifact | Key path | Value type | Value | Interpretation |",
        "|---|---|---|---|---|",
    ]
    if gate_rows:
        for r in gate_rows:
            lines.append(f"| {r.artifact} | `{r.key_path}` | {r.value_type} | `{r.value}` | {r.interpretation} |")
    else:
        lines.append("| (none) | (none) | (none) | (none) | UNKNOWN |")

    lines.extend(
        [
            "",
            "## Candidate metric fields",
            "",
            "| Artifact | Key path | Value type | Value |",
            "|---|---|---|---|",
        ]
    )
    if metric_rows:
        for r in metric_rows[:80]:
            lines.append(f"| {r.artifact} | `{r.key_path}` | {r.value_type} | `{r.value}` |")
        if len(metric_rows) > 80:
            lines.append(f"| … | … | … | … *(+{len(metric_rows) - 80} more)* |")
    else:
        lines.append("| (none) | (none) | (none) | (none) |")

    lines.extend(
        [
            "",
            "## Candidate threshold/tolerance fields",
            "",
            "| Artifact | Key path | Value type | Value |",
            "|---|---|---|---|",
        ]
    )
    if thresh_rows:
        for r in thresh_rows[:80]:
            lines.append(f"| {r.artifact} | `{r.key_path}` | {r.value_type} | `{r.value}` |")
        if len(thresh_rows) > 80:
            lines.append(f"| … | … | … | … *(+{len(thresh_rows) - 80} more)* |")
    else:
        lines.append("| (none) | (none) | (none) | (none) |")

    lines.extend(
        [
            "",
            "## Conservative interpretation",
            "- Explicit boolean gate fields may be reported as direct gate evidence.",
            "- Numeric metrics are evidence only, not pass/fail proof unless paired with explicit thresholds/tolerances.",
            "- Missing or unclear schema remains UNKNOWN.",
            "",
            "## Recommended update to parity_lane_health.py",
            "Suggest only (do not implement here):",
            "- Strict gate evidence: read explicit boolean fields discovered under strict artifact (if any).",
            "- Relaxed gate evidence: read explicit boolean fields discovered under relaxed artifact (if any).",
            "- Metrics: display the metric fields you care about (e.g. rmse, max_abs deviations) only if present.",
            "",
            "## Permission boundary",
            "Read-only schema audit. No metrics, outputs, thresholds, or experiment logic modified.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--write",
        type=str,
        default=None,
        help="Optional output path under runs/diagnostics/ (repo-relative). Default: stdout only.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = CODE_ROOT

    strict_status, _ = _artifact_status(repo_root, STRICT_PATH)
    relaxed_status, _ = _artifact_status(repo_root, RELAXED_PATH)

    gate_rows: list[KeyRecord] = []
    metric_rows: list[KeyRecord] = []
    thresh_rows: list[KeyRecord] = []
    strict_conf: SchemaConfidence = "unknown"
    relaxed_conf: SchemaConfidence = "unknown"

    if strict_status == "present":
        try:
            strict_data = _read_json_object(repo_root, STRICT_PATH)
            g, m, t, strict_conf = audit_json("strict", strict_data)
            gate_rows.extend(g)
            metric_rows.extend(m)
            thresh_rows.extend(t)
        except Exception:  # noqa: BLE001
            strict_conf = "unknown"

    if relaxed_status == "present":
        try:
            relaxed_data = _read_json_object(repo_root, RELAXED_PATH)
            g, m, t, relaxed_conf = audit_json("relaxed", relaxed_data)
            gate_rows.extend(g)
            metric_rows.extend(m)
            thresh_rows.extend(t)
        except Exception:  # noqa: BLE001
            relaxed_conf = "unknown"

    report = render_report(
        strict_status=strict_status,
        relaxed_status=relaxed_status,
        strict_conf=strict_conf,
        relaxed_conf=relaxed_conf,
        gate_rows=gate_rows,
        metric_rows=metric_rows,
        thresh_rows=thresh_rows,
    )

    if args.write:
        rli = _load_write_guard()
        try:
            target = rli._safe_write_target(repo_root, args.write)
        except (ValueError, FileExistsError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        target.write_text(report, encoding="utf-8")
        print(f"Wrote {target}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

