"""Generate the preliminary CueLoop Bridge Fusion assembly.

This Autodesk Fusion script creates editable concept solids from the sibling
``design_parameters.json``. All geometry uses Fusion's internal centimeter
units through the ``mm`` conversion helper. Dimensions are preliminary until
the physical validation checklist is complete.
"""

from __future__ import annotations

import json
import math
import os
import traceback
from typing import Any

import adsk.core
import adsk.fusion


DEFAULT_PARAMETERS: dict[str, Any] = {
    "global": {
        "wall": 2.0,
        "floor": 2.0,
        "lid": 2.4,
        "edge_radius": 3.5,
        "m2_clearance_diameter": 2.4,
        "m2_boss_diameter": 5.5,
        "boss_edge_offset": 5.0,
        "exploded_gap": 7.0,
    },
    "source_hardware": {
        "uno_q": {"length": 68.85, "width": 53.34, "height_envelope": 18.0},
        "xiao_sense": {"length": 21.0, "width": 17.8, "height": 15.0},
        "lipo_500": {"length": 36.0, "width": 29.0, "height": 4.75},
    },
    "pod": {
        "outer_length": 46.0,
        "outer_width": 40.0,
        "base_height": 24.0,
        "lid_height": 2.4,
        "corner_radius": 4.0,
        "mic_center_x": 23.0,
        "mic_center_y": 20.0,
        "mic_hole_diameter": 1.8,
        "mic_ring_radius": 4.5,
        "usb_opening_width": 11.0,
        "usb_opening_height": 5.5,
        "usb_opening_z": 8.0,
        "board_standoff_height": 7.0,
    },
    "receiver": {
        "outer_length": 102.0,
        "outer_width": 78.0,
        "base_height": 29.0,
        "lid_height": 3.0,
        "corner_radius": 6.0,
        "uno_standoff_height": 4.0,
        "light_window_length": 76.0,
        "light_window_height": 10.0,
        "light_window_z": 10.0,
        "dock_length": 48.0,
        "dock_width": 42.0,
        "dock_depth": 1.2,
        "button_diameter": 12.0,
        "clip_length": 62.0,
        "clip_width": 20.0,
        "clip_thickness": 3.0,
        "clip_gap": 4.0,
    },
}


def mm(value: float) -> float:
    """Convert millimeters to Fusion internal centimeters."""

    return float(value) / 10.0


def load_parameters() -> dict[str, Any]:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = (
        os.path.join(here, "design_parameters.json"),
        os.path.join(os.path.dirname(here), "design_parameters.json"),
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as handle:
                return json.load(handle)
    return DEFAULT_PARAMETERS


def point(x: float, y: float, z: float = 0.0) -> adsk.core.Point3D:
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def component_at(
    parent: adsk.fusion.Component,
    name: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> adsk.fusion.Component:
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(mm(x), mm(y), mm(z))
    occurrence = parent.occurrences.addNewComponent(transform)
    occurrence.component.name = name
    return occurrence.component


def plane_at(component: adsk.fusion.Component, z: float) -> adsk.core.Base:
    if abs(z) < 1e-9:
        return component.xYConstructionPlane
    planes = component.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(
        component.xYConstructionPlane,
        adsk.core.ValueInput.createByReal(mm(z)),
    )
    plane = planes.add(plane_input)
    plane.name = f"Offset_{z:.2f}_mm"
    return plane


def fillet_vertical_edges(
    component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    radius: float,
) -> None:
    if radius <= 0:
        return
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        start = edge.startVertex.geometry
        end = edge.endVertex.geometry
        mostly_vertical = (
            abs(start.x - end.x) < mm(0.05)
            and abs(start.y - end.y) < mm(0.05)
            and abs(start.z - end.z) > mm(0.1)
        )
        if mostly_vertical:
            edges.add(edge)
    if edges.count == 0:
        return
    try:
        feature_input = component.features.filletFeatures.createInput()
        feature_input.addConstantRadiusEdgeSet(
            edges,
            adsk.core.ValueInput.createByReal(mm(radius)),
            True,
        )
        component.features.filletFeatures.add(feature_input)
    except RuntimeError:
        # A valid unfilleted solid is preferable to aborting the whole script.
        pass


def box_body(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    radius: float = 0.0,
) -> adsk.fusion.BRepBody:
    sketch = component.sketches.add(plane_at(component, z))
    sketch.name = f"{name}_Profile"
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        point(x, y),
        point(x + length, y + width),
    )
    profile = sketch.profiles.item(0)
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    extrude_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm(height)),
    )
    feature = extrudes.add(extrude_input)
    feature.name = f"{name}_Extrude"
    body = feature.bodies.item(0)
    body.name = name
    fillet_vertical_edges(component, body, min(radius, length / 2.1, width / 2.1))
    return body


