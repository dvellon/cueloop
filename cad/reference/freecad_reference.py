"""Generate CueLoop's non-authoritative OpenCascade reference model.

Run with FreeCADCmd (FreeCAD 1.1 or newer).  The model uses the same audited
JSON parameters as the authoritative Autodesk Fusion generator and writes
actual STEP/STL solids plus a geometry report.  This path exists to catch
dimension, clearance, output-structure, and boolean-solid defects on Ubuntu.
It is never a substitute for the native Fusion timeline or contest .f3d.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import FreeCAD as App
import Part


SCRIPT_VERSION = "1.0.0"
CAD_ROOT = Path(__file__).resolve().parents[1]
PARAMETER_PATH = CAD_ROOT / "design_parameters.json"
CONTRACT_PATH = CAD_ROOT / "design_contract.json"
OUTPUT_DIR = CAD_ROOT / "reference_exports"
MANUFACTURING_DIR = OUTPUT_DIR / "manufacturing"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def number(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def translated(shape: Part.Shape, x: float, y: float, z: float) -> Part.Shape:
    result = shape.copy()
    result.translate(App.Vector(x, y, z))
    return result


def rounded_box(
    length: float, width: float, height: float, radius: float
) -> Part.Shape:
    if min(length, width, height) <= 0:
        raise ValueError("rounded_box dimensions must be positive")
    radius = min(radius, length / 2.01, width / 2.01)
    if radius <= 0:
        return Part.makeBox(length, width, height)
    pieces = [
        translated(Part.makeBox(length - 2.0 * radius, width, height), radius, 0, 0),
        translated(Part.makeBox(length, width - 2.0 * radius, height), 0, radius, 0),
    ]
    for x in (radius, length - radius):
        for y in (radius, width - radius):
            pieces.append(
                translated(Part.makeCylinder(radius, height), x, y, 0)
            )
    result = pieces[0]
    for piece in pieces[1:]:
        result = result.fuse(piece)
    return result.removeSplitter()


def fuse_all(base: Part.Shape, additions: list[Part.Shape]) -> Part.Shape:
    result = base
    for addition in additions:
        result = result.fuse(addition)
    return result.removeSplitter()


def cut_all(base: Part.Shape, tools: list[Part.Shape]) -> Part.Shape:
    result = base
    for tool in tools:
        result = result.cut(tool)
    return result.removeSplitter()


def open_shell(
    length: float,
    width: float,
    height: float,
    wall: float,
    floor: float,
    radius: float,
) -> Part.Shape:
    outer = rounded_box(length, width, height, radius)
    inner = rounded_box(
        length - 2.0 * wall,
        width - 2.0 * wall,
        height - floor + 0.5,
        max(0.5, radius - wall),
    )
    inner = translated(inner, wall, wall, floor)
    return outer.cut(inner).removeSplitter()


def screw_locations(
    length: float, width: float, offset: float
) -> list[tuple[float, float]]:
    return [
        (offset, offset),
        (length - offset, offset),
        (length - offset, width - offset),
        (offset, width - offset),
    ]


def boss_ring(
    x: float,
    y: float,
    z: float,
    height: float,
    outer_diameter: float,
    inner_diameter: float,
) -> Part.Shape:
    outer = translated(
        Part.makeCylinder(outer_diameter / 2.0, height), x, y, z
    )
    inner = translated(
        Part.makeCylinder(inner_diameter / 2.0, height + 0.4),
        x,
        y,
        z - 0.2,
    )
    return outer.cut(inner)


def lid_lip_shapes(
    prefix: dict[str, Any],
    mfg: dict[str, Any],
    length: float,
    width: float,
) -> list[Part.Shape]:
    lip_height = number(prefix, "lid_lip_height")
    lip_width = number(prefix, "lid_lip_width")
    inset = number(mfg, "wall") + number(mfg, "print_gap")
    inner_length = length - 2.0 * inset
    inner_width = width - 2.0 * inset
    z = -lip_height
    height = lip_height + 0.1
    return [
        translated(Part.makeBox(inner_length, lip_width, height), inset, inset, z),
        translated(
            Part.makeBox(inner_length, lip_width, height),
            inset,
            inset + inner_width - lip_width,
            z,
        ),
        translated(
            Part.makeBox(lip_width, inner_width - 2.0 * lip_width, height),
            inset,
            inset + lip_width,
            z,
        ),
        translated(
            Part.makeBox(lip_width, inner_width - 2.0 * lip_width, height),
            inset + inner_length - lip_width,
            inset + lip_width,
            z,
        ),
    ]


def build_pod_bottom(params: dict[str, Any]) -> Part.Shape:
    mfg = params["manufacturing"]
    pod = params["pod"]
    hardware = params["source_hardware"]
    length = number(pod, "outer_length")
    width = number(pod, "outer_width")
    height = number(pod, "bottom_height")
    wall = number(mfg, "wall")
    floor = number(mfg, "floor")
    shape = open_shell(
        length, width, height, wall, floor, number(pod, "corner_radius")
    )

    cuts = [
        translated(
            Part.makeBox(
                wall + 1.0,
                number(pod, "usb_opening_width"),
                number(pod, "usb_opening_height"),
            ),
            length - wall - 0.5,
            (width - number(pod, "usb_opening_width")) / 2.0,
            number(pod, "usb_opening_z"),
        ),
        translated(
            Part.makeBox(
                wall + 1.0,
                number(pod, "cable_opening_width"),
                number(pod, "cable_opening_height"),
            ),
            -0.5,
            (width - number(pod, "cable_opening_width")) / 2.0,
            number(pod, "cable_opening_z"),
        ),
    ]
    for index in range(int(number(pod, "vent_slot_count"))):
        cuts.append(
            translated(
                Part.makeBox(
                    number(pod, "vent_slot_length"),
                    wall + 1.0,
                    number(pod, "vent_slot_width"),
                ),
                (length - number(pod, "vent_slot_length")) / 2.0,
                -0.5,
                15.0 + index * number(pod, "vent_slot_spacing"),
            )
        )
    shape = cut_all(shape, cuts)

    additions: list[Part.Shape] = []
    for x, y in screw_locations(
        length, width, number(pod, "boss_edge_offset")
    ):
        additions.append(
            boss_ring(
                x,
                y,
                floor - 0.1,
                height - floor - 0.9,
                number(mfg, "m2_boss_diameter"),
                number(mfg, "m2_pilot_diameter"),
            )
        )
    xiao = hardware["xiao_sense"]
    deck_x = (length - number(xiao, "length")) / 2.0
    deck_y = (width - number(xiao, "width")) / 2.0
    battery = hardware["lipo_500"]
    bridge_z = (
        floor
        + number(pod, "battery_floor_gap")
        + number(battery, "height_envelope")
        + number(pod, "battery_bridge_clearance")
    )
    for rail_y in (
        deck_y + 2.0,
        deck_y + number(xiao, "width") - 4.0,
    ):
        additions.append(
            translated(
                Part.makeBox(
                    length,
                    2.0,
                    number(pod, "board_bridge_thickness"),
                ),
                0.0,
                rail_y,
                bridge_z,
            )
        )
    battery_x = (length - number(battery, "length")) / 2.0
    battery_y = (width - number(battery, "width")) / 2.0
    for rail_y in (
        battery_y - number(pod, "battery_restraint_gap") - 1.4,
        battery_y
        + number(battery, "width")
        + number(pod, "battery_restraint_gap"),
    ):
        additions.append(
            translated(
                Part.makeBox(
                    number(battery, "length"),
                    1.4,
                    number(pod, "battery_rail_height") + 0.1,
                ),
                battery_x,
                rail_y,
                floor - 0.1,
            )
        )
    tongue_x = (length - number(pod, "dock_tongue_length")) / 2.0
    tongue_y = (width - number(pod, "dock_tongue_width")) / 2.0
    additions.append(
        translated(
            Part.makeBox(
                number(pod, "dock_tongue_length"),
                number(pod, "dock_tongue_width"),
                number(pod, "dock_tongue_height") + 0.1,
            ),
            tongue_x,
            tongue_y,
            -number(pod, "dock_tongue_height"),
        )
    )
    additions.append(
        translated(
            Part.makeBox(
                number(pod, "dock_latch_width"),
                number(pod, "dock_latch_depth") + 0.1,
                number(pod, "dock_tongue_height"),
            ),
            (length - number(pod, "dock_latch_width")) / 2.0,
            tongue_y - number(pod, "dock_latch_depth"),
            -number(pod, "dock_tongue_height"),
        )
    )
    return fuse_all(shape, additions)


def build_pod_top(params: dict[str, Any]) -> Part.Shape:
    mfg = params["manufacturing"]
    pod = params["pod"]
    length = number(pod, "outer_length")
    width = number(pod, "outer_width")
    height = number(pod, "top_height")
    shape = rounded_box(length, width, height, number(pod, "corner_radius"))
    shape = fuse_all(shape, lid_lip_shapes(pod, mfg, length, width))
    cuts: list[Part.Shape] = []
    for x, y in screw_locations(
        length, width, number(pod, "boss_edge_offset")
    ):
        cuts.append(
            translated(
                Part.makeCylinder(
                    number(mfg, "m2_clearance_diameter") / 2.0,
                    height + number(pod, "lid_lip_height") + 0.3,
                ),
                x,
                y,
                -number(pod, "lid_lip_height") - 0.1,
            )
        )
    mic_x = number(pod, "mic_center_x")
    mic_y = number(pod, "mic_center_y")
    mic_points = [(mic_x, mic_y)]
    for index in range(6):
        angle = index * 3.141592653589793 / 3.0
        mic_points.append(
            (
                mic_x + number(pod, "mic_ring_radius") * math_cos(angle),
                mic_y + number(pod, "mic_ring_radius") * math_sin(angle),
            )
        )
    for x, y in mic_points:
        cuts.append(
            translated(
                Part.makeCylinder(
                    number(pod, "mic_hole_diameter") / 2.0,
                    height + number(pod, "lid_lip_height") + 0.3,
                ),
                x,
                y,
                -number(pod, "lid_lip_height") - 0.1,
            )
        )
    return cut_all(shape, cuts)


def math_cos(value: float) -> float:
    # Kept local so the FreeCAD script has no numerical-library dependency.
    import math

    return math.cos(value)


def math_sin(value: float) -> float:
    import math

    return math.sin(value)


def build_receiver_bottom(params: dict[str, Any]) -> Part.Shape:
    mfg = params["manufacturing"]
    receiver = params["receiver"]
    hardware = params["source_hardware"]
    length = number(receiver, "outer_length")
    width = number(receiver, "outer_width")
    height = number(receiver, "bottom_height")
    wall = number(mfg, "wall")
    floor = number(mfg, "floor")
    shape = open_shell(
        length,
        width,
        height,
        wall,
        floor,
        number(receiver, "corner_radius"),
    )
    cuts = [
        translated(
            Part.makeBox(
                wall + 1.0,
                number(receiver, "usb_power_opening_width"),
                number(receiver, "usb_power_opening_height"),
            ),
            length - wall - 0.5,
            14.0,
            number(receiver, "usb_power_opening_z"),
        ),
        translated(
            Part.makeBox(
                wall + 1.0,
                number(receiver, "cable_opening_width"),
                number(receiver, "cable_opening_height"),
            ),
            -0.5,
            62.0,
            number(receiver, "cable_opening_z"),
        ),
    ]
    for index in range(int(number(receiver, "vent_slot_count"))):
        cuts.append(
            translated(
                Part.makeBox(
                    number(receiver, "vent_slot_width"),
                    wall + 1.0,
                    number(receiver, "vent_slot_length"),
                ),
                10.0 + index * number(receiver, "vent_slot_spacing"),
                width - wall - 0.5,
                17.0,
            )
        )
    shape = cut_all(shape, cuts)
    additions: list[Part.Shape] = []
    for x, y in screw_locations(
        length, width, number(mfg, "boss_edge_offset")
    ):
        additions.append(
            boss_ring(
                x,
                y,
                floor - 0.1,
                height - floor - 0.9,
                number(mfg, "m2_boss_diameter"),
                number(mfg, "m2_pilot_diameter"),
            )
        )
    uno = hardware["uno_q"]
    uno_x = number(receiver, "uno_origin_x")
    uno_y = number(receiver, "uno_origin_y")
    for x, y in (
        (uno_x + 3.0, uno_y + 3.0),
        (uno_x + number(uno, "length") - 3.0, uno_y + 3.0),
        (
            uno_x + number(uno, "length") - 3.0,
            uno_y + number(uno, "width") - 3.0,
        ),
        (uno_x + 3.0, uno_y + number(uno, "width") - 3.0),
    ):
        additions.append(
            translated(
                Part.makeCylinder(
                    number(receiver, "uno_support_diameter") / 2.0,
                    number(receiver, "uno_standoff_height") + 0.1,
                ),
                x,
                y,
                floor - 0.1,
            )
        )
    return fuse_all(shape, additions)


def build_receiver_top(params: dict[str, Any]) -> Part.Shape:
    mfg = params["manufacturing"]
    receiver = params["receiver"]
    length = number(receiver, "outer_length")
    width = number(receiver, "outer_width")
    height = number(receiver, "top_height")
    lip_height = number(receiver, "lid_lip_height")
    shape = rounded_box(
        length, width, height, number(receiver, "corner_radius")
    )
    shape = fuse_all(shape, lid_lip_shapes(receiver, mfg, length, width))
    cuts: list[Part.Shape] = []
    for x, y in screw_locations(
        length, width, number(mfg, "boss_edge_offset")
    ):
        cuts.append(
            translated(
                Part.makeCylinder(
                    number(mfg, "m2_clearance_diameter") / 2.0,
                    height + lip_height + 0.3,
                ),
                x,
                y,
                -lip_height - 0.1,
            )
        )
    cuts.extend(
        [
            translated(
                Part.makeBox(
                    number(receiver, "light_window_length"),
                    number(receiver, "light_window_width"),
                    height + lip_height + 0.3,
                ),
                number(receiver, "light_window_x"),
                number(receiver, "light_window_y"),
                -lip_height - 0.1,
            ),
            translated(
                Part.makeBox(
                    number(receiver, "dock_pocket_length"),
                    number(receiver, "dock_pocket_width"),
                    number(receiver, "dock_pocket_depth") + 0.2,
                ),
                number(receiver, "dock_pocket_x"),
                number(receiver, "dock_pocket_y"),
                height - number(receiver, "dock_pocket_depth"),
            ),
        ]
    )
    center_x = length / 2.0
    for x in (
        center_x - number(receiver, "button_spacing"),
        center_x,
        center_x + number(receiver, "button_spacing"),
    ):
        cuts.append(
            translated(
                Part.makeCylinder(
                    number(receiver, "button_diameter") / 2.0,
                    height + lip_height + 0.3,
                ),
                x,
                number(receiver, "button_center_y"),
                -lip_height - 0.1,
            )
        )
    shape = cut_all(shape, cuts)
    dock_x = number(receiver, "dock_pocket_x")
    dock_y = number(receiver, "dock_pocket_y")
    dock_length = number(receiver, "dock_pocket_length")
    dock_width = number(receiver, "dock_pocket_width")
    rail_width = number(receiver, "dock_rail_width")
    rails = []
    for rail_x in (dock_x - rail_width, dock_x + dock_length):
        rails.append(
            translated(
                Part.makeBox(
                    rail_width,
                    dock_width - 8.0,
                    number(receiver, "dock_rail_height") + 0.1,
                ),
                rail_x,
                dock_y + 4.0,
                height - 0.1,
            )
        )
    return fuse_all(shape, rails)


def build_clip(params: dict[str, Any]) -> Part.Shape:
    mfg = params["manufacturing"]
    receiver = params["receiver"]
    length = number(receiver, "clip_length")
    width = number(receiver, "clip_width")
    thickness = number(receiver, "clip_thickness")
    arm_length = number(receiver, "clip_arm_length")
    arm_x = (length - arm_length) / 2.0
    base = rounded_box(length, width, thickness, number(mfg, "edge_radius"))
    root = translated(
        Part.makeBox(
            number(mfg, "snap_root_thickness") + 0.2,
            width - 6.0,
            number(receiver, "clip_gap") + thickness + 0.2,
        ),
        arm_x - number(mfg, "snap_root_thickness"),
        3.0,
        thickness - 0.1,
    )
    arm = translated(
        Part.makeBox(arm_length, width - 6.0, thickness),
        arm_x,
        3.0,
        thickness + number(receiver, "clip_gap"),
    )
    foot = translated(
        Part.makeBox(3.0, width - 6.0, number(receiver, "clip_foot_height")),
        arm_x + arm_length - 3.0,
        3.0,
        thickness + number(receiver, "clip_gap"),
    )
    return fuse_all(base, [root, arm, foot])


def build_diffuser(params: dict[str, Any]) -> Part.Shape:
    receiver = params["receiver"]
    return rounded_box(
        number(receiver, "light_window_length"),
        number(receiver, "light_window_width") - 0.6,
        1.8,
        1.2,
    )


def hardware_box(mapping: dict[str, Any]) -> Part.Shape:
    return Part.makeBox(
        number(mapping, "length"),
        number(mapping, "width"),
        number(mapping, "height_envelope"),
    )


def build_objects(params: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layout = params["layout"]
    mfg = params["manufacturing"]
    pod = params["pod"]
    receiver = params["receiver"]
    hardware = params["source_hardware"]
    pod_x = number(layout, "pod_origin_x")
    pod_y = number(layout, "pod_origin_y")
    receiver_x = number(layout, "receiver_origin_x")
    receiver_y = number(layout, "receiver_origin_y")
    floor = number(mfg, "floor")

    battery = hardware["lipo_500"]
    xiao = hardware["xiao_sense"]
    microphone = hardware["microphone_cartridge"]
    uno = hardware["uno_q"]
    support = hardware["support_electronics"]
    haptic = hardware["haptic_led_module"]
    result: dict[str, dict[str, Any]] = {
        "CuePod_Bottom": {
            "shape": build_pod_bottom(params),
            "placement": (pod_x, pod_y, 0.0),
        },
        "CuePod_Top": {
            "shape": build_pod_top(params),
            "placement": (
                pod_x,
                pod_y,
                number(pod, "bottom_height") + number(layout, "exploded_gap"),
            ),
        },
        "Reference_LiPo_500mAh": {
            "shape": hardware_box(battery),
            "placement": (
                pod_x + (number(pod, "outer_length") - number(battery, "length")) / 2.0,
                pod_y + (number(pod, "outer_width") - number(battery, "width")) / 2.0,
                floor + number(pod, "battery_floor_gap"),
            ),
        },
        "Reference_XIAO_Sense": {
            "shape": hardware_box(xiao),
            "placement": (
                pod_x + (number(pod, "outer_length") - number(xiao, "length")) / 2.0,
                pod_y + (number(pod, "outer_width") - number(xiao, "width")) / 2.0,
                floor
                + number(pod, "board_standoff_height")
                + number(pod, "board_support_clearance"),
            ),
        },
        "Reference_Microphone_Cartridge": {
            "shape": hardware_box(microphone),
            "placement": (
                pod_x + (number(pod, "outer_length") - number(microphone, "length")) / 2.0,
                pod_y + (number(pod, "outer_width") - number(microphone, "width")) / 2.0,
                number(pod, "bottom_height")
                - number(microphone, "height_envelope")
                - number(pod, "microphone_top_gap"),
            ),
        },
        "Receiver_Bottom": {
            "shape": build_receiver_bottom(params),
            "placement": (receiver_x, receiver_y, 0.0),
        },
        "Receiver_Top": {
            "shape": build_receiver_top(params),
            "placement": (
                receiver_x,
                receiver_y,
                number(receiver, "bottom_height") + number(layout, "exploded_gap"),
            ),
        },
        "Receiver_Carry_Clip": {
            "shape": build_clip(params),
            "placement": (
                receiver_x
                + (number(receiver, "outer_length") - number(receiver, "clip_length")) / 2.0,
                receiver_y
                + number(receiver, "outer_width")
                + number(layout, "clip_exploded_gap"),
                0.0,
            ),
        },
        "Alert_Diffuser": {
            "shape": build_diffuser(params),
            "placement": (
                receiver_x + number(receiver, "light_window_x"),
                receiver_y + number(receiver, "light_window_y") + 0.3,
                number(receiver, "bottom_height")
                + number(layout, "exploded_gap")
                + 0.4,
            ),
        },
        "Reference_UNO_Q": {
            "shape": hardware_box(uno),
            "placement": (
                receiver_x + number(receiver, "uno_origin_x"),
                receiver_y + number(receiver, "uno_origin_y"),
                floor + number(receiver, "uno_standoff_height") + 0.2,
            ),
        },
        "Reference_Support_Electronics": {
            "shape": hardware_box(support),
            "placement": (
                receiver_x + number(receiver, "support_origin_x"),
                receiver_y + number(receiver, "support_origin_y"),
                floor + 0.5,
            ),
        },
        "Reference_Haptic_LED_Module": {
            "shape": hardware_box(haptic),
            "placement": (
                receiver_x + number(receiver, "haptic_origin_x"),
                receiver_y + number(receiver, "haptic_origin_y"),
                floor + 0.5,
            ),
        },
    }
    return result


def geometry_record(name: str, shape: Part.Shape) -> dict[str, Any]:
    bounds = shape.BoundBox
    return {
        "name": name,
        "valid": bool(shape.isValid()),
        "closed": bool(shape.isClosed()),
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "volume_mm3": float(shape.Volume),
        "area_mm2": float(shape.Area),
        "bounds_mm": {
            "x": float(bounds.XLength),
            "y": float(bounds.YLength),
            "z": float(bounds.ZLength),
        },
    }


def interference_records(
    objects: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Measure forbidden overlap volume for placement/enclosure pairs."""

    pairs = [
        ("CuePod_Bottom", "Reference_LiPo_500mAh"),
        ("CuePod_Bottom", "Reference_XIAO_Sense"),
        ("CuePod_Bottom", "Reference_Microphone_Cartridge"),
        ("Reference_LiPo_500mAh", "Reference_XIAO_Sense"),
        ("Reference_LiPo_500mAh", "Reference_Microphone_Cartridge"),
        ("Reference_XIAO_Sense", "Reference_Microphone_Cartridge"),
        ("Receiver_Bottom", "Reference_UNO_Q"),
        ("Receiver_Bottom", "Reference_Support_Electronics"),
        ("Receiver_Bottom", "Reference_Haptic_LED_Module"),
        ("Reference_UNO_Q", "Reference_Support_Electronics"),
        ("Reference_UNO_Q", "Reference_Haptic_LED_Module"),
        ("Reference_Support_Electronics", "Reference_Haptic_LED_Module"),
    ]
    placed: dict[str, Part.Shape] = {}
    for name, record in objects.items():
        placed[name] = translated(record["shape"], *record["placement"])
    results = []
    for left, right in pairs:
        common = placed[left].common(placed[right])
        volume = float(common.Volume) if not common.isNull() else 0.0
        results.append(
            {
                "left": left,
                "right": right,
                "overlap_volume_mm3": volume,
                "pass": volume <= 1e-5,
            }
        )
    return results


