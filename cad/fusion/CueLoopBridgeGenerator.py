"""Build and export the authoritative native CueLoop Bridge Fusion model.

This script is intended to run from Autodesk Fusion's Scripts and Add-Ins
dialog.  It creates a new parametric design using native sketches, constrained
profiles, construction planes, extrude/combine/fillet features, named user
parameters, components, occurrences, and captured design history.  It never
imports a mesh, STEP body, or other completed design.

The sibling ``design_parameters.json`` and ``design_contract.json`` files are
the auditable source contract.  Manufacturer-derived bodies are deliberately
simple placement envelopes and carry provenance attributes; they are not
presented as original board or battery geometry.  All dimensions remain
subject to the physical checks in ``cad/DIMENSION_VALIDATION.md``.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import traceback
from typing import Any

import adsk.core
import adsk.fusion


SCRIPT_VERSION = "2.0.0"
OUTPUT_DIRECTORY_NAME = "CueLoop_Bridge_Native_v2"
ROOT_NAME = "CueLoop Bridge Native Parametric Assembly"
ATTRIBUTE_GROUP = "CueLoop"
VALIDATION_ATTRIBUTE = "ESTIMATED_DIMENSIONS_VALIDATE_BEFORE_MANUFACTURE"


def mm(value: float) -> float:
    """Convert millimeters to Fusion's internal centimeter length unit."""

    return float(value) / 10.0


def point(x: float, y: float, z: float = 0.0) -> adsk.core.Point3D:
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def _source_directory() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _required_path(filename: str) -> str:
    here = _source_directory()
    candidates = (
        os.path.join(here, filename),
        os.path.join(os.path.dirname(here), filename),
    )
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        f"Missing {filename}; copy it beside this script before running Fusion"
    )


def _required_json(filename: str) -> dict[str, Any]:
    with open(_required_path(filename), "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{filename} must contain a JSON object")
    return value


def load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    parameters = _required_json("design_parameters.json")
    contract = _required_json("design_contract.json")
    if parameters.get("schema_version") != 2:
        raise ValueError("design_parameters.json schema_version must be 2")
    if parameters.get("units") != "mm":
        raise ValueError("design_parameters.json units must be mm")
    if contract.get("schema_version") != 1:
        raise ValueError("design_contract.json schema_version must be 1")
    return parameters, contract