def cylinder_body(
    component: adsk.fusion.Component,
    name: str,
    x: float,
    y: float,
    z: float,
    diameter: float,
    height: float,
) -> adsk.fusion.BRepBody:
    sketch = component.sketches.add(plane_at(component, z))
    sketch.name = f"{name}_Profile"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(x, y),
        mm(diameter / 2.0),
    )
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(
        sketch.profiles.item(0),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    extrude_input.setDistanceExtent(
        False,
        adsk.core.ValueInput.createByReal(mm(height)),
    )
    feature = extrudes.add(extrude_input)
    feature.name = f"{name}_Extrude"
    body = feature.bodies.item(0)
    body.name = name
    return body


def cut_body(
    component: adsk.fusion.Component,
    target: adsk.fusion.BRepBody,
    tool: adsk.fusion.BRepBody,
    name: str,
) -> None:
    tools = adsk.core.ObjectCollection.create()
    tools.add(tool)
    combine_input = component.features.combineFeatures.createInput(target, tools)
    combine_input.operation = adsk.fusion.FeatureOperations.CutFeatureOperation
    combine_input.isKeepToolBodies = False
    feature = component.features.combineFeatures.add(combine_input)
    feature.name = name


def cut_box(
    component: adsk.fusion.Component,
    target: adsk.fusion.BRepBody,
    name: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    radius: float = 0.0,
) -> None:
    tool = box_body(
        component,
        f"{name}_Tool",
        x,
        y,
        z,
        length,
        width,
        height,
        radius,
    )
    cut_body(component, target, tool, name)


def cut_cylinder(
    component: adsk.fusion.Component,
    target: adsk.fusion.BRepBody,
    name: str,
    x: float,
    y: float,
    z: float,
    diameter: float,
    height: float,
) -> None:
    tool = cylinder_body(
        component,
        f"{name}_Tool",
        x,
        y,
        z,
        diameter,
        height,
    )
    cut_body(component, target, tool, name)


def open_shell(
    component: adsk.fusion.Component,
    name: str,
    length: float,
    width: float,
    height: float,
    wall: float,
    floor: float,
    radius: float,
) -> adsk.fusion.BRepBody:
    outer = box_body(
        component,
        name,
        0,
        0,
        0,
        length,
        width,
        height,
        radius,
    )
    cavity = box_body(
        component,
        f"{name}_Cavity_Tool",
        wall,
        wall,
        floor,
        length - 2 * wall,
        width - 2 * wall,
        height - floor + 0.5,
        max(0.5, radius - wall),
    )
    cut_body(component, outer, cavity, f"{name}_Cavity")
    return outer


def screw_locations(length: float, width: float, offset: float) -> list[tuple[float, float]]:
    return [
        (offset, offset),
        (length - offset, offset),
        (length - offset, width - offset),
        (offset, width - offset),
    ]


def add_bosses(
    component: adsk.fusion.Component,
    prefix: str,
    locations: list[tuple[float, float]],
    z: float,
    height: float,
    outside_diameter: float,
    hole_diameter: float,
) -> None:
    for index, (x, y) in enumerate(locations, start=1):
        boss = cylinder_body(
            component,
            f"{prefix}_Boss_{index}",
            x,
            y,
            z,
            outside_diameter,
            height,
        )
        cut_cylinder(
            component,
            boss,
            f"{prefix}_Boss_{index}_Pilot",
            x,
            y,
            z - 0.1,
            hole_diameter,
            height + 0.2,
        )


def add_lid_holes(
    component: adsk.fusion.Component,
    lid: adsk.fusion.BRepBody,
    locations: list[tuple[float, float]],
    lid_height: float,
    hole_diameter: float,
    prefix: str,
) -> None:
    for index, (x, y) in enumerate(locations, start=1):
        cut_cylinder(
            component,
            lid,
            f"{prefix}_Screw_Clearance_{index}",
            x,
            y,
            -0.1,
            hole_diameter,
            lid_height + 0.2,
        )


def add_user_parameters(design: adsk.fusion.Design, params: dict[str, Any]) -> None:
    for group in ("global", "pod", "receiver"):
        for key, value in params.get(group, {}).items():
            if not isinstance(value, (int, float)):
                continue
            parameter_name = f"{group}_{key}".replace("-", "_")
            if design.userParameters.itemByName(parameter_name):
                continue
            design.userParameters.add(
                parameter_name,
                adsk.core.ValueInput.createByString(f"{value} mm"),
                "mm",
                "CueLoop preliminary; validate against physical hardware",
            )


def build_pod(
    root: adsk.fusion.Component,
    params: dict[str, Any],
    origin_x: float,
) -> None:
    glob = params["global"]
    pod = params["pod"]
    hw = params["source_hardware"]
    length = pod["outer_length"]
    width = pod["outer_width"]
    base_height = pod["base_height"]
    lid_height = pod["lid_height"]
    locations = screw_locations(length, width, glob["boss_edge_offset"])

    base_component = component_at(root, "CuePod_Base", origin_x)
    base = open_shell(
        base_component,
        "CuePod_Base_Shell",
        length,
        width,
        base_height,
        glob["wall"],
        glob["floor"],
        pod["corner_radius"],
    )
    cut_box(
        base_component,
        base,
        "CuePod_USB_C_Access",
        length - glob["wall"] - 0.5,
        (width - pod["usb_opening_width"]) / 2,
        pod["usb_opening_z"],
        glob["wall"] + 1.0,
        pod["usb_opening_width"],
        pod["usb_opening_height"],
        1.0,
    )
    add_bosses(
        base_component,
        "CuePod",
        locations,
        glob["floor"],
        base_height - glob["floor"] - 1.0,
        glob["m2_boss_diameter"],
        1.6,
    )

    # Four low standoffs create a supported deck above the restrained cell.
    xiao = hw["xiao_sense"]
    deck_x = (length - xiao["length"]) / 2
    deck_y = (width - xiao["width"]) / 2
    for index, (x, y) in enumerate(
        (
            (deck_x + 2.0, deck_y + 2.0),
            (deck_x + xiao["length"] - 2.0, deck_y + 2.0),
            (deck_x + xiao["length"] - 2.0, deck_y + xiao["width"] - 2.0),
            (deck_x + 2.0, deck_y + xiao["width"] - 2.0),
        ),
        start=1,
    ):
        cylinder_body(
            base_component,
            f"XIAO_Deck_Support_{index}",
            x,
            y,
            glob["floor"],
            3.2,
            pod["board_standoff_height"],
        )

    lid_component = component_at(
        root,
        "CuePod_Lid",
        origin_x,
        0,
        base_height + glob["exploded_gap"],
    )
    lid = box_body(
        lid_component,
        "CuePod_Lid_Panel",
        0,
        0,
        0,
        length,
        width,
        lid_height,
        pod["corner_radius"],
    )
    add_lid_holes(
        lid_component,
        lid,
        locations,
        lid_height,
        glob["m2_clearance_diameter"],
        "CuePod",
    )
    mic_x = pod["mic_center_x"]
    mic_y = pod["mic_center_y"]
    mic_points = [(mic_x, mic_y)]
    for index in range(6):
        angle = index * math.pi / 3.0
        mic_points.append(
            (
                mic_x + pod["mic_ring_radius"] * math.cos(angle),
                mic_y + pod["mic_ring_radius"] * math.sin(angle),
            )
        )
    for index, (x, y) in enumerate(mic_points, start=1):
        cut_cylinder(
            lid_component,
            lid,
            f"Microphone_Labyrinth_{index}",
            x,
            y,
            -0.1,
            pod["mic_hole_diameter"],
            lid_height + 0.2,
        )

    # Named keepouts make the preliminary stacking assumption visible.
    battery = hw["lipo_500"]
    battery_component = component_at(root, "CuePod_Battery_Keepout", origin_x)
    box_body(
        battery_component,
        "LiPo_500mAh_ESTIMATED_Keepout",
        (length - battery["length"]) / 2,
        (width - battery["width"]) / 2,
        glob["floor"] + 0.5,
        battery["length"],
        battery["width"],
        battery["height"],
        1.5,
    )
    xiao_component = component_at(root, "CuePod_XIAO_Keepout", origin_x)
    box_body(
        xiao_component,
        "XIAO_Sense_ESTIMATED_Keepout",
        deck_x,
        deck_y,
        glob["floor"] + pod["board_standoff_height"] + 0.5,
        xiao["length"],
        xiao["width"],
        xiao["height"],
        1.0,
    )


def build_receiver(
    root: adsk.fusion.Component,
    params: dict[str, Any],
    origin_x: float,
) -> None:
    glob = params["global"]
    receiver = params["receiver"]
    uno = params["source_hardware"]["uno_q"]
    length = receiver["outer_length"]
    width = receiver["outer_width"]
    base_height = receiver["base_height"]
    lid_height = receiver["lid_height"]
    locations = screw_locations(length, width, glob["boss_edge_offset"])

    base_component = component_at(root, "Receiver_Base", origin_x)
    base = open_shell(
        base_component,
        "Receiver_Base_Shell",
        length,
        width,
        base_height,
        glob["wall"],
        glob["floor"],
        receiver["corner_radius"],
    )
    light_x = (length - receiver["light_window_length"]) / 2
    cut_box(
        base_component,
        base,
        "Front_Alert_Window",
        light_x,
        -0.6,
        receiver["light_window_z"],
        receiver["light_window_length"],
        glob["wall"] + 1.2,
        receiver["light_window_height"],
        2.0,
    )
    add_bosses(
        base_component,
        "Receiver",
        locations,
        glob["floor"],
        base_height - glob["floor"] - 1.0,
        glob["m2_boss_diameter"],
        1.6,
    )

    # Preliminary UNO supports use its outline, not unverified mounting holes.
    board_x = (length - uno["length"]) / 2
    board_y = (width - uno["width"]) / 2
    for index, (x, y) in enumerate(
        (
            (board_x + 3.0, board_y + 3.0),
            (board_x + uno["length"] - 3.0, board_y + 3.0),
            (board_x + uno["length"] - 3.0, board_y + uno["width"] - 3.0),
            (board_x + 3.0, board_y + uno["width"] - 3.0),
        ),
        start=1,
    ):
        cylinder_body(
            base_component,
            f"UNO_Q_Outline_Support_{index}",
            x,
            y,
            glob["floor"],
            5.0,
            receiver["uno_standoff_height"],
        )

    lid_component = component_at(
        root,
        "Receiver_Lid",
        origin_x,
        0,
        base_height + glob["exploded_gap"],
    )
    lid = box_body(
        lid_component,
        "Receiver_Lid_Panel",
        0,
        0,
        0,
        length,
        width,
        lid_height,
        receiver["corner_radius"],
    )
    add_lid_holes(
        lid_component,
        lid,
        locations,
        lid_height,
        glob["m2_clearance_diameter"],
        "Receiver",
    )
    dock_x = (length - receiver["dock_length"]) / 2
    dock_y = 8.0
    cut_box(
        lid_component,
        lid,
        "CuePod_Dock_Pocket",
        dock_x,
        dock_y,
        lid_height - receiver["dock_depth"],
        receiver["dock_length"],
        receiver["dock_width"],
        receiver["dock_depth"] + 0.2,
        3.0,
    )
    # Raised rails communicate the dock/latch concept without freezing magnets.
    for index, rail_x in enumerate((dock_x - 1.5, dock_x + receiver["dock_length"] - 0.5), start=1):
        box_body(
            lid_component,
            f"Dock_Rail_{index}",
            rail_x,
            dock_y + 4.0,
            lid_height,
            2.0,
            receiver["dock_width"] - 8.0,
            2.0,
            0.8,
        )

    button_y = width - 14.0
    for index, button_x in enumerate((length / 2 - 18.0, length / 2, length / 2 + 18.0), start=1):
        cylinder_body(
            lid_component,
            f"Tactile_Button_{index}",
            button_x,
            button_y,
            lid_height,
            receiver["button_diameter"],
            2.2,
        )

    diffuser_component = component_at(root, "Alert_Diffuser", origin_x)
    box_body(
        diffuser_component,
        "Front_Alert_Diffuser",
        light_x + 0.4,
        0.2,
        receiver["light_window_z"] + 0.3,
        receiver["light_window_length"] - 0.8,
        1.4,
        receiver["light_window_height"] - 0.6,
        1.8,
    )

    uno_component = component_at(root, "Receiver_UNO_Q_Keepout", origin_x)
    box_body(
        uno_component,
        "UNO_Q_ESTIMATED_Keepout",
        board_x,
        board_y,
        glob["floor"] + receiver["uno_standoff_height"] + 0.5,
        uno["length"],
        uno["width"],
        uno["height_envelope"],
        1.0,
    )

    clip_component = component_at(root, "Clip_Stand", origin_x + (length - receiver["clip_length"]) / 2, width + 8.0)
    box_body(
        clip_component,
        "Clip_Stand_Main",
        0,
        0,
        0,
        receiver["clip_length"],
        receiver["clip_width"],
        receiver["clip_thickness"],
        3.0,
    )
    box_body(
        clip_component,
        "Clip_Stand_Foot",
        4.0,
        receiver["clip_width"] - 3.0,
        receiver["clip_thickness"],
        receiver["clip_length"] - 8.0,
        3.0,
        receiver["clip_gap"],
        1.0,
    )


def run(_context: Any) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        root.name = "CueLoop Bridge Preliminary Assembly"
        root.attributes.add(
            "CueLoop",
            "Evidence",
            "ESTIMATED_DIMENSIONS_VALIDATE_BEFORE_MANUFACTURE",
        )

        params = load_parameters()
        add_user_parameters(design, params)
        build_pod(root, params, 0.0)
        build_receiver(root, params, 70.0)

        app.activeViewport.fit()
        ui.messageBox(
            "CueLoop Bridge preliminary assembly created.\n\n"
            "Dimensions are estimated/manufacturer envelopes. Complete "
            "cad/DIMENSION_VALIDATION.md before manufacturing, inspect all "
            "cuts and clearances, then export the reviewed design as .f3d.",
            "CueLoop Bridge",
        )
    except Exception:
        ui.messageBox(
            "CueLoop Bridge generator failed:\n\n" + traceback.format_exc(),
            "CueLoop Bridge Generator Error",
        )


def stop(_context: Any) -> None:
    """Fusion script stop hook; the generated document remains open."""