def add_document_object(
    document: App.Document,
    name: str,
    shape: Part.Shape,
    placement: tuple[float, float, float],
    role: str,
    provenance: str,
) -> Any:
    obj = document.addObject("Part::Feature", name)
    obj.Label = name
    obj.Shape = shape
    obj.Placement = App.Placement(App.Vector(*placement), App.Rotation())
    obj.addProperty("App::PropertyString", "CueLoopRole", "CueLoop")
    obj.addProperty("App::PropertyString", "CueLoopProvenance", "CueLoop")
    obj.addProperty("App::PropertyString", "CueLoopAuthority", "CueLoop")
    obj.CueLoopRole = role
    obj.CueLoopProvenance = provenance
    obj.CueLoopAuthority = "REFERENCE_ONLY_NOT_CONTEST_AUTHORITATIVE"
    return obj


def export_local_shape(
    document: App.Document, shape: Part.Shape, step_path: Path, stl_path: Path
) -> None:
    temporary = document.addObject("Part::Feature", "TemporaryManufacturingExport")
    temporary.Shape = shape
    document.recompute()
    Part.export([temporary], str(step_path))
    Part.export([temporary], str(stl_path))
    document.removeObject(temporary.Name)


def reopen_step(path: Path) -> Part.Shape:
    reopened = Part.read(str(path))
    if reopened is None:
        raise RuntimeError(f"OpenCascade returned no shape while reopening {path}")
    return reopened


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_checksums(output_dir: Path, paths: list[Path]) -> Path:
    checksum_path = output_dir / "SHA256SUMS.txt"
    lines = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(output_dir).as_posix()
        lines.append(f"{digest}  {relative}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def main() -> int:
    params = load_json(PARAMETER_PATH)
    contract = load_json(CONTRACT_PATH)
    if params.get("schema_version") != 2 or params.get("units") != "mm":
        raise ValueError("CueLoop reference generator requires parameter schema 2 in mm")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUFACTURING_DIR.mkdir(parents=True, exist_ok=True)

    objects = build_objects(params)
    specifications = {entry["name"]: entry for entry in contract["components"]}
    expected_solids = {
        entry["name"]
        for entry in contract["components"]
        if entry["role"] in {"manufacturing", "reference"}
    }
    if set(objects) != expected_solids:
        raise ValueError(
            "Reference object set differs from contract: "
            f"missing={sorted(expected_solids - set(objects))}, "
            f"extra={sorted(set(objects) - expected_solids)}"
        )

    interferences = interference_records(objects)
    failed_interferences = [record for record in interferences if not record["pass"]]
    if failed_interferences:
        raise ValueError(
            "OpenCascade found forbidden placement intersections: "
            + json.dumps(failed_interferences, sort_keys=True)
        )

    document = App.newDocument("CueLoop_Reference_Validation")
    document_objects = []
    records = []
    for name, record in objects.items():
        geometry = geometry_record(name, record["shape"])
        if (
            not geometry["valid"]
            or not geometry["closed"]
            or geometry["solid_count"] != 1
            or geometry["volume_mm3"] <= 0
        ):
            raise ValueError(f"Invalid OpenCascade solid {name}: {geometry}")
        records.append(geometry)
        specification = specifications[name]
        document_objects.append(
            add_document_object(
                document,
                name,
                record["shape"],
                record["placement"],
                specification["role"],
                specification["provenance"],
            )
        )
    document.recompute()

    output_files: list[Path] = []
    freecad_document = OUTPUT_DIR / "CueLoop_Reference.FCStd"
    document.saveAs(str(freecad_document))
    if not freecad_document.is_file() or freecad_document.stat().st_size == 0:
        raise RuntimeError("FreeCAD reference document was not saved")
    output_files.append(freecad_document)
    assembly_step = OUTPUT_DIR / "CueLoop_Reference_Assembly.step"
    Part.export(document_objects, str(assembly_step))
    output_files.append(assembly_step)

    for specification in contract["components"]:
        if not specification.get("manufacturing_export"):
            continue
        name = specification["name"]
        stem = specification["output_stem"]
        step_path = MANUFACTURING_DIR / f"{stem}.step"
        stl_path = MANUFACTURING_DIR / f"{stem}.stl"
        export_local_shape(document, objects[name]["shape"], step_path, stl_path)
        output_files.extend((step_path, stl_path))

    reopened = reopen_step(assembly_step)
    reopened_record = geometry_record("Reopened_Assembly_STEP", reopened)
    if not reopened_record["valid"] or reopened_record["solid_count"] < len(objects):
        raise ValueError(f"Reopened assembly STEP failed validation: {reopened_record}")

    App.closeDocument(document.Name)
    reopened_document = App.openDocument(str(freecad_document))
    reopened_fcstd_solids = 0
    for name in expected_solids:
        reopened_object = reopened_document.getObject(name)
        if reopened_object is None or not hasattr(reopened_object, "Shape"):
            raise ValueError(f"Reopened FCStd is missing shape object {name}")
        reopened_geometry = geometry_record(name, reopened_object.Shape)
        if (
            not reopened_geometry["valid"]
            or not reopened_geometry["closed"]
            or reopened_geometry["solid_count"] != 1
        ):
            raise ValueError(
                f"Reopened FCStd contains invalid object {name}: {reopened_geometry}"
            )
        reopened_fcstd_solids += reopened_geometry["solid_count"]
    reopened_fcstd_validation = {
        "status": "pass",
        "object_count": len(expected_solids),
        "solid_count": reopened_fcstd_solids,
    }
    App.closeDocument(reopened_document.Name)
    # FreeCAD may create timestamped backups while replacing the generated
    # reference document. They are not evidence and must not pollute outputs.
    for backup in OUTPUT_DIR.glob("CueLoop_Reference.*.FCBak"):
        backup.unlink()

    geometry_report = {
        "schema_version": 1,
        "status": "pass",
        "generator_version": SCRIPT_VERSION,
        "freecad_version": ".".join(str(value) for value in App.Version()[:3]),
        "kernel": "OpenCascade via FreeCAD",
        "authoritative": False,
        "model_role": "automated Ubuntu reference and geometric validation",
        "objects": sorted(records, key=lambda entry: entry["name"]),
        "object_count": len(records),
        "solid_count": sum(record["solid_count"] for record in records),
        "reopened_fcstd_validation": reopened_fcstd_validation,
        "reopened_step_validation": reopened_record,
        "interference_checks": interferences,
        "claim_boundary": (
            "This validates modeled solids, dimensions, booleans, and exports only. "
            "The Autodesk contest model must be generated natively by the Fusion script."
        ),
    }
    report_path = OUTPUT_DIR / "CueLoop_Reference_geometry_report.json"
    write_json(report_path, geometry_report)
    output_files.append(report_path)

    provenance = {
        "schema_version": 1,
        "authoritative": False,
        "generator": "cad/reference/freecad_reference.py",
        "engine": "FreeCAD/OpenCascade",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "design_parameter_sha256": hashlib.sha256(PARAMETER_PATH.read_bytes()).hexdigest(),
        "design_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "original_geometry": [
            entry["name"]
            for entry in contract["components"]
            if "CueLoop original" in entry["provenance"]
        ],
        "vendor_and_estimated_reference_geometry": [
            {
                "name": entry["name"],
                "provenance": entry["provenance"],
            }
            for entry in contract["components"]
            if entry["role"] == "reference"
        ],
        "source_hardware": params["source_hardware"],
        "boundary": (
            "Simple boxes are placement envelopes only. They are not vendor CAD, "
            "original board geometry, physical-fit evidence, or manufacturing outputs."
        ),
    }
    provenance_path = OUTPUT_DIR / "CueLoop_Reference_provenance.json"
    write_json(provenance_path, provenance)
    output_files.append(provenance_path)

    parameter_snapshot_path = OUTPUT_DIR / "CueLoop_Reference_parameters.json"
    write_json(parameter_snapshot_path, params)
    output_files.append(parameter_snapshot_path)
    checksum_path = write_checksums(OUTPUT_DIR, output_files)

    print("CueLoop OpenCascade reference generation: PASS")
    print(f"FreeCAD version: {geometry_report['freecad_version']}")
    print(f"Valid solids: {geometry_report['solid_count']}")
    print(f"Reopened FCStd solids: {reopened_fcstd_solids}")
    print(f"Reopened STEP solids: {reopened_record['solid_count']}")
    print(f"Outputs: {OUTPUT_DIR}")
    print(f"Checksums: {checksum_path}")
    return 0


# FreeCADCmd loads positional .py files as macros rather than as ``__main__``.
# Calling the entry point here is therefore intentional; this file is an
# executable generator, not an importable library.
main()