def _numeric(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Expected numeric parameter {key}")
    return float(value)


def validate_parameter_geometry(params: dict[str, Any]) -> dict[str, Any]:
    """Reject unsafe or internally inconsistent parameter sets before CAD."""

    mfg = params["manufacturing"]
    pod = params["pod"]
    receiver = params["receiver"]
    hardware = params["source_hardware"]

    numeric_groups: list[tuple[str, dict[str, Any]]] = [
        ("manufacturing", mfg),
        ("pod", pod),
        ("receiver", receiver),
    ]
    for group_name, group in numeric_groups:
        for name, value in group.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{group_name}.{name} must be numeric")
            if float(value) <= 0:
                raise ValueError(f"{group_name}.{name} must be positive")

    wall = _numeric(mfg, "wall")
    floor = _numeric(mfg, "floor")
    clearance = _numeric(mfg, "fit_clearance")
    if wall < 2.0 or floor < 2.0:
        raise ValueError("PCBWay production-intent wall and floor must be >= 2.0 mm")
    if _numeric(mfg, "minimum_web") > wall:
        raise ValueError("minimum_web cannot exceed nominal wall")
    if _numeric(mfg, "m2_boss_diameter") <= _numeric(
        mfg, "m2_pilot_diameter"
    ) + 2.0 * _numeric(mfg, "minimum_web"):
        raise ValueError("M2 boss lacks the declared minimum radial web")

    pod_inner = (
        _numeric(pod, "outer_length") - 2.0 * wall,
        _numeric(pod, "outer_width") - 2.0 * wall,
        _numeric(pod, "bottom_height") - floor,
    )
    battery = hardware["lipo_500"]
    xiao = hardware["xiao_sense"]
    if pod_inner[0] < _numeric(battery, "length") + 2.0 * clearance:
        raise ValueError("CuePod inner length does not clear the LiPo envelope")
    if pod_inner[1] < _numeric(battery, "width") + 2.0 * clearance:
        raise ValueError("CuePod inner width does not clear the LiPo envelope")
    if pod_inner[0] < _numeric(xiao, "length") + 2.0 * clearance:
        raise ValueError("CuePod inner length does not clear the XIAO envelope")
    if pod_inner[1] < _numeric(xiao, "width") + 2.0 * clearance:
        raise ValueError("CuePod inner width does not clear the XIAO envelope")
    battery_top = (
        floor
        + _numeric(pod, "battery_floor_gap")
        + _numeric(battery, "height_envelope")
    )
    bridge_bottom = battery_top + _numeric(pod, "battery_bridge_clearance")
    bridge_top = bridge_bottom + _numeric(pod, "board_bridge_thickness")
    xiao_bottom = (
        floor
        + _numeric(pod, "board_standoff_height")
        + _numeric(pod, "board_support_clearance")
    )
    xiao_top = xiao_bottom + _numeric(xiao, "height_envelope")
    if xiao_top > _numeric(pod, "bottom_height") + _numeric(pod, "top_height"):
        raise ValueError("XIAO stacked envelope exceeds the closed CuePod height")
    if xiao_bottom - bridge_top + 1e-9 < _numeric(
        pod, "board_support_clearance"
    ):
        raise ValueError("XIAO bridge-to-board clearance is below the declaration")
    microphone = hardware["microphone_cartridge"]
    microphone_bottom = (
        _numeric(pod, "bottom_height")
        - _numeric(microphone, "height_envelope")
        - _numeric(pod, "microphone_top_gap")
    )
    if microphone_bottom - xiao_top + 1e-9 < _numeric(mfg, "print_gap"):
        raise ValueError("XIAO-to-microphone vertical clearance is below print_gap")

    receiver_inner = (
        _numeric(receiver, "outer_length") - 2.0 * wall,
        _numeric(receiver, "outer_width") - 2.0 * wall,
        _numeric(receiver, "bottom_height") - floor,
    )
    uno = hardware["uno_q"]
    if receiver_inner[0] < _numeric(uno, "length") + 2.0 * clearance:
        raise ValueError("Receiver inner length does not clear the UNO Q envelope")
    if receiver_inner[1] < _numeric(uno, "width") + 2.0 * clearance:
        raise ValueError("Receiver inner width does not clear the UNO Q envelope")
    uno_top = (
        floor
        + _numeric(receiver, "uno_standoff_height")
        + _numeric(uno, "height_envelope")
    )
    if uno_top > _numeric(receiver, "bottom_height"):
        raise ValueError("UNO Q envelope exceeds the receiver bottom height")

    dock_length_clearance = _numeric(receiver, "dock_pocket_length") - _numeric(
        pod, "outer_length"
    )
    dock_width_clearance = _numeric(receiver, "dock_pocket_width") - _numeric(
        pod, "outer_width"
    )
    if dock_length_clearance < 2.0 * clearance:
        raise ValueError("Dock length clearance is below the declared fit clearance")
    if dock_width_clearance < 2.0 * clearance:
        raise ValueError("Dock width clearance is below the declared fit clearance")
    if _numeric(receiver, "dock_pocket_depth") >= _numeric(receiver, "top_height"):
        raise ValueError("Dock pocket would cut through the receiver top")

    return {
        "pod_inner_mm": list(pod_inner),
        "receiver_inner_mm": list(receiver_inner),
        "dock_total_clearance_mm": [dock_length_clearance, dock_width_clearance],
        "xiao_closed_height_margin_mm": (
            _numeric(pod, "bottom_height")
            + _numeric(pod, "top_height")
            - xiao_top
        ),
        "pod_vertical_clearance_mm": {
            "battery_to_bridge": bridge_bottom - battery_top,
            "bridge_to_xiao": xiao_bottom - bridge_top,
            "xiao_to_microphone": microphone_bottom - xiao_top,
        },
        "uno_vertical_margin_mm": _numeric(receiver, "bottom_height") - uno_top,
    }


def _parameter_name(group: str, key: str, parent: str | None = None) -> str:
    prefixes = {
        "manufacturing": "mfg",
        "layout": "layout",
        "pod": "pod",
        "receiver": "receiver",
        "source_hardware": "ref",
    }
    prefix = prefixes[group]
    parts = [prefix]
    if parent:
        parts.append(parent)
    parts.append(key)
    return "_".join(parts).replace("-", "_")


def _parameter_unit(key: str) -> tuple[str, str]:
    if key.endswith("_count"):
        return "", ""
    if key.endswith("_degrees"):
        return "deg", " deg"
    return "mm", " mm"


def numeric_parameter_records(params: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for group in ("manufacturing", "layout", "pod", "receiver"):
        for key, value in params[group].items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            unit, suffix = _parameter_unit(key)
            records.append(
                {
                    "name": _parameter_name(group, key),
                    "expression": f"{value}{suffix}",
                    "unit": unit,
                    "source_path": f"{group}.{key}",
                }
            )
    for parent, mapping in params["source_hardware"].items():
        for key, value in mapping.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            unit, suffix = _parameter_unit(key)
            records.append(
                {
                    "name": _parameter_name("source_hardware", key, parent),
                    "expression": f"{value}{suffix}",
                    "unit": unit,
                    "source_path": f"source_hardware.{parent}.{key}",
                }
            )
    return records


def add_user_parameters(
    design: adsk.fusion.Design, params: dict[str, Any]
) -> list[dict[str, Any]]:
    records = numeric_parameter_records(params)
    for record in records:
        existing = design.userParameters.itemByName(record["name"])
        if existing:
            existing.expression = record["expression"]
            continue
        design.userParameters.add(
            record["name"],
            adsk.core.ValueInput.createByString(record["expression"]),
            record["unit"],
            "CueLoop generated parameter; source: " + record["source_path"],
        )
    # These declared values are also checked in JSON, but inside Fusion the
    # dock dimensions remain equation-driven by the pod and process clearance.
    derived_expressions = {
        "receiver_dock_pocket_length": "pod_outer_length + 2 * mfg_fit_clearance",
        "receiver_dock_pocket_width": "pod_outer_width + 2 * mfg_fit_clearance",
    }
    for name, expression in derived_expressions.items():
        parameter = design.userParameters.itemByName(name)
        if parameter is None:
            raise KeyError(f"Missing derived Fusion user parameter {name}")
        parameter.expression = expression
    return records


def component_at(
    parent: adsk.fusion.Component,
    name: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    role: str = "assembly",
    provenance: str = "CueLoop original geometry",
) -> adsk.fusion.Component:
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(mm(x), mm(y), mm(z))
    occurrence = parent.occurrences.addNewComponent(transform)
    component = occurrence.component
    component.name = name
    component.partNumber = name
    component.attributes.add(ATTRIBUTE_GROUP, "Role", role)
    component.attributes.add(ATTRIBUTE_GROUP, "Provenance", provenance)
    component.attributes.add(ATTRIBUTE_GROUP, "GeneratorVersion", SCRIPT_VERSION)
    return component


def plane_at(
    component: adsk.fusion.Component,
    z_mm: float,
    expression: str | None = None,
    name: str | None = None,
) -> adsk.core.Base:
    if abs(z_mm) < 1e-9 and expression is None:
        return component.xYConstructionPlane
    plane_input = component.constructionPlanes.createInput()
    value = (
        adsk.core.ValueInput.createByString(expression)
        if expression
        else adsk.core.ValueInput.createByReal(mm(z_mm))
    )
    if not plane_input.setByOffset(component.xYConstructionPlane, value):
        raise RuntimeError(f"Unable to define construction plane {name or z_mm}")
    plane = component.constructionPlanes.add(plane_input)
    plane.name = name or f"Offset_{z_mm:.2f}_mm"
    return plane


def _set_rectangle_dimensions(
    sketch: adsk.fusion.Sketch,
    lines: Any,
    length_expression: str | None,
    width_expression: str | None,
    text_x: float,
    text_y: float,
) -> None:
    horizontal = None
    vertical = None
    for index in range(lines.count):
        line = lines.item(index)
        start = line.startSketchPoint.geometry
        end = line.endSketchPoint.geometry
        if abs(start.x - end.x) >= abs(start.y - end.y) and horizontal is None:
            horizontal = line
        elif vertical is None:
            vertical = line
    dimensions = sketch.sketchDimensions
    if horizontal and length_expression:
        dimension = dimensions.addDistanceDimension(
            horizontal.startSketchPoint,
            horizontal.endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            point(text_x, text_y - 4.0),
        )
        dimension.parameter.expression = length_expression
    if vertical and width_expression:
        dimension = dimensions.addDistanceDimension(
            vertical.startSketchPoint,
            vertical.endSketchPoint,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            point(text_x - 4.0, text_y),
        )
        dimension.parameter.expression = width_expression


def rectangle_profile(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    length: float,
    width: float,
    z: float = 0.0,
    length_expression: str | None = None,
    width_expression: str | None = None,
    z_expression: str | None = None,
) -> adsk.fusion.Profile:
    sketch = component.sketches.add(
        plane_at(component, z, z_expression, f"{name}_Plane")
    )
    sketch.name = f"{name}_Sketch"
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        point(x, y), point(x + length, y + width)
    )
    # Fix exactly one corner; length/width remain driven by named dimensions.
    lines.item(0).startSketchPoint.isFixed = True
    _set_rectangle_dimensions(
        sketch,
        lines,
        length_expression,
        width_expression,
        x + length / 2.0,
        y + width / 2.0,
    )
    if sketch.profiles.count != 1:
        raise RuntimeError(f"{name} did not create exactly one closed profile")
    return sketch.profiles.item(0)


def circle_profile(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    diameter: float,
    z: float = 0.0,
    diameter_expression: str | None = None,
    z_expression: str | None = None,
) -> adsk.fusion.Profile:
    sketch = component.sketches.add(
        plane_at(component, z, z_expression, f"{name}_Plane")
    )
    sketch.name = f"{name}_Sketch"
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(x, y), mm(diameter / 2.0)
    )
    circle.centerSketchPoint.isFixed = True
    if diameter_expression:
        dimension = sketch.sketchDimensions.addDiameterDimension(
            circle, point(x + diameter, y + diameter)
        )
        dimension.parameter.expression = diameter_expression
    if sketch.profiles.count != 1:
        raise RuntimeError(f"{name} did not create exactly one closed profile")
    return sketch.profiles.item(0)


def extrude_profile(
    component: adsk.fusion.Component,
    profile: adsk.fusion.Profile,
    name: str,
    distance_expression: str,
    operation: adsk.fusion.FeatureOperations,
) -> adsk.fusion.ExtrudeFeature:
    extrudes = component.features.extrudeFeatures
    feature_input = extrudes.createInput(profile, operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(distance_expression)
    )
    if not feature_input.setOneSideExtent(
        extent, adsk.fusion.ExtentDirections.PositiveExtentDirection
    ):
        raise RuntimeError(f"Unable to define extrusion distance for {name}")
    feature = extrudes.add(feature_input)
    feature.name = name
    return feature


