#!/usr/bin/env python3
"""Run timing sweep only when parity gate has passed."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate timing-sweep analysis on parity readiness.")
    parser.add_argument(
        "--gate-json",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs" / "compare_signals_metrics.json",
        help="JSON produced by compare_signals.py containing parity_ready flag.",
    )
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=ROOT / "systematic_studies" / "outputs",
    )
    parser.add_argument("--skip-pronation", action="store_true")
    parser.add_argument("--double-steps", type=int, default=800)
    parser.add_argument("--pronation-steps", type=int, default=600)
    args = parser.parse_args()

    if not args.gate_json.exists():
        raise FileNotFoundError(
            f"Parity gate JSON not found: {args.gate_json}. Run compare_signals.py first."
        )
    with args.gate_json.open("r") as f:
        gate = json.load(f)
    if not gate.get("parity_ready", False):
        raise SystemExit(
            "Parity gate failed (parity_ready=false). Aborting timing sweep to protect analysis quality."
        )

    _run(
        [
            sys.executable,
            str(ROOT / "systematic_studies" / "double_pendulum_sweep.py"),
            "--steps",
            str(args.double_steps),
            "--out",
            str(args.outputs_dir / "double_pendulum_sweep.csv"),
        ]
    )
    if not args.skip_pronation:
        _run(
            [
                sys.executable,
                str(ROOT / "systematic_studies" / "pronation_supination_sweep.py"),
                "--steps",
                str(args.pronation_steps),
                "--out",
                str(args.outputs_dir / "pronation_supination_sweep.csv"),
            ]
        )
    _run(
        [
            sys.executable,
            str(ROOT / "systematic_studies" / "visualisation" / "plot_results.py"),
            "--csv-path",
            str(args.outputs_dir),
        ]
    )
    print("Timing sweep and plot generation completed after parity gate pass.")


if __name__ == "__main__":
    main()
