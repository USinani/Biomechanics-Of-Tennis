"""Stdlib unittests for tools/diagnostics/artifact_contract_check.py (no pytest required)."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    path = REPO_ROOT / "tools/diagnostics/artifact_contract_check.py"
    spec = importlib.util.spec_from_file_location("artifact_contract_check", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_acc = _load_module()


class TestArtifactContractCheck(unittest.TestCase):
    def test_missing_file_is_missing(self) -> None:
        tmp_root = REPO_ROOT / "tests/fixtures/diagnostics/artifact_contract/root"
        res = _acc.check_artifact(tmp_root, "systematic_studies/outputs/does_not_exist.json")
        self.assertEqual(res.status, "missing")

    def test_present_file_is_present(self) -> None:
        tmp_root = REPO_ROOT / "tests/fixtures/diagnostics/artifact_contract/root"
        res = _acc.check_artifact(
            tmp_root, "systematic_studies/outputs/compare_signals_matlab_vs_mujoco_metrics.json"
        )
        self.assertEqual(res.status, "present")

    def test_wrong_type_directory(self) -> None:
        tmp_root = REPO_ROOT / "tests/fixtures/diagnostics/artifact_contract/root"
        d = tmp_root / "example_two_link/metrics/eval_sac_two_link_arm.json"
        d.mkdir(parents=True, exist_ok=True)
        try:
            res = _acc.check_artifact(tmp_root, "example_two_link/metrics/eval_sac_two_link_arm.json")
            self.assertEqual(res.status, "wrong_type")
        finally:
            # Remove created dir if empty.
            try:
                d.rmdir()
            except OSError:
                pass

    def test_unreadable_file(self) -> None:
        tmp_root = REPO_ROOT / "tests/fixtures/diagnostics/artifact_contract/root"
        p = tmp_root / "systematic_studies/outputs/unreadable.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
        old_mode = p.stat().st_mode
        try:
            os.chmod(p, 0)
            res = _acc.check_artifact(tmp_root, "systematic_studies/outputs/unreadable.json")
            # On some systems the owner may still be able to read; accept present or unreadable.
            self.assertIn(res.status, ("present", "unreadable"))
        finally:
            os.chmod(p, old_mode)
            p.unlink(missing_ok=True)

    def test_write_guard_rejects_unsafe_paths(self) -> None:
        rli = _acc._load_run_log_inventory_module(REPO_ROOT)
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "/tmp/x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/diagnostics/../x.md")
        with self.assertRaises(ValueError):
            rli._safe_write_target(REPO_ROOT, "runs/not_diagnostics/x.md")

    def test_refuses_overwrite_existing_file(self) -> None:
        rli = _acc._load_run_log_inventory_module(REPO_ROOT)
        diag_dir = REPO_ROOT / "runs/diagnostics"
        diag_dir.mkdir(parents=True, exist_ok=True)
        target = diag_dir / "tmp_existing_contract_check.md"
        target.write_text("x", encoding="utf-8")
        try:
            with self.assertRaises(FileExistsError):
                rli._safe_write_target(REPO_ROOT, "runs/diagnostics/tmp_existing_contract_check.md")
        finally:
            target.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