def fillet_vertical_edges(
    component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    name: str,
    radius_expression: str,
) -> None:
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        if (
            abs(start.x - end.x) < mm(0.05)
            and abs(start.y - end.y) < mm(0.05)
            and abs(start.z - end.z) > mm(0.1)
        ):
            edges.add(edge)
    if edges.count == 0:
        return
    fillet_input = component.features.filletFeatures.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edges,
        adsk.core.ValueInput.createByString(radius_expression),
        True,
    )
    feature = component.features.filletFeatures.add(fillet_input)
    feature.name = name


def new_box(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    length_expression: str | None = None,
    width_expression: str | None = None,
    height_expression: str | None = None,
    z_expression: str | None = None,
    radius_expression: str | None = None,
) -> adsk.fusion.BRepBody:
    profile = rectangle_profile(
        component,
        name,
        x,
        y,
        length,
        width,
        z,
        length_expression,
        width_expression,
        z_expression,
    )
    feature = extrude_profile(
        component,
        profile,
        f"{name}_Extrude",
        height_expression or f"{height} mm",
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    if radius_expression:
        fillet_vertical_edges(
            component, body, f"{name}_Vertical_Fillet", radius_expression
        )
    return body


def join_box(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    length_expression: str | None = None,
    width_expression: str | None = None,
    height_expression: str | None = None,
    z_expression: str | None = None,
) -> None:
    profile = rectangle_profile(
        component,
        name,
        x,
        y,
        length,
        width,
        z,
        length_expression,
        width_expression,
        z_expression,
    )
    extrude_profile(
        component,
        profile,
        f"{name}_Join",
        height_expression or f"{height} mm",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )


def cut_box(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    length_expression: str | None = None,
    width_expression: str | None = None,
    height_expression: str | None = None,
    z_expression: str | None = None,
) -> None:
    profile = rectangle_profile(
        component,
        name,
        x,
        y,
        length,
        width,
        z,
        length_expression,
        width_expression,
        z_expression,
    )
    extrude_profile(
        component,
        profile,
        f"{name}_Cut",
        height_expression or f"{height} mm",
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def join_cylinder(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    diameter: float,
    height: float,
    diameter_expression: str | None = None,
    height_expression: str | None = None,
    z_expression: str | None = None,
) -> None:
    profile = circle_profile(
        component,
        name,
        x,
        y,
        diameter,
        z,
        diameter_expression,
        z_expression,
    )
    extrude_profile(
        component,
        profile,
        f"{name}_Join",
        height_expression or f"{height} mm",
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )


def cut_cylinder(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    diameter: float,
    height: float,
    diameter_expression: str | None = None,
    height_expression: str | None = None,
    z_expression: str | None = None,
) -> None:
    profile = circle_profile(
        component,
        name,
        x,
        y,
        diameter,
        z,
        diameter_expression,
        z_expression,
    )
    extrude_profile(
        component,
        profile,
        f"{name}_Cut",
        height_expression or f"{height} mm",
        adsk.fusion.FeatureOperations.CutFeatureOperation,
    )


def screw_locations(length: float, width: float, offset: float) -> list[tuple[float, float]]:
    return [
        (offset, offset),
        (length - offset, offset),
        (length - offset, width - offset),
        (offset, width - offset),
    ]


def open_shell(
    component: adsk.fusion.Component,
    name: str,
    prefix: str,
    length: float,
    width: float,
    height: float,
    radius_expression: str,
) -> adsk.fusion.BRepBody:
    body = new_box(
        component,
        name,
        0.0,
        0.0,
        0.0,
        length,
        width,
        height,
        f"{prefix}_outer_length",
        f"{prefix}_outer_width",
        f"{prefix}_bottom_height",
        radius_expression=radius_expression,
    )
    wall = mm_value(component, "mfg_wall")
    floor = mm_value(component, "mfg_floor")
    cut_box(
        component,
        f"{name}_Internal_Cavity",
        wall,
        wall,
        floor,
        length - 2.0 * wall,
        width - 2.0 * wall,
        height - floor + 0.5,
        f"{prefix}_outer_length - 2 * mfg_wall",
        f"{prefix}_outer_width - 2 * mfg_wall",
        f"{prefix}_bottom_height - mfg_floor + 0.5 mm",
        "mfg_floor",
    )
    return body


def mm_value(component: adsk.fusion.Component, parameter_name: str) -> float:
    design = adsk.fusion.Design.cast(component.parentDesign)
    parameter = design.userParameters.itemByName(parameter_name)
    if not parameter:
        raise KeyError(f"Missing Fusion user parameter {parameter_name}")
    return float(parameter.value) * 10.0


def add_bosses(
    component: adsk.fusion.Component,
    prefix: str,
    locations: list[tuple[float, float]],
    floor: float,
    height: float,
) -> None:
    for index, (x, y) in enumerate(locations, start=1):
        join_cylinder(
            component,
            f"{prefix}_M2_Boss_{index}",
            x,
            y,
            floor - 0.1,
            mm_value(component, "mfg_m2_boss_diameter"),
            height + 0.1,
            "mfg_m2_boss_diameter",
            f"{height + 0.1} mm",
        )
        cut_cylinder(
            component,
            f"{prefix}_M2_Pilot_{index}",
            x,
            y,
            floor - 0.2,
            mm_value(component, "mfg_m2_pilot_diameter"),
            height + 0.4,
            "mfg_m2_pilot_diameter",
            f"{height + 0.4} mm",
        )


def add_lid_fastener_holes(
    component: adsk.fusion.Component,
    prefix: str,
    locations: list[tuple[float, float]],
    top_height: float,
) -> None:
    for index, (x, y) in enumerate(locations, start=1):
        cut_cylinder(
            component,
            f"{prefix}_M2_Clearance_{index}",
            x,
            y,
            -0.1,
            mm_value(component, "mfg_m2_clearance_diameter"),
            top_height + 0.2,
            "mfg_m2_clearance_diameter",
            f"{top_height + 0.2} mm",
        )


def add_lid_lip(
    component: adsk.fusion.Component,
    prefix: str,
    length: float,
    width: float,
    lip_height: float,
    lip_width: float,
) -> None:
    inset = mm_value(component, "mfg_wall") + mm_value(component, "mfg_print_gap")
    inner_length = length - 2.0 * inset
    inner_width = width - 2.0 * inset
    z = -lip_height
    z_expression = f"-{prefix}_lid_lip_height"
    join_box(
        component,
        f"{prefix}_Lid_Lip_Front",
        inset,
        inset,
        z,
        inner_length,
        lip_width,
        lip_height + 0.1,
        f"{prefix}_outer_length - 2 * (mfg_wall + mfg_print_gap)",
        f"{prefix}_lid_lip_width",
        f"{prefix}_lid_lip_height + 0.1 mm",
        z_expression,
    )
    join_box(
        component,
        f"{prefix}_Lid_Lip_Back",
        inset,
        inset + inner_width - lip_width,
        z,
        inner_length,
        lip_width,
        lip_height + 0.1,
        f"{prefix}_outer_length - 2 * (mfg_wall + mfg_print_gap)",
        f"{prefix}_lid_lip_width",
        f"{prefix}_lid_lip_height + 0.1 mm",
        z_expression,
    )
    join_box(
        component,
        f"{prefix}_Lid_Lip_Left",
        inset,
        inset + lip_width,
        z,
        lip_width,
        inner_width - 2.0 * lip_width,
        lip_height + 0.1,
        f"{prefix}_lid_lip_width",
        f"{prefix}_outer_width - 2 * (mfg_wall + mfg_print_gap + {lip_width} mm)",
        f"{prefix}_lid_lip_height + 0.1 mm",
        z_expression,
    )
    join_box(
        component,
        f"{prefix}_Lid_Lip_Right",
        inset + inner_length - lip_width,
        inset + lip_width,
        z,
        lip_width,
        inner_width - 2.0 * lip_width,
        lip_height + 0.1,
        f"{prefix}_lid_lip_width",
        f"{prefix}_outer_width - 2 * (mfg_wall + mfg_print_gap + {lip_width} mm)",
        f"{prefix}_lid_lip_height + 0.1 mm",
        z_expression,
    )


def reference_box(
    parent: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    parent_key: str,
    provenance: str,
) -> adsk.fusion.Component:
    component = component_at(parent, name, role="reference", provenance=provenance)
    body = new_box(
        component,
        f"{name}_ENVELOPE_ONLY",
        x,
        y,
        z,
        length,
        width,
        height,
        f"ref_{parent_key}_length",
        f"ref_{parent_key}_width",
        f"ref_{parent_key}_height_envelope",
    )
    body.attributes.add(ATTRIBUTE_GROUP, "ReferenceOnly", "true")
    body.attributes.add(ATTRIBUTE_GROUP, "Provenance", provenance)
    return component


def build_pod(
    root: adsk.fusion.Component, params: dict[str, Any]
) -> list[adsk.fusion.Component]:
    mfg = params["manufacturing"]
    layout = params["layout"]
    pod = params["pod"]
    hardware = params["source_hardware"]
    length = _numeric(pod, "outer_length")
    width = _numeric(pod, "outer_width")
    bottom_height = _numeric(pod, "bottom_height")
    top_height = _numeric(pod, "top_height")
    floor = _numeric(mfg, "floor")
    offset = _numeric(pod, "boss_edge_offset")

    assembly = component_at(
        root,
        "CuePod_Microphone_Module",
        _numeric(layout, "pod_origin_x"),
        _numeric(layout, "pod_origin_y"),
        0.0,
        "assembly",
        "CueLoop original detachable microphone-pod assembly",
    )
    bottom = component_at(
        assembly,
        "CuePod_Bottom",
        role="manufacturing",
        provenance="CueLoop original enclosure geometry",
    )
    open_shell(
        bottom,
        "CuePod_Bottom_Print",
        "pod",
        length,
        width,
        bottom_height,
        "pod_corner_radius",
    )
    cut_box(
        bottom,
        "CuePod_USB_C_Opening",
        length - _numeric(mfg, "wall") - 0.5,
        (width - _numeric(pod, "usb_opening_width")) / 2.0,
        _numeric(pod, "usb_opening_z"),
        _numeric(mfg, "wall") + 1.0,
        _numeric(pod, "usb_opening_width"),
        _numeric(pod, "usb_opening_height"),
        "mfg_wall + 1 mm",
        "pod_usb_opening_width",
        "pod_usb_opening_height",
        "pod_usb_opening_z",
    )
    cut_box(
        bottom,
        "CuePod_Battery_Cable_Opening",
        -0.5,
        (width - _numeric(pod, "cable_opening_width")) / 2.0,
        _numeric(pod, "cable_opening_z"),
        _numeric(mfg, "wall") + 1.0,
        _numeric(pod, "cable_opening_width"),
        _numeric(pod, "cable_opening_height"),
        "mfg_wall + 1 mm",
        "pod_cable_opening_width",
        "pod_cable_opening_height",
        "pod_cable_opening_z",
    )
    for index in range(int(_numeric(pod, "vent_slot_count"))):
        cut_box(
            bottom,
            f"CuePod_Ventilation_Slot_{index + 1}",
            (length - _numeric(pod, "vent_slot_length")) / 2.0,
            -0.5,
            15.0 + index * _numeric(pod, "vent_slot_spacing"),
            _numeric(pod, "vent_slot_length"),
            _numeric(mfg, "wall") + 1.0,
            _numeric(pod, "vent_slot_width"),
            "pod_vent_slot_length",
            "mfg_wall + 1 mm",
            "pod_vent_slot_width",
        )
    locations = screw_locations(length, width, offset)
    add_bosses(bottom, "CuePod", locations, floor, bottom_height - floor - 1.0)

    xiao = hardware["xiao_sense"]
    deck_x = (length - _numeric(xiao, "length")) / 2.0
    deck_y = (width - _numeric(xiao, "width")) / 2.0
    battery = hardware["lipo_500"]
    bridge_z = (
        floor
        + _numeric(pod, "battery_floor_gap")
        + _numeric(battery, "height_envelope")
        + _numeric(pod, "battery_bridge_clearance")
    )
    for index, rail_y in enumerate(
        (
            deck_y + 2.0,
            deck_y + _numeric(xiao, "width") - 4.0,
        ),
        start=1,
    ):
        join_box(
            bottom,
            f"XIAO_Battery_Bridge_Rail_{index}",
            0.0,
            rail_y,
            bridge_z,
            length,
            2.0,
            _numeric(pod, "board_bridge_thickness"),
            "pod_outer_length",
            "2 mm",
            "pod_board_bridge_thickness",
            "mfg_floor + pod_battery_floor_gap + ref_lipo_500_height_envelope + pod_battery_bridge_clearance",
        )

    battery_y = (width - _numeric(battery, "width")) / 2.0
    for index, rail_y in enumerate(
        (
            battery_y - _numeric(pod, "battery_restraint_gap") - 1.4,
            battery_y
            + _numeric(battery, "width")
            + _numeric(pod, "battery_restraint_gap"),
        ),
        start=1,
    ):
        join_box(
            bottom,
            f"LiPo_Noncompressive_Rail_{index}",
            (length - _numeric(battery, "length")) / 2.0,
            rail_y,
            floor - 0.1,
            _numeric(battery, "length"),
            1.4,
            _numeric(pod, "battery_rail_height") + 0.1,
            "ref_lipo_500_length",
            "1.4 mm",
            "pod_battery_rail_height + 0.1 mm",
        )

    tongue_x = (length - _numeric(pod, "dock_tongue_length")) / 2.0
    tongue_y = (width - _numeric(pod, "dock_tongue_width")) / 2.0
    join_box(
        bottom,
        "CuePod_Dock_Tongue",
        tongue_x,
        tongue_y,
        -_numeric(pod, "dock_tongue_height"),
        _numeric(pod, "dock_tongue_length"),
        _numeric(pod, "dock_tongue_width"),
        _numeric(pod, "dock_tongue_height") + 0.1,
        "pod_dock_tongue_length",
        "pod_dock_tongue_width",
        "pod_dock_tongue_height + 0.1 mm",
        "-pod_dock_tongue_height",
    )
    join_box(
        bottom,
        "CuePod_Dock_Latch_Tab",
        (length - _numeric(pod, "dock_latch_width")) / 2.0,
        tongue_y - _numeric(pod, "dock_latch_depth"),
        -_numeric(pod, "dock_tongue_height"),
        _numeric(pod, "dock_latch_width"),
        _numeric(pod, "dock_latch_depth") + 0.1,
        _numeric(pod, "dock_tongue_height"),
        "pod_dock_latch_width",
        "pod_dock_latch_depth + 0.1 mm",
        "pod_dock_tongue_height",
        "-pod_dock_tongue_height",
    )

    top = component_at(
        assembly,
        "CuePod_Top",
        0.0,
        0.0,
        bottom_height + _numeric(layout, "exploded_gap"),
        "manufacturing",
        "CueLoop original enclosure geometry",
    )
    new_box(
        top,
        "CuePod_Top_Print",
        0.0,
        0.0,
        0.0,
        length,
        width,
        top_height,
        "pod_outer_length",
        "pod_outer_width",
        "pod_top_height",
        radius_expression="pod_corner_radius",
    )
    add_lid_fastener_holes(top, "CuePod", locations, top_height)
    add_lid_lip(
        top,
        "pod",
        length,
        width,
        _numeric(pod, "lid_lip_height"),
        _numeric(pod, "lid_lip_width"),
    )
    mic_x = _numeric(pod, "mic_center_x")
    mic_y = _numeric(pod, "mic_center_y")
    mic_points = [(mic_x, mic_y)]
    for index in range(6):
        angle = index * math.pi / 3.0
        mic_points.append(
            (
                mic_x + _numeric(pod, "mic_ring_radius") * math.cos(angle),
                mic_y + _numeric(pod, "mic_ring_radius") * math.sin(angle),
            )
        )
    for index, (x, y) in enumerate(mic_points, start=1):
        cut_cylinder(
            top,
            f"Microphone_Acoustic_Port_{index}",
            x,
            y,
            -_numeric(pod, "lid_lip_height") - 0.1,
            _numeric(pod, "mic_hole_diameter"),
            top_height + _numeric(pod, "lid_lip_height") + 0.2,
            "pod_mic_hole_diameter",
            "pod_top_height + pod_lid_lip_height + 0.2 mm",
        )

    battery_x = (length - _numeric(battery, "length")) / 2.0
    reference_battery = reference_box(
        assembly,
        "Reference_LiPo_500mAh",
        battery_x,
        battery_y,
        floor + _numeric(pod, "battery_floor_gap"),
        _numeric(battery, "length"),
        _numeric(battery, "width"),
        _numeric(battery, "height_envelope"),
        "lipo_500",
        str(battery["geometry_policy"]),
    )
    reference_xiao = reference_box(
        assembly,
        "Reference_XIAO_Sense",
        deck_x,
        deck_y,
        floor
        + _numeric(pod, "board_standoff_height")
        + _numeric(pod, "board_support_clearance"),
        _numeric(xiao, "length"),
        _numeric(xiao, "width"),
        _numeric(xiao, "height_envelope"),
        "xiao_sense",
        str(xiao["geometry_policy"]),
    )
    microphone = hardware["microphone_cartridge"]
    reference_microphone = reference_box(
        assembly,
        "Reference_Microphone_Cartridge",
        (length - _numeric(microphone, "length")) / 2.0,
        (width - _numeric(microphone, "width")) / 2.0,
        bottom_height
        - _numeric(microphone, "height_envelope")
        - _numeric(pod, "microphone_top_gap"),
        _numeric(microphone, "length"),
        _numeric(microphone, "width"),
        _numeric(microphone, "height_envelope"),
        "microphone_cartridge",
        str(microphone["geometry_policy"]),
    )
    return [
        assembly,
        bottom,
        top,
        reference_battery,
        reference_xiao,
        reference_microphone,
    ]


def build_receiver(
    root: adsk.fusion.Component, params: dict[str, Any]
) -> list[adsk.fusion.Component]:
    mfg = params["manufacturing"]
    layout = params["layout"]
    receiver = params["receiver"]
    hardware = params["source_hardware"]
    length = _numeric(receiver, "outer_length")
    width = _numeric(receiver, "outer_width")
    bottom_height = _numeric(receiver, "bottom_height")
    top_height = _numeric(receiver, "top_height")
    floor = _numeric(mfg, "floor")
    offset = _numeric(mfg, "boss_edge_offset")

    assembly = component_at(
        root,
        "Receiver_Assembly",
        _numeric(layout, "receiver_origin_x"),
        _numeric(layout, "receiver_origin_y"),
        0.0,
        "assembly",
        "CueLoop original portable receiver assembly",
    )
    bottom = component_at(
        assembly,
        "Receiver_Bottom",
        role="manufacturing",
        provenance="CueLoop original enclosure geometry",
    )
    open_shell(
        bottom,
        "Receiver_Bottom_Print",
        "receiver",
        length,
        width,
        bottom_height,
        "receiver_corner_radius",
    )
    cut_box(
        bottom,
        "Receiver_USB_C_Power_Opening",
        length - _numeric(mfg, "wall") - 0.5,
        14.0,
        _numeric(receiver, "usb_power_opening_z"),
        _numeric(mfg, "wall") + 1.0,
        _numeric(receiver, "usb_power_opening_width"),
        _numeric(receiver, "usb_power_opening_height"),
        "mfg_wall + 1 mm",
        "receiver_usb_power_opening_width",
        "receiver_usb_power_opening_height",
        "receiver_usb_power_opening_z",
    )
    cut_box(
        bottom,
        "Receiver_Accessory_Cable_Opening",
        -0.5,
        62.0,
        _numeric(receiver, "cable_opening_z"),
        _numeric(mfg, "wall") + 1.0,
        _numeric(receiver, "cable_opening_width"),
        _numeric(receiver, "cable_opening_height"),
        "mfg_wall + 1 mm",
        "receiver_cable_opening_width",
        "receiver_cable_opening_height",
        "receiver_cable_opening_z",
    )
    for index in range(int(_numeric(receiver, "vent_slot_count"))):
        cut_box(
            bottom,
            f"Receiver_Ventilation_Slot_{index + 1}",
            10.0 + index * _numeric(receiver, "vent_slot_spacing"),
            width - _numeric(mfg, "wall") - 0.5,
            17.0,
            _numeric(receiver, "vent_slot_width"),
            _numeric(mfg, "wall") + 1.0,
            _numeric(receiver, "vent_slot_length"),
            "receiver_vent_slot_width",
            "mfg_wall + 1 mm",
            "receiver_vent_slot_length",
        )
    locations = screw_locations(length, width, offset)
    add_bosses(bottom, "Receiver", locations, floor, bottom_height - floor - 1.0)

    uno = hardware["uno_q"]
    uno_x = _numeric(receiver, "uno_origin_x")
    uno_y = _numeric(receiver, "uno_origin_y")
    for index, (x, y) in enumerate(
        (
            (uno_x + 3.0, uno_y + 3.0),
            (uno_x + _numeric(uno, "length") - 3.0, uno_y + 3.0),
            (
                uno_x + _numeric(uno, "length") - 3.0,
                uno_y + _numeric(uno, "width") - 3.0,
            ),
            (uno_x + 3.0, uno_y + _numeric(uno, "width") - 3.0),
        ),
        start=1,
    ):
        join_cylinder(
            bottom,
            f"UNO_Q_Outline_Support_{index}",
            x,
            y,
            floor - 0.1,
            _numeric(receiver, "uno_support_diameter"),
            _numeric(receiver, "uno_standoff_height") + 0.1,
            "receiver_uno_support_diameter",
            "receiver_uno_standoff_height + 0.1 mm",
        )

    top = component_at(
        assembly,
        "Receiver_Top",
        0.0,
        0.0,
        bottom_height + _numeric(layout, "exploded_gap"),
        "manufacturing",
        "CueLoop original enclosure geometry",
    )
    new_box(
        top,
        "Receiver_Top_Print",
        0.0,
        0.0,
        0.0,
        length,
        width,
        top_height,
        "receiver_outer_length",
        "receiver_outer_width",
        "receiver_top_height",
        radius_expression="receiver_corner_radius",
    )
    add_lid_fastener_holes(top, "Receiver", locations, top_height)
    add_lid_lip(
        top,
        "receiver",
        length,
        width,
        _numeric(receiver, "lid_lip_height"),
        _numeric(receiver, "lid_lip_width"),
    )
    cut_box(
        top,
        "Receiver_Alert_LED_Window",
        _numeric(receiver, "light_window_x"),
        _numeric(receiver, "light_window_y"),
        -_numeric(receiver, "lid_lip_height") - 0.1,
        _numeric(receiver, "light_window_length"),
        _numeric(receiver, "light_window_width"),
        top_height + _numeric(receiver, "lid_lip_height") + 0.2,
        "receiver_light_window_length",
        "receiver_light_window_width",
        "receiver_top_height + receiver_lid_lip_height + 0.2 mm",
    )
    cut_box(
        top,
        "CuePod_Dock_Pocket",
        _numeric(receiver, "dock_pocket_x"),
        _numeric(receiver, "dock_pocket_y"),
        top_height - _numeric(receiver, "dock_pocket_depth"),
        _numeric(receiver, "dock_pocket_length"),
        _numeric(receiver, "dock_pocket_width"),
        _numeric(receiver, "dock_pocket_depth") + 0.2,
        "receiver_dock_pocket_length",
        "receiver_dock_pocket_width",
        "receiver_dock_pocket_depth + 0.2 mm",
        "receiver_top_height - receiver_dock_pocket_depth",
    )
    dock_x = _numeric(receiver, "dock_pocket_x")
    dock_y = _numeric(receiver, "dock_pocket_y")
    dock_length = _numeric(receiver, "dock_pocket_length")
    dock_width = _numeric(receiver, "dock_pocket_width")
    rail_width = _numeric(receiver, "dock_rail_width")
    for index, rail_x in enumerate((dock_x - rail_width, dock_x + dock_length), start=1):
        join_box(
            top,
            f"CuePod_Dock_Rail_{index}",
            rail_x,
            dock_y + 4.0,
            top_height - 0.1,
            rail_width,
            dock_width - 8.0,
            _numeric(receiver, "dock_rail_height") + 0.1,
            "receiver_dock_rail_width",
            "receiver_dock_pocket_width - 8 mm",
            "receiver_dock_rail_height + 0.1 mm",
            "receiver_top_height - 0.1 mm",
        )
    button_center = length / 2.0
    button_spacing = _numeric(receiver, "button_spacing")
    for index, x in enumerate(
        (button_center - button_spacing, button_center, button_center + button_spacing),
        start=1,
    ):
        cut_cylinder(
            top,
            f"Receiver_Button_Opening_{index}",
            x,
            _numeric(receiver, "button_center_y"),
            -_numeric(receiver, "lid_lip_height") - 0.1,
            _numeric(receiver, "button_diameter"),
            top_height + _numeric(receiver, "lid_lip_height") + 0.2,
            "receiver_button_diameter",
            "receiver_top_height + receiver_lid_lip_height + 0.2 mm",
        )

    clip = component_at(
        assembly,
        "Receiver_Carry_Clip",
        (length - _numeric(receiver, "clip_length")) / 2.0,
        width + _numeric(layout, "clip_exploded_gap"),
        0.0,
        "manufacturing",
        "CueLoop original clip/carry geometry",
    )
    new_box(
        clip,
        "Receiver_Carry_Clip_Print",
        0.0,
        0.0,
        0.0,
        _numeric(receiver, "clip_length"),
        _numeric(receiver, "clip_width"),
        _numeric(receiver, "clip_thickness"),
        "receiver_clip_length",
        "receiver_clip_width",
        "receiver_clip_thickness",
        radius_expression="mfg_edge_radius",
    )
    arm_x = (_numeric(receiver, "clip_length") - _numeric(receiver, "clip_arm_length")) / 2.0
    join_box(
        clip,
        "Clip_Root_Bridge",
        arm_x - _numeric(mfg, "snap_root_thickness"),
        3.0,
        _numeric(receiver, "clip_thickness") - 0.1,
        _numeric(mfg, "snap_root_thickness") + 0.2,
        _numeric(receiver, "clip_width") - 6.0,
        _numeric(receiver, "clip_gap") + _numeric(receiver, "clip_thickness") + 0.2,
        "mfg_snap_root_thickness + 0.2 mm",
        "receiver_clip_width - 6 mm",
        "receiver_clip_gap + receiver_clip_thickness + 0.2 mm",
        "receiver_clip_thickness - 0.1 mm",
    )
    join_box(
        clip,
        "Clip_Flex_Arm",
        arm_x,
        3.0,
        _numeric(receiver, "clip_thickness") + _numeric(receiver, "clip_gap"),
        _numeric(receiver, "clip_arm_length"),
        _numeric(receiver, "clip_width") - 6.0,
        _numeric(receiver, "clip_thickness"),
        "receiver_clip_arm_length",
        "receiver_clip_width - 6 mm",
        "receiver_clip_thickness",
        "receiver_clip_thickness + receiver_clip_gap",
    )
    join_box(
        clip,
        "Clip_Lead_In_Foot",
        arm_x + _numeric(receiver, "clip_arm_length") - 3.0,
        3.0,
        _numeric(receiver, "clip_thickness") + _numeric(receiver, "clip_gap"),
        3.0,
        _numeric(receiver, "clip_width") - 6.0,
        _numeric(receiver, "clip_foot_height"),
        "3 mm",
        "receiver_clip_width - 6 mm",
        "receiver_clip_foot_height",
        "receiver_clip_thickness + receiver_clip_gap",
    )

    diffuser = component_at(
        assembly,
        "Alert_Diffuser",
        _numeric(receiver, "light_window_x"),
        _numeric(receiver, "light_window_y") + 0.3,
        bottom_height + _numeric(layout, "exploded_gap") + 0.4,
        "manufacturing",
        "CueLoop original optical envelope; optical performance unvalidated",
    )
    new_box(
        diffuser,
        "Alert_Diffuser_Print",
        0.0,
        0.0,
        0.0,
        _numeric(receiver, "light_window_length"),
        _numeric(receiver, "light_window_width") - 0.6,
        1.8,
        "receiver_light_window_length",
        "receiver_light_window_width - 0.6 mm",
        "1.8 mm",
        radius_expression="1.2 mm",
    )

    reference_uno = reference_box(
        assembly,
        "Reference_UNO_Q",
        _numeric(receiver, "uno_origin_x"),
        _numeric(receiver, "uno_origin_y"),
        floor + _numeric(receiver, "uno_standoff_height") + 0.2,
        _numeric(uno, "length"),
        _numeric(uno, "width"),
        _numeric(uno, "height_envelope"),
        "uno_q",
        str(uno["geometry_policy"]),
    )
    support = hardware["support_electronics"]
    reference_support = reference_box(
        assembly,
        "Reference_Support_Electronics",
        _numeric(receiver, "support_origin_x"),
        _numeric(receiver, "support_origin_y"),
        floor + 0.5,
        _numeric(support, "length"),
        _numeric(support, "width"),
        _numeric(support, "height_envelope"),
        "support_electronics",
        str(support["geometry_policy"]),
    )
    haptic = hardware["haptic_led_module"]
    reference_haptic = reference_box(
        assembly,
        "Reference_Haptic_LED_Module",
        _numeric(receiver, "haptic_origin_x"),
        _numeric(receiver, "haptic_origin_y"),
        floor + 0.5,
        _numeric(haptic, "length"),
        _numeric(haptic, "width"),
        _numeric(haptic, "height_envelope"),
        "haptic_led_module",
        str(haptic["geometry_policy"]),
    )
    return [
        assembly,
        bottom,
        top,
        clip,
        diffuser,
        reference_uno,
        reference_support,
        reference_haptic,
    ]


def _all_components(design: adsk.fusion.Design) -> list[adsk.fusion.Component]:
    return [design.allComponents.item(index) for index in range(design.allComponents.count)]


def component_by_name(
    design: adsk.fusion.Design, name: str
) -> adsk.fusion.Component | None:
    for component in _all_components(design):
        if component.name == name:
            return component
    return None


def model_statistics(design: adsk.fusion.Design) -> dict[str, Any]:
    components = _all_components(design)
    component_records: list[dict[str, Any]] = []
    body_count = 0
    sketch_count = 0
    feature_count = 0
    for component in components:
        bodies = component.bRepBodies.count
        sketches = component.sketches.count
        features = component.features.count
        body_count += bodies
        sketch_count += sketches
        feature_count += features
        body_records: list[dict[str, Any]] = []
        for index in range(bodies):
            body = component.bRepBodies.item(index)
            bounds = body.boundingBox
            body_records.append(
                {
                    "name": body.name,
                    "solid": bool(body.isSolid),
                    "bounds_mm": {
                        "length_x": (bounds.maxPoint.x - bounds.minPoint.x) * 10.0,
                        "length_y": (bounds.maxPoint.y - bounds.minPoint.y) * 10.0,
                        "length_z": (bounds.maxPoint.z - bounds.minPoint.z) * 10.0,
                    },
                }
            )
        component_records.append(
            {
                "name": component.name,
                "role": (
                    component.attributes.itemByName(ATTRIBUTE_GROUP, "Role").value
                    if component.attributes.itemByName(ATTRIBUTE_GROUP, "Role")
                    else "root"
                ),
                "bodies": body_records,
                "sketch_count": sketches,
                "feature_count": features,
            }
        )
    return {
        "component_count_including_root": len(components),
        "solid_body_count": body_count,
        "sketch_count": sketch_count,
        "feature_count": feature_count,
        "timeline_count": design.timeline.count,
        "user_parameter_count": design.userParameters.count,
        "components": component_records,
    }


def validate_native_model(
    design: adsk.fusion.Design,
    contract: dict[str, Any],
    analytic_checks: dict[str, Any],
) -> dict[str, Any]:
    stats = model_statistics(design)
    errors: list[str] = []
    minimum = contract["minimum_counts"]
    count_map = {
        "components_including_root": stats["component_count_including_root"],
        "solid_bodies": stats["solid_body_count"],
        "native_sketches": stats["sketch_count"],
        "native_features": stats["feature_count"],
        "timeline_entries": stats["timeline_count"],
        "user_parameters": stats["user_parameter_count"],
    }
    for name, required in minimum.items():
        actual = count_map[name]
        if actual < required:
            errors.append(f"{name}: expected at least {required}, found {actual}")

    for specification in contract["components"]:
        component = component_by_name(design, specification["name"])
        if component is None:
            errors.append(f"missing component: {specification['name']}")
            continue
        if specification["role"] in ("manufacturing", "reference"):
            if component.bRepBodies.count != 1:
                errors.append(
                    f"{specification['name']} must contain exactly one final body; "
                    f"found {component.bRepBodies.count}"
                )
            elif not component.bRepBodies.item(0).isSolid:
                errors.append(f"{specification['name']} final body is not solid")

    result = {
        "schema_version": 1,
        "generator_version": SCRIPT_VERSION,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "analytic_clearance_checks": analytic_checks,
        "statistics": stats,
        "claim_boundary": (
            "Native-model structural validation only. It does not establish physical "
            "fit, latch force, optical/acoustic performance, RF, thermal safety, or DFM approval."
        ),
    }
    if errors:
        raise RuntimeError("Native model validation failed: " + "; ".join(errors))
    return result


def _write_json(path: str, value: Any) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _bom_rows(params: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"item": "Printed CuePod bottom", "qty": "1", "source": "CueLoop original", "part": "CuePod_Bottom", "status": "generated; physical validation pending"},
        {"item": "Printed CuePod top", "qty": "1", "source": "CueLoop original", "part": "CuePod_Top", "status": "generated; physical validation pending"},
        {"item": "Printed receiver bottom", "qty": "1", "source": "CueLoop original", "part": "Receiver_Bottom", "status": "generated; physical validation pending"},
        {"item": "Printed receiver top", "qty": "1", "source": "CueLoop original", "part": "Receiver_Top", "status": "generated; physical validation pending"},
        {"item": "Printed carry clip", "qty": "1", "source": "CueLoop original", "part": "Receiver_Carry_Clip", "status": "generated; flex/force validation pending"},
        {"item": "Printed optical diffuser", "qty": "1", "source": "CueLoop original", "part": "Alert_Diffuser", "status": "generated; material/optics validation pending"},
        {"item": "Arduino UNO Q 4GB/32GB", "qty": "1", "source": params["source_hardware"]["uno_q"]["source_url"], "part": "ABX00173", "status": "vendor placement envelope only"},
        {"item": "Seeed XIAO ESP32S3 Sense", "qty": "1", "source": params["source_hardware"]["xiao_sense"]["source_url"], "part": "113991115", "status": "vendor placement envelope only"},
        {"item": "Adafruit protected LiPo 500mAh", "qty": "1", "source": params["source_hardware"]["lipo_500"]["source_url"], "part": "1578", "status": "vendor placement envelope only; battery safety unproven"},
        {"item": "M2 enclosure fasteners", "qty": "8", "source": "TBD after physical validation", "part": "M2", "status": "hole/boss strategy generated; exact length/material TBD"},
        {"item": "Support/output electronics", "qty": "TBD", "source": "No vendor selected", "part": "reserved envelopes", "status": "not a purchased part and not essential to V1"},
    ]


def _execute_export(
    export_manager: adsk.fusion.ExportManager,
    options: adsk.fusion.ExportOptions,
    expected_path: str,
) -> None:
    if os.path.exists(expected_path):
        os.remove(expected_path)
    if not export_manager.execute(options):
        raise RuntimeError(f"Fusion export failed: {expected_path}")
    if not os.path.isfile(expected_path) or os.path.getsize(expected_path) == 0:
        raise RuntimeError(f"Fusion export produced no file: {expected_path}")


def snapshot_authoritative_sources(output_dir: str) -> list[str]:
    """Copy exact inputs into the export and emit a digest provenance record."""

    sources_dir = os.path.join(output_dir, "sources")
    os.makedirs(sources_dir, exist_ok=True)
    source_paths = (
        ("fusion_generator", os.path.abspath(__file__), "CueLoopBridgeGenerator.py"),
        ("design_parameters", _required_path("design_parameters.json"), "design_parameters.json"),
        ("design_contract", _required_path("design_contract.json"), "design_contract.json"),
    )
    copied: list[str] = []
    records: list[dict[str, Any]] = []
    for role, source, filename in source_paths:
        target = os.path.join(sources_dir, filename)
        with open(source, "rb") as source_handle:
            payload = source_handle.read()
        with open(target, "wb") as target_handle:
            target_handle.write(payload)
        records.append(
            {
                "role": role,
                "path": "sources/" + filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
            }
        )
        copied.append(target)

    manifest_path = os.path.join(output_dir, "CueLoop_Bridge_source_manifest.json")
    _write_json(
        manifest_path,
        {
            "schema_version": 1,
            "authoritative": True,
            "generator_version": SCRIPT_VERSION,
            "model_creation": (
                "Native Autodesk Fusion API sketches and features; no imported "
                "mesh, STEP, BRep, or completed base geometry."
            ),
            "sources": records,
        },
    )
    return copied + [manifest_path]


def export_native_outputs(
    design: adsk.fusion.Design,
    params: dict[str, Any],
    contract: dict[str, Any],
    validation: dict[str, Any],
    parameter_records: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    output_dir = os.path.join(
        _source_directory(), "exports", OUTPUT_DIRECTORY_NAME
    )
    manufacturing_dir = os.path.join(output_dir, "manufacturing")
    os.makedirs(manufacturing_dir, exist_ok=True)
    export_manager = design.exportManager
    root = design.rootComponent
    output_files: list[str] = []
    output_files.extend(snapshot_authoritative_sources(output_dir))

    archive_path = os.path.join(output_dir, "CueLoop_Bridge_Native.f3d")
    archive_options = export_manager.createFusionArchiveExportOptions(
        archive_path, root
    )
    _execute_export(export_manager, archive_options, archive_path)
    output_files.append(archive_path)

    assembly_step = os.path.join(output_dir, "CueLoop_Bridge_Native.step")
    step_options = export_manager.createSTEPExportOptions(assembly_step, root)
    _execute_export(export_manager, step_options, assembly_step)
    output_files.append(assembly_step)

    for specification in contract["components"]:
        if not specification.get("manufacturing_export"):
            continue
        component = component_by_name(design, specification["name"])
        if component is None:
            raise RuntimeError(f"Cannot export missing component {specification['name']}")
        stem = specification["output_stem"]

        component_step = os.path.join(manufacturing_dir, stem + ".step")
        component_step_options = export_manager.createSTEPExportOptions(
            component_step, component
        )
        _execute_export(export_manager, component_step_options, component_step)
        output_files.append(component_step)

        component_stl = os.path.join(manufacturing_dir, stem + ".stl")
        stl_options = export_manager.createSTLExportOptions(component, component_stl)
        stl_options.isBinaryFormat = True
        stl_options.meshRefinement = (
            adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        )
        stl_options.surfaceDeviation = mm(
            _numeric(params["manufacturing"], "mesh_surface_deviation")
        )
        stl_options.maximumEdgeLength = mm(
            _numeric(params["manufacturing"], "mesh_max_edge")
        )
        stl_options.sendToPrintUtility = False
        _execute_export(export_manager, stl_options, component_stl)
        output_files.append(component_stl)

        component_3mf = os.path.join(manufacturing_dir, stem + ".3mf")
        mesh_options = export_manager.createC3MFExportOptions(
            component, component_3mf
        )
        mesh_options.meshRefinement = (
            adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        )
        mesh_options.surfaceDeviation = mm(
            _numeric(params["manufacturing"], "mesh_surface_deviation")
        )
        mesh_options.maximumEdgeLength = mm(
            _numeric(params["manufacturing"], "mesh_max_edge")
        )
        mesh_options.sendToPrintUtility = False
        _execute_export(export_manager, mesh_options, component_3mf)
        output_files.append(component_3mf)

    parameter_path = os.path.join(output_dir, "CueLoop_Bridge_parameters.json")
    actual_parameters: list[dict[str, Any]] = []
    for record in parameter_records:
        user_parameter = design.userParameters.itemByName(record["name"])
        actual_parameters.append(
            {
                **record,
                "fusion_expression": user_parameter.expression,
                "fusion_internal_value": user_parameter.value,
            }
        )
    _write_json(
        parameter_path,
        {
            "schema_version": 1,
            "design_version": params["design_version"],
            "generator_version": SCRIPT_VERSION,
            "parameters": actual_parameters,
        },
    )
    output_files.append(parameter_path)

    bom_rows = _bom_rows(params)
    bom_json = os.path.join(output_dir, "CueLoop_Bridge_BOM.json")
    _write_json(
        bom_json,
        {
            "schema_version": 1,
            "design_version": params["design_version"],
            "claim_boundary": "Reference envelopes are not original vendor geometry or fit evidence.",
            "items": bom_rows,
        },
    )
    output_files.append(bom_json)
    bom_csv = os.path.join(output_dir, "CueLoop_Bridge_BOM.csv")
    with open(bom_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=("item", "qty", "source", "part", "status")
        )
        writer.writeheader()
        writer.writerows(bom_rows)
    output_files.append(bom_csv)

    validation_path = os.path.join(output_dir, "CueLoop_Bridge_validation.json")
    _write_json(validation_path, validation)
    output_files.append(validation_path)

    readme_path = os.path.join(output_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "CueLoop Bridge Native v2 Fusion export\n"
            "Authoritative model: CueLoop_Bridge_Native.f3d\n"
            "The F3D must show native components, sketches, features, timeline, and named parameters.\n"
            "Vendor/reference envelopes are marked and are not original board geometry.\n"
            "Manufacturing files require visual, dimensional, physical-fit, and PCBWay DFM review.\n"
        )
    output_files.append(readme_path)

    checksum_path = os.path.join(output_dir, "SHA256SUMS.txt")
    with open(checksum_path, "w", encoding="utf-8", newline="\n") as handle:
        for path in sorted(output_files):
            digest = hashlib.sha256()
            with open(path, "rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            handle.write(
                f"{digest.hexdigest()}  {os.path.relpath(path, output_dir).replace(os.sep, '/')}\n"
            )
    output_files.append(checksum_path)
    return output_dir, output_files


def run(_context: Any) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        params, contract = load_sources()
        analytic_checks = validate_parameter_geometry(params)

        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError("Fusion did not create an active Design product")
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = (
            adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        )
        root = design.rootComponent
        root.name = ROOT_NAME
        root.partNumber = "CUELOOP-BRIDGE-NATIVE-V2"
        root.attributes.add(ATTRIBUTE_GROUP, "Evidence", VALIDATION_ATTRIBUTE)
        root.attributes.add(ATTRIBUTE_GROUP, "GeneratorVersion", SCRIPT_VERSION)
        root.attributes.add(
            ATTRIBUTE_GROUP,
            "AuthoritativeModel",
            "Native Fusion API sketches/features; no imported completed geometry",
        )

        parameter_records = add_user_parameters(design, params)
        build_pod(root, params)
        build_receiver(root, params)
        validation = validate_native_model(design, contract, analytic_checks)
        root.attributes.add(ATTRIBUTE_GROUP, "ValidationStatus", validation["status"])
        output_dir, output_files = export_native_outputs(
            design,
            params,
            contract,
            validation,
            parameter_records,
        )

        app.activeViewport.fit()
        ui.messageBox(
            "CueLoop Bridge native parametric model created and exported.\n\n"
            f"Validation: PASS\n"
            f"Components including root: {validation['statistics']['component_count_including_root']}\n"
            f"Solid bodies: {validation['statistics']['solid_body_count']}\n"
            f"Timeline entries: {validation['statistics']['timeline_count']}\n"
            f"User parameters: {validation['statistics']['user_parameter_count']}\n"
            f"Files exported: {len(output_files)}\n\n"
            f"Output directory:\n{output_dir}\n\n"
            "The model still requires the documented visual inspection, physical "
            "dimension/fit checks, and PCBWay DFM review before manufacture.",
            "CueLoop Bridge Native Generator",
        )
    except Exception:
        ui.messageBox(
            "CueLoop Bridge native generator failed. No physical/manufacturing "
            "claim may be made from a partial output.\n\n"
            + traceback.format_exc(),
            "CueLoop Bridge Generator Error",
        )


def stop(_context: Any) -> None:
    """Fusion script stop hook; the generated document remains open."""
