"""Stdlib unittests for tools/diagnostics/diagnosis_stub.py (no pytest required)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    path = REPO_ROOT / "tools/diagnostics/diagnosis_stub.py"
    spec = importlib.util.spec_from_file_location("diagnosis_stub", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_ds = _load_module()


class TestDiagnosisStub(unittest.TestCase):
    def test_fail_inventory_yields_failed_status_and_cited_evidence(self) -> None:
        md = (REPO_ROOT / "tests/fixtures/diagnostics/inventory_reports/inventory_fail.md").read_text(
            encoding="utf-8"
        )
        roots, evidence = _ds.parse_inventory_markdown(md)
        self.assertEqual(roots, ["tests/fixtures/diagnostics/sample_runs/run_fail"])
        self.assertEqual(len(evidence), 1)
        out = _ds.render_stub(roots, evidence)
        self.assertIn("\nfailed\n", out)
        self.assertIn("tests/fixtures/diagnostics/sample_runs/run_fail/stderr.log", out)
        self.assertIn("Traceback", out)
        self.assertIn("\npython_exception\n", out)

    def test_ok_inventory_yields_no_failure_detected(self) -> None:
        md = (REPO_ROOT / "tests/fixtures/diagnostics/inventory_reports/inventory_ok.md").read_text(encoding="utf-8")
        roots, evidence = _ds.parse_inventory_markdown(md)
        out = _ds.render_stub(roots, evidence)
        self.assertIn("\nno-failure-detected\n", out)
        self.assertIn("\nunknown\n", out)  # classification should remain conservative

    def test_write_guard_rejects_unsafe_paths(self) -> None:
        rli = _ds._load_run_log_inventory_module(REPO_ROOT)
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "/tmp/x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/diagnostics/../x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/not_diagnostics/x.md")

    def test_refuses_overwrite_existing_file(self) -> None:
        rli = _ds._load_run_log_inventory_module(REPO_ROOT)
        diag_dir = REPO_ROOT / "runs/diagnostics"
        diag_dir.mkdir(parents=True, exist_ok=True)
        target = diag_dir / "tmp_existing_diagnosis_stub.md"
        target.write_text("x", encoding="utf-8")
        try:
            with self.assertRaises(FileExistsError):
                rli._safe_write_target(REPO_ROOT, "runs/diagnostics/tmp_existing_diagnosis_stub.md")
        finally:
            target.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

