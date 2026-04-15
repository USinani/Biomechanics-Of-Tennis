#!/usr/bin/env python3
"""Load and view 3D_model/two_link_model_scene.xml in MuJoCo viewer."""

from __future__ import annotations

import os

import mujoco
import mujoco.viewer


ASSET = os.path.join(os.path.dirname(__file__), "3D_model", "two_link_model_scene.xml")


def main() -> None:
    model = mujoco.MjModel.from_xml_path(ASSET)
    data = mujoco.MjData(model)

    print("Loaded 3D model scene. Close viewer window to exit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()

