import json
import tempfile
import unittest
from pathlib import Path


class TestRunNativeMatlabParityProvenance(unittest.TestCase):
    def test_sha256_helper_stable(self) -> None:
        from systematic_studies.run_native_matlab_parity import sha256_file

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text("abc")
            h1 = sha256_file(p)
            h2 = sha256_file(p)
            self.assertEqual(h1, h2)
            # Known sha256 for "abc"
            self.assertEqual(
                h1,
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_prepare_diagnostics_dir_copies_and_writes_manifest(self) -> None:
        from systematic_studies.run_native_matlab_parity import prepare_diagnostics_dir, sha256_file

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_root = root / "repo"
            repo_root.mkdir()
            # Make it look like a git repo is optional; git status may fail.
            diag = root / "diag"
            csv_in = root / "bench.csv"
            csv_in.write_text("time_s,mujoco_qdot2_rad_s\n0.0,0.0\n")

            manifest = prepare_diagnostics_dir(
                diag, csv_in, argv=["run_native_matlab_parity.py", "--benchmark-csv", str(csv_in)], repo_root=repo_root
            )
            copied = diag / f"input_{csv_in.name}"
            self.assertTrue(copied.exists())
            self.assertEqual(sha256_file(csv_in), sha256_file(copied))

            mpath = diag / "native_matlab_parity_manifest.json"
            self.assertTrue(mpath.exists())
            loaded = json.loads(mpath.read_text())
            self.assertEqual(loaded["benchmark_csv_original_path"], str(csv_in))
            self.assertEqual(loaded["benchmark_csv_copied_path"], str(copied))
            self.assertIn("benchmark_csv_sha256_original", loaded)
            self.assertIn("argv", loaded)

    def test_default_paths_unchanged_when_out_args_absent(self) -> None:
        from systematic_studies.run_native_matlab_parity import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.diagnostics_dir)
        self.assertIsNone(args.out_json)
        self.assertIsNone(args.out_figure)

    def test_build_compare_cmd_plumbs_out_paths(self) -> None:
        from systematic_studies.run_native_matlab_parity import build_compare_cmd

        parity_csv = Path("/tmp/parity_timeseries.csv")
        compare_script = Path("/tmp/compare_signals.py")
        out_fig = Path("/tmp/out.png")
        out_json = Path("/tmp/out.json")
        cmd = build_compare_cmd(
            parity_csv=parity_csv,
            compare_script=compare_script,
            out_figure=out_fig,
            out_json=out_json,
        )
        self.assertIn(str(parity_csv), cmd)
        self.assertIn(str(out_fig), cmd)
        self.assertIn(str(out_json), cmd)

    def test_capture_matlab_logs_writes_files(self) -> None:
        from systematic_studies.run_native_matlab_parity import capture_matlab_logs

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            out_p, err_p = capture_matlab_logs(
                d,
                stdout="hello out\n",
                stderr="hello err\n",
                returncode=7,
            )
            self.assertTrue(out_p.exists())
            self.assertTrue(err_p.exists())
            self.assertEqual(out_p.read_text(), "hello out\n")
            self.assertEqual(err_p.read_text(), "hello err\n")
            rc_p = d / "matlab_returncode.txt"
            self.assertTrue(rc_p.exists())
            self.assertEqual(rc_p.read_text().strip(), "7")


if __name__ == "__main__":
    unittest.main()

