#!/usr/bin/env python3
"""
Diagnosis stub generator (dry-run by default).

Consumes a run/log inventory markdown report (from tools/diagnostics/run_log_inventory.py)
and emits a structured diagnosis *template* with evidence citations.

Hard guarantees:
- stdout-only by default.
- Optional --write is allowed only under runs/diagnostics/ and uses the same strict
  guard as run_log_inventory.py (absolute paths, traversal, symlink escape rejected).
- Refuses to overwrite existing files.
- Does not propose code changes. Does not modify canonical outputs.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal


Status = Literal["failed", "no-failure-detected", "unknown"]
Classification = Literal[
    "python_exception",
    "matlab_error",
    "mujoco_or_mjpython_error",
    "missing_expected_artifact",
    "corrupt_or_partial_output",
    "numerical_issue_nan_inf",
    "unknown",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_run_log_inventory_module(repo_root: Path):
    """
    Load tools/diagnostics/run_log_inventory.py as a module without requiring tools/ to be a package.
    We do this so the write-guard behavior is exactly shared.
    """
    path = repo_root / "tools/diagnostics/run_log_inventory.py"
    spec = importlib.util.spec_from_file_location("run_log_inventory", path)
    if not spec or not spec.loader:
        raise RuntimeError("could not load run_log_inventory.py")
    mod = importlib.util.module_from_spec(spec)
    # Ensure dataclasses inside run_log_inventory can resolve module name.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass(frozen=True)
class EvidenceItem:
    file_path: str
    matched: str | None
    excerpt: str


FILE_RE = re.compile(r"^- \*\*File\*\*: `([^`]+)`\s*$")
MATCHED_RE = re.compile(r"^\s*- \*\*Matched\*\*: `([^`]+)`\s*$")


def parse_inventory_markdown(md: str) -> tuple[list[str], list[EvidenceItem]]:
    """
    Parse the subset of markdown emitted by run_log_inventory.py needed for evidence citations.

    Returns:
      - roots listed under "## Scan roots" (best-effort)
      - evidence items (file + matched pattern + excerpt)
    """
    roots: list[str] = []
    evidence: list[EvidenceItem] = []

    lines = md.splitlines()
    i = 0
    in_roots = False
    while i < len(lines):
        line = lines[i]
        if line.strip() == "## Scan roots":
            in_roots = True
            i += 1
            continue
        if in_roots:
            if line.startswith("## "):
                in_roots = False
            else:
                m = re.match(r"^- `([^`]+)`\s*$", line.strip())
                if m:
                    roots.append(m.group(1))
                i += 1
                continue

        m_file = FILE_RE.match(line)
        if not m_file:
            i += 1
            continue

        file_path = m_file.group(1)
        matched: str | None = None
        excerpt: str = ""

        # Look ahead for matched and excerpt fenced block.
        j = i + 1
        while j < len(lines) and not lines[j].startswith("- **File**:"):
            m_matched = MATCHED_RE.match(lines[j])
            if m_matched:
                matched = m_matched.group(1)
            if lines[j].strip() == "```":
                k = j + 1
                buf: list[str] = []
                while k < len(lines) and lines[k].strip() != "```":
                    buf.append(lines[k])
                    k += 1
                excerpt = "\n".join(buf).strip("\n")
                j = k + 1
                break
            j += 1

        evidence.append(EvidenceItem(file_path=file_path, matched=matched, excerpt=excerpt))
        i = j

    return roots, evidence


def classify_from_evidence(evidence: list[EvidenceItem]) -> Classification:
    text = "\n".join([e.excerpt for e in evidence if e.excerpt])
    text_l = text.lower()
    if "traceback" in text_l:
        return "python_exception"
    if "matlab" in text_l and ("license" in text_l or "toolbox" in text_l or "undefined function" in text_l):
        return "matlab_error"
    if "mjpython" in text_l or "mujoco" in text_l and ("glfw" in text_l or "glcontext" in text_l):
        return "mujoco_or_mjpython_error"
    if "filenotfounderror" in text_l or "no such file" in text_l:
        return "missing_expected_artifact"
    if "jsondecodeerror" in text_l or "unexpected end of json" in text_l or "truncated" in text_l:
        return "corrupt_or_partial_output"
    if "nan" in text_l or "inf" in text_l:
        return "numerical_issue_nan_inf"
    return "unknown"


def status_from_evidence(evidence: list[EvidenceItem]) -> Status:
    if not evidence:
        return "no-failure-detected"
    # If we have evidence records but empty excerpts, treat as unknown signal quality.
    if any(e.excerpt for e in evidence):
        return "failed"
    return "unknown"


def render_stub(roots: list[str], evidence: list[EvidenceItem]) -> str:
    inspected = roots[0] if len(roots) == 1 else ("; ".join(roots) if roots else "UNKNOWN")
    status = status_from_evidence(evidence)
    classification = classify_from_evidence(evidence) if status == "failed" else "unknown"

    lines: list[str] = [
        "# Diagnosis Stub",
        "",
        "## Run / root inspected",
        inspected,
        "",
        "## Status",
        status,
        "",
        "## Evidence",
    ]

    if evidence:
        for e in evidence[:10]:
            # Evidence citations must be anchored to inventory records.
            fp = e.file_path or "UNKNOWN"
            excerpt = (e.excerpt or "UNKNOWN").strip()
            lines.append(f"- `{fp}` excerpt:")
            lines.append("")
            lines.append("```")
            lines.append(excerpt)
            lines.append("```")
    else:
        lines.append("- UNKNOWN — no evidence items found in inventory report.")

    lines.extend(
        [
            "",
            "## Preliminary classification",
            classification,
            "",
            "## Ranked hypotheses",
            "1. UNKNOWN — evidence needed:",
            "2. UNKNOWN — evidence needed:",
            "3. UNKNOWN — evidence needed:",
            "",
            "## Smallest safe next action",
            "- Read-only: open the cited evidence file(s) and capture additional surrounding context (±50 lines).",
            "- Human-approved: if a rerun is needed, start with the smallest existing smoke command (no long runs).",
            "",
            "## Permission boundary",
            "No code changes proposed. No experiment outputs modified.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory_report", type=str, help="Path to an inventory markdown report to consume.")
    p.add_argument(
        "--write",
        type=str,
        default=None,
        help="Optional output path under runs/diagnostics/ (repo-relative). Default: stdout only.",
    )
    return p.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = _repo_root()

    report_path = Path(args.inventory_report)
    if not report_path.is_absolute():
        report_path = (repo_root / report_path)
    if not report_path.exists():
        print(f"error: inventory report not found: {report_path}", file=sys.stderr)
        return 2

    md = report_path.read_text(encoding="utf-8", errors="replace")
    roots, evidence = parse_inventory_markdown(md)
    stub = render_stub(roots, evidence)

    if args.write:
        rli = _load_run_log_inventory_module(repo_root)
        try:
            target = rli._safe_write_target(repo_root, args.write)
        except (ValueError, FileExistsError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        target.write_text(stub, encoding="utf-8")
        print(f"Wrote {target}")
    else:
        print(stub)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

