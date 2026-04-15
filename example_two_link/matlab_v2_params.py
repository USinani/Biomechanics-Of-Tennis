#!/usr/bin/env python3
"""Parameter presets for the MATLAB_v2 two-link dynamics bridge."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class TwoLinkParams:
    """Parameter container aligned with MATLAB_v2 naming."""

    l1: float
    l2: float
    m1: float
    m2: float
    lc1: float
    lc2: float
    I1: float
    I2: float
    g: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


def default_matlab_v2_params() -> TwoLinkParams:
    """Default values taken from MATLAB_v2 examples."""
    return TwoLinkParams(
        l1=0.30,
        l2=0.35,
        m1=2.0,
        m2=1.5,
        lc1=0.15,
        lc2=0.20,
        I1=0.025,
        I2=0.045,
        g=9.81,
    )


def params_from_mujoco_xml(xml_path: str | Path) -> TwoLinkParams:
    """
    Build an approximate parameter set from the MuJoCo two-link XML.

    Notes:
    - Uses link lengths/radii/densities from geoms where available.
    - Approximates each link as a solid capsule-like rod for inertia.
    - Keeps COM at half-length for each link.
    """
    tree = ET.parse(str(xml_path))
    root = tree.getroot()

    gravity = 9.81
    option = root.find("option")
    if option is not None and option.get("gravity"):
        gvals = [float(v) for v in option.get("gravity", "0 0 -9.81").split()]
        if len(gvals) == 3:
            gravity = abs(gvals[2])

    def _parse_fromto_length(geom_elem: ET.Element) -> float:
        vals = [float(v) for v in geom_elem.get("fromto", "").split()]
        if len(vals) != 6:
            raise ValueError("Expected geom fromto with 6 values.")
        x1, y1, z1, x2, y2, z2 = vals
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5

    def _capsule_mass(length: float, radius: float, density: float) -> float:
        # Cylinder + two hemispheres (sphere)
        import math

        vol = math.pi * radius * radius * length + (4.0 / 3.0) * math.pi * radius**3
        return density * vol

    def _rod_inertia_about_base(mass: float, length: float) -> float:
        # Simple slender rod proxy around one end in planar motion.
        return (1.0 / 3.0) * mass * length * length

    geoms = {g.get("name"): g for g in root.findall(".//geom") if g.get("name")}
    upper = geoms.get("upperarm")
    fore = geoms.get("forearm")
    if upper is None or fore is None:
        return default_matlab_v2_params()

    l1 = _parse_fromto_length(upper)
    l2 = _parse_fromto_length(fore)
    r1 = float(upper.get("size", "0.03").split()[0])
    r2 = float(fore.get("size", "0.025").split()[0])
    d1 = float(upper.get("density", "1050"))
    d2 = float(fore.get("density", "1050"))

    m1 = _capsule_mass(l1, r1, d1)
    m2 = _capsule_mass(l2, r2, d2)
    lc1 = 0.5 * l1
    lc2 = 0.5 * l2
    I1 = _rod_inertia_about_base(m1, l1)
    I2 = _rod_inertia_about_base(m2, l2)

    return TwoLinkParams(l1=l1, l2=l2, m1=m1, m2=m2, lc1=lc1, lc2=lc2, I1=I1, I2=I2, g=gravity)

