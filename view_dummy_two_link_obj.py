#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import mujoco
import mujoco.viewer


def resolve_asset() -> Path:
    root = Path(__file__).resolve().parent
    # Canonical location after the 2026-04-22 reorg.
    canonical_xml = root / "assets" / "scenes" / "dummy_two_link_obj_view.xml"
    # Backward-compatible fallbacks for older checkouts.
    root_legacy = root / "dummy_two_link_obj_view.xml"
    deep_legacy = root / "3D_model" / "dummy_two_link_obj_view.xml"
    for candidate in (canonical_xml, root_legacy, deep_legacy):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find dummy OBJ scene XML. Expected one of: "
        f"{canonical_xml}, {root_legacy}, {deep_legacy}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Compile-check the XML/mesh path and exit without opening viewer.",
    )
    args = parser.parse_args()

    asset = resolve_asset()
    try:
        model = mujoco.MjModel.from_xml_path(str(asset))
    except Exception as exc:
        raise RuntimeError(
            f"MuJoCo failed to compile scene XML at '{asset}'. "
            "Check mesh path/material refs in dummy_two_link_obj_view.xml."
        ) from exc
    print(f"Preflight OK: {asset} (nq={model.nq}, nmesh={model.nmesh})")
    if args.check_only:
        return
    data = mujoco.MjData(model)
    print(f"Loaded: {asset}")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()

