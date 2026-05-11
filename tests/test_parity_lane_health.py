"""Stdlib unittests for tools/diagnostics/parity_lane_health.py (no pytest required)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    path = REPO_ROOT / "tools/diagnostics/parity_lane_health.py"
    spec = importlib.util.spec_from_file_location("parity_lane_health", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_plh = _load_module()


class TestParityLaneHealth(unittest.TestCase):
    def test_missing_artifacts_yields_warning(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_missing"
        # No files exist under this root; check_artifact should report missing.
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        relaxed = _plh.check_parity_artifact(fixture_root, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        overall = _plh.compute_overall(strict, relaxed, smoke=None, wrapper_error=False)
        self.assertEqual(overall, "warning")

    def test_present_artifacts_parse_known_fields(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_ok"
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        relaxed = _plh.check_parity_artifact(fixture_root, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        self.assertEqual(strict.status, "present")
        self.assertIn("rmse_q", strict.parsed_fields)
        self.assertEqual(strict.parity_evidence, "no")  # parity_ready false in fixture
        self.assertEqual(relaxed.parity_evidence, "yes")
        overall = _plh.compute_overall(strict, relaxed, smoke=None, wrapper_error=False)
        self.assertEqual(overall, "ok")

    def test_unknown_schema_yields_unknown_overall(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_unknown_schema"
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        relaxed = _plh.check_parity_artifact(fixture_root, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        self.assertEqual(strict.status, "present")
        overall = _plh.compute_overall(strict, relaxed, smoke=None, wrapper_error=False)
        self.assertEqual(overall, "unknown")

    def test_write_guard_rejects_unsafe_paths(self) -> None:
        rli = _plh._load_write_guard(REPO_ROOT)
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "/tmp/x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/diagnostics/../x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/not_diagnostics/x.md")

    def test_smoke_skipped_is_neutral(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_ok"
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        relaxed = _plh.check_parity_artifact(fixture_root, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        overall = _plh.compute_overall(strict, relaxed, smoke=None, wrapper_error=False)
        self.assertEqual(overall, "ok")

    def test_strict_and_relaxed_true_report_yes(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_yes"
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        relaxed = _plh.check_parity_artifact(fixture_root, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        self.assertEqual(strict.parity_evidence, "yes")
        self.assertEqual(relaxed.parity_evidence, "yes")

    def test_missing_or_nonboolean_reports_unknown(self) -> None:
        fixture_root = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_missing_boolean"
        strict = _plh.check_parity_artifact(fixture_root, "strict", _plh.STRICT_PATH, ["parity_ready"])
        self.assertEqual(strict.parity_evidence, "unknown")

        fixture_root2 = REPO_ROOT / "tests/fixtures/diagnostics/parity_lane_health/root_nonboolean"
        relaxed = _plh.check_parity_artifact(fixture_root2, "relaxed", _plh.RELAXED_PATH, ["parity_ready"])
        self.assertEqual(relaxed.parity_evidence, "unknown")


if __name__ == "__main__":
    unittest.main()

