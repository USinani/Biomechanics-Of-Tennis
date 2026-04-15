#!/usr/bin/env python3
"""Compile-check MJCF model files and report mesh/path errors clearly."""

from __future__ import annotations

import argparse
from pathlib import Path

import mujoco


def check_one(xml_path: Path) -> tuple[bool, str]:
    try:
        model = mujoco.MjModel.from_xml_path(str(xml_path))
        return True, f"OK: {xml_path} (nq={model.nq}, nv={model.nv}, nu={model.nu}, nmesh={model.nmesh})"
    except Exception as exc:  # noqa: BLE001
        return False, f"FAIL: {xml_path}\n  {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        nargs="+",
        default=["example_two_link/view_mesh.xml", "example_two_link/view_matlab_model.xml"],
        help="MJCF files to compile-check.",
    )
    args = parser.parse_args()

    all_ok = True
    for model_str in args.models:
        ok, msg = check_one(Path(model_str))
        print(msg)
        all_ok = all_ok and ok
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

