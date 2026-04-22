#!/usr/bin/env python3
"""Load and view assets/scenes/two_link_model_scene.xml in MuJoCo viewer."""

from __future__ import annotations

import os

import mujoco
import mujoco.viewer


_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = (
    os.path.join(_HERE, "assets", "scenes", "two_link_model_scene.xml"),
    os.path.join(_HERE, "two_link_model_scene.xml"),
    os.path.join(_HERE, "3D_model", "two_link_model_scene.xml"),
)


def _resolve_asset() -> str:
    for path in _CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Could not find two_link_model_scene.xml. Tried: " + ", ".join(_CANDIDATES)
    )


def main() -> None:
    model = mujoco.MjModel.from_xml_path(_resolve_asset())
    data = mujoco.MjData(model)

    print("Loaded 3D model scene. Close viewer window to exit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()

