from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def generate_mjcf(model_params: Dict[str, Any]) -> str:
    """Generate an MJCF XML string for a two-link arm from JSON parameters."""
    model_name = model_params.get("model_name", "two_link_arm")
    gravity = model_params.get("gravity", [0.0, 0.0, -9.81])
    timestep = model_params.get("timestep", 0.001)
    shoulder_height = model_params.get("shoulder_height", 1.4)

    links = {link["name"]: link for link in model_params.get("links", [])}
    upperarm = links["upperarm"]
    forearm = links["forearm"]

    joints = {j["name"]: j for j in model_params.get("joints", [])}
    shoulder_joint = joints["shoulder_pitch"]
    elbow_joint = joints["elbow_pitch"]

    sites = {s["name"]: s for s in model_params.get("sites", [])}
    hand_site = sites["hand"]
    target_site = sites["target"]

    actuators = model_params.get("actuators", [])
    m_shoulder = next(a for a in actuators if a["name"] == "m_shoulder")
    m_elbow = next(a for a in actuators if a["name"] == "m_elbow")

    geom_defaults = model_params.get("contact", {}).get("geom_defaults", {})
    default_density = geom_defaults.get("density", 1200.0)
    default_rgba = geom_defaults.get("rgba", [0.7, 0.7, 0.7, 1.0])
    default_friction = geom_defaults.get("friction", [0.8, 0.1, 0.1])

    def fmt(v) -> str:
        if isinstance(v, (list, tuple)):
            return " ".join(str(x) for x in v)
        return str(v)

    xml = f"""<mujoco model="{model_name}">
  <compiler angle="degree" coordinate="local"/>
  <option timestep="{timestep}" gravity="{fmt(gravity)}"/>
  <default>
    <joint damping="{shoulder_joint.get("damping", 0.05)}" limited="true"/>
    <geom type="capsule" rgba="{fmt(default_rgba)}" density="{default_density}" friction="{fmt(default_friction)}"/>
  </default>

  <worldbody>
    <body name="shoulder" pos="0 0 {shoulder_height}">
      <joint name="{shoulder_joint["name"]}" type="{shoulder_joint["type"]}" axis="{fmt(shoulder_joint["axis"])}" range="{fmt(shoulder_joint["range_deg"])}"/>
      <geom name="upperarm" fromto="0 0 0 {upperarm["length"]} 0 0" size="{upperarm["radius"]}" density="{upperarm["density"]}"/>
      <body name="elbow" pos="{upperarm["length"]} 0 0">
        <joint name="{elbow_joint["name"]}" type="{elbow_joint["type"]}" axis="{fmt(elbow_joint["axis"])}" range="{fmt(elbow_joint["range_deg"])}"/>
        <geom name="forearm" fromto="0 0 0 {forearm["length"]} 0 0" size="{forearm["radius"]}" density="{forearm["density"]}"/>
        <site name="{hand_site["name"]}" pos="{fmt(hand_site["pos"])}" size="{hand_site["size"]}" rgba="0.2 0.2 1 1"/>
      </body>
    </body>
    <site name="{target_site["name"]}" pos="{fmt(target_site["pos"])}" size="{target_site["size"]}" rgba="1 0 0 1"/>
  </worldbody>

  <actuator>
    <motor name="{m_shoulder["name"]}" joint="{m_shoulder["joint"]}" ctrllimited="true" ctrlrange="{fmt(m_shoulder["ctrlrange"])}" gear="{m_shoulder.get("gear", 1.0)}"/>
    <motor name="{m_elbow["name"]}"    joint="{m_elbow["joint"]}"    ctrllimited="true" ctrlrange="{fmt(m_elbow["ctrlrange"])}" gear="{m_elbow.get("gear", 1.0)}"/>
  </actuator>
</mujoco>
"""
    return xml


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_path", type=Path, default=Path("model_params.json"))
    parser.add_argument(
        "--out",
        dest="output_path",
        type=Path,
        default=Path("mujoco_arm_from_json.xml"),
    )
    args = parser.parse_args()

    with args.input_path.open("r") as f:
        model_params = json.load(f)

    xml = generate_mjcf(model_params)
    with args.output_path.open("w") as f:
        f.write(xml)

    print(f"Wrote MJCF to {args.output_path}")


if __name__ == "__main__":
    main()

