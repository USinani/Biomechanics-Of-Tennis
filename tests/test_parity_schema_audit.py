"""Stdlib unittests for tools/diagnostics/parity_schema_audit.py (no pytest required)."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    path = REPO_ROOT / "tools/diagnostics/parity_schema_audit.py"
    spec = importlib.util.spec_from_file_location("parity_schema_audit", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_psa = _load_module()


class TestParitySchemaAudit(unittest.TestCase):
    def test_audit_json_detects_gate_metric_threshold(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_schema_audit/root_ok"
        strict_path = fixture_root / _psa.STRICT_PATH
        relaxed_path = fixture_root / _psa.RELAXED_PATH

        strict = json.loads(strict_path.read_text(encoding="utf-8"))
        relaxed = json.loads(relaxed_path.read_text(encoding="utf-8"))

        g1, m1, t1, c1 = _psa.audit_json("strict", strict)
        self.assertEqual(c1, "explicit")  # parity_ready boolean present
        self.assertTrue(any(r.key_path.endswith(".parity_ready") for r in g1))
        self.assertTrue(any("rmse" in r.key_path.lower() for r in m1))
        self.assertTrue(any("threshold" in r.key_path.lower() for r in t1))

        g2, m2, t2, c2 = _psa.audit_json("relaxed", relaxed)
        self.assertEqual(c2, "explicit")
        self.assertTrue(any(r.key_path.endswith(".parity_ready") for r in g2))
        self.assertTrue(any("rmse" in r.key_path.lower() for r in m2))
        self.assertTrue(any("threshold" in r.key_path.lower() for r in t2))

    def test_audit_json_unknown_schema(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_schema_audit/root_unknown"
        strict_path = fixture_root / _psa.STRICT_PATH
        strict = json.loads(strict_path.read_text(encoding="utf-8"))
        g, m, t, c = _psa.audit_json("strict", strict)
        self.assertEqual(c, "unknown")
        self.assertEqual(g, [])

    def test_write_guard_rejects_unsafe_paths(self) -> None:
        rli = _psa._load_write_guard()
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "/tmp/x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/diagnostics/../x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/not_diagnostics/x.md")


if __name__ == "__main__":
    unittest.main()

