#!/usr/bin/env python3
"""Open mesh wrapper XML in MuJoCo viewer."""

from __future__ import annotations

from pathlib import Path
import time

import mujoco
import mujoco.viewer


def main() -> None:
    xml = Path(__file__).resolve().parent / "view_mesh.xml"
    model = mujoco.MjModel.from_xml_path(str(xml))
    data = mujoco.MjData(model)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()
            time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()

