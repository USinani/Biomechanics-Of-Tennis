#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import mujoco
import mujoco.viewer


def resolve_asset() -> Path:
    root = Path(__file__).resolve().parent
    # Preferred root-level scene (current canonical path)
    root_xml = root / "dummy_two_link_obj_view.xml"
    # Backward-compatible fallback for older folder layout
    legacy_xml = root / "3D_model" / "dummy_two_link_obj_view.xml"
    if root_xml.exists():
        return root_xml
    if legacy_xml.exists():
        return legacy_xml
    raise FileNotFoundError(
        "Could not find dummy OBJ scene XML. Expected one of: "
        f"{root_xml} or {legacy_xml}"
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

