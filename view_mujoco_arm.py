#!/usr/bin/env python3
"""Load and visualize mujoco_arm.xml in the MuJoCo viewer. No RL, no policy - just the model."""
import os

import mujoco
import mujoco.viewer

ASSET = os.path.join(os.path.dirname(__file__), "mujoco_arm.xml")


def main() -> None:
    model = mujoco.MjModel.from_xml_path(ASSET)
    data = mujoco.MjData(model)

    print("Loaded mujoco_arm.xml. Close the viewer window to exit.")
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
