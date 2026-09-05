#!/usr/bin/env python3
"""Host-side validation for CueLoop CAD sources and generated output bundles.

This module intentionally has no CAD dependency.  It validates the shared
parameter/contract math, required component and output structure, reported
OpenCascade/Fusion geometry facts, and SHA-256 manifests.  OpenCascade itself
produces the reference geometry report in ``cad/reference/freecad_reference.py``;
this validator independently enforces the report contract on any Ubuntu host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CAD_ROOT = Path(__file__).resolve().parent
DEFAULT_PARAMETERS = CAD_ROOT / "design_parameters.json"
DEFAULT_CONTRACT = CAD_ROOT / "design_contract.json"


class CadValidationError(ValueError):
    """Raised when CAD inputs or outputs violate the declared design contract."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CadValidationError(f"{path} must contain a JSON object")
    return value


def number(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CadValidationError(f"{key} must be numeric")
    return float(value)


def numeric_parameter_count(parameters: dict[str, Any]) -> int:
    count = 0
    for group in ("manufacturing", "layout", "pod", "receiver"):
        count += sum(
            1
            for value in parameters[group].values()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        )
    for hardware in parameters["source_hardware"].values():
        count += sum(
            1
            for value in hardware.values()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        )
    return count


def rectangle_separation(a: dict[str, float], b: dict[str, float]) -> float:
    """Return the largest axis separation; negative means planar overlap."""

    x_gap = max(b["x"] - (a["x"] + a["length"]), a["x"] - (b["x"] + b["length"]))
    y_gap = max(b["y"] - (a["y"] + a["width"]), a["y"] - (b["y"] + b["width"]))
    return max(x_gap, y_gap)


def rectangle_circle_clearance(
    rectangle: dict[str, float], center_x: float, center_y: float, radius: float
) -> float:
    closest_x = min(max(center_x, rectangle["x"]), rectangle["x"] + rectangle["length"])
    closest_y = min(max(center_y, rectangle["y"]), rectangle["y"] + rectangle["width"])
    distance = ((center_x - closest_x) ** 2 + (center_y - closest_y) ** 2) ** 0.5
    return distance - radius


def validate_sources(
    parameters: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    if parameters.get("schema_version") != 2:
        raise CadValidationError("design_parameters schema_version must be 2")
    if parameters.get("units") != "mm":
        raise CadValidationError("design_parameters units must be mm")
    if contract.get("schema_version") != 1:
        raise CadValidationError("design_contract schema_version must be 1")

    for required_group in (
        "manufacturing",
        "layout",
        "source_hardware",
        "pod",
        "receiver",
    ):
        if not isinstance(parameters.get(required_group), dict):
            raise CadValidationError(f"missing parameter group: {required_group}")

    mfg = parameters["manufacturing"]
    pod = parameters["pod"]
    receiver = parameters["receiver"]
    hardware = parameters["source_hardware"]
    for group_name, group in (
        ("manufacturing", mfg),
        ("pod", pod),
        ("receiver", receiver),
    ):
        for key, value in group.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise CadValidationError(f"{group_name}.{key} must be numeric")
            if value <= 0:
                raise CadValidationError(f"{group_name}.{key} must be positive")

    wall = number(mfg, "wall")
    floor = number(mfg, "floor")
    clearance = number(mfg, "fit_clearance")
    minimum_web = number(mfg, "minimum_web")
    if wall < 2.0 or floor < 2.0:
        raise CadValidationError("wall and floor must each be at least 2.0 mm")
    if minimum_web > wall:
        raise CadValidationError("minimum_web cannot exceed wall")
    boss_radial_web = (
        number(mfg, "m2_boss_diameter") - number(mfg, "m2_pilot_diameter")
    ) / 2.0
    if boss_radial_web < minimum_web:
        raise CadValidationError("M2 boss radial web is below minimum_web")

    battery = hardware["lipo_500"]
    xiao = hardware["xiao_sense"]
    pod_inner = {
        "length": number(pod, "outer_length") - 2.0 * wall,
        "width": number(pod, "outer_width") - 2.0 * wall,
        "height": number(pod, "bottom_height") - floor,
    }
    for axis in ("length", "width"):
        if pod_inner[axis] < number(battery, axis) + 2.0 * clearance:
            raise CadValidationError(f"CuePod does not clear LiPo {axis}")
        if pod_inner[axis] < number(xiao, axis) + 2.0 * clearance:
            raise CadValidationError(f"CuePod does not clear XIAO {axis}")
    xiao_closed_margin = (
        number(pod, "bottom_height")
        + number(pod, "top_height")
        - floor
        - number(pod, "board_standoff_height")
        - number(xiao, "height_envelope")
    )
    if xiao_closed_margin < 0:
        raise CadValidationError("XIAO vertical envelope exceeds closed CuePod")
    battery_bottom = floor + number(pod, "battery_floor_gap")
    battery_top = battery_bottom + number(battery, "height_envelope")
    bridge_bottom = battery_top + number(pod, "battery_bridge_clearance")
    bridge_top = bridge_bottom + number(pod, "board_bridge_thickness")
    xiao_bottom = (
        floor
        + number(pod, "board_standoff_height")
        + number(pod, "board_support_clearance")
    )
    xiao_top = xiao_bottom + number(xiao, "height_envelope")
    microphone = hardware["microphone_cartridge"]
    microphone_bottom = (
        number(pod, "bottom_height")
        - number(microphone, "height_envelope")
        - number(pod, "microphone_top_gap")
    )
    microphone_top = microphone_bottom + number(microphone, "height_envelope")
    vertical_clearances = {
        "battery_to_bridge": bridge_bottom - battery_top,
        "bridge_to_xiao": xiao_bottom - bridge_top,
        "battery_to_xiao": xiao_bottom - battery_top,
        "xiao_to_microphone": microphone_bottom - xiao_top,
        "microphone_to_lid": number(pod, "bottom_height") - microphone_top,
    }
    required_vertical_clearances = {
        "battery_to_bridge": number(pod, "battery_bridge_clearance"),
        "bridge_to_xiao": number(pod, "board_support_clearance"),
        "battery_to_xiao": number(mfg, "fit_clearance"),
        "xiao_to_microphone": number(mfg, "print_gap"),
        "microphone_to_lid": number(pod, "microphone_top_gap"),
    }
    for name, required in required_vertical_clearances.items():
        actual = vertical_clearances[name]
        if actual + 1e-9 < required:
            raise CadValidationError(
                f"CuePod vertical clearance {name} is {actual:.3f} mm; "
                f"requires {required:.3f} mm"
            )
    battery_rectangle = {
        "x": (number(pod, "outer_length") - number(battery, "length")) / 2.0,
        "y": (number(pod, "outer_width") - number(battery, "width")) / 2.0,
        "length": number(battery, "length"),
        "width": number(battery, "width"),
    }
    pod_boss_radius = number(mfg, "m2_boss_diameter") / 2.0
    pod_boss_clearances: dict[str, float] = {}
    for index, (boss_x, boss_y) in enumerate(
        (
            (number(pod, "boss_edge_offset"), number(pod, "boss_edge_offset")),
            (
                number(pod, "outer_length") - number(pod, "boss_edge_offset"),
                number(pod, "boss_edge_offset"),
            ),
            (
                number(pod, "outer_length") - number(pod, "boss_edge_offset"),
                number(pod, "outer_width") - number(pod, "boss_edge_offset"),
            ),
            (
                number(pod, "boss_edge_offset"),
                number(pod, "outer_width") - number(pod, "boss_edge_offset"),
            ),
        ),
        start=1,
    ):
        boss_clearance = rectangle_circle_clearance(
            battery_rectangle, boss_x, boss_y, pod_boss_radius
        )
        if boss_clearance < number(pod, "battery_restraint_gap"):
            raise CadValidationError(
                f"LiPo clearance to CuePod boss {index} is only {boss_clearance:.3f} mm"
            )
        pod_boss_clearances[f"LiPo--boss_{index}"] = boss_clearance

    uno = hardware["uno_q"]
    receiver_inner = {
        "length": number(receiver, "outer_length") - 2.0 * wall,
        "width": number(receiver, "outer_width") - 2.0 * wall,
        "height": number(receiver, "bottom_height") - floor,
    }
    for axis in ("length", "width"):
        if receiver_inner[axis] < number(uno, axis) + 2.0 * clearance:
            raise CadValidationError(f"Receiver does not clear UNO Q {axis}")
    uno_vertical_margin = (
        number(receiver, "bottom_height")
        - floor
        - number(receiver, "uno_standoff_height")
        - number(uno, "height_envelope")
    )
    if uno_vertical_margin < 0:
        raise CadValidationError("UNO Q vertical envelope exceeds receiver bottom")

    receiver_envelopes = {
        "UNO_Q": {
            "x": number(receiver, "uno_origin_x"),
            "y": number(receiver, "uno_origin_y"),
            "length": number(uno, "length"),
            "width": number(uno, "width"),
        },
        "support_electronics": {
            "x": number(receiver, "support_origin_x"),
            "y": number(receiver, "support_origin_y"),
            "length": number(hardware["support_electronics"], "length"),
            "width": number(hardware["support_electronics"], "width"),
        },
        "haptic_led_module": {
            "x": number(receiver, "haptic_origin_x"),
            "y": number(receiver, "haptic_origin_y"),
            "length": number(hardware["haptic_led_module"], "length"),
            "width": number(hardware["haptic_led_module"], "width"),
        },
    }
    receiver_bounds = {
        "left": wall + clearance,
        "right": number(receiver, "outer_length") - wall - clearance,
        "front": wall + clearance,
        "back": number(receiver, "outer_width") - wall - clearance,
    }
    edge_clearances: dict[str, float] = {}
    for name, envelope in receiver_envelopes.items():
        edge_clearance = min(
            envelope["x"] - receiver_bounds["left"],
            receiver_bounds["right"] - (envelope["x"] + envelope["length"]),
            envelope["y"] - receiver_bounds["front"],
            receiver_bounds["back"] - (envelope["y"] + envelope["width"]),
        )
        if edge_clearance < 0:
            raise CadValidationError(f"{name} envelope violates receiver wall clearance")
        edge_clearances[name] = edge_clearance

    pair_clearances: dict[str, float] = {}
    envelope_items = list(receiver_envelopes.items())
    for index, (left_name, left) in enumerate(envelope_items):
        for right_name, right in envelope_items[index + 1 :]:
            separation = rectangle_separation(left, right)
            pair_name = f"{left_name}--{right_name}"
            if separation < clearance:
                raise CadValidationError(
                    f"receiver envelopes {pair_name} have only {separation:.3f} mm separation"
                )
            pair_clearances[pair_name] = separation

    boss_radius = number(mfg, "m2_boss_diameter") / 2.0
    boss_clearances: dict[str, float] = {}
    for envelope_name, envelope in receiver_envelopes.items():
        for index, (boss_x, boss_y) in enumerate(
            (
                (number(mfg, "boss_edge_offset"), number(mfg, "boss_edge_offset")),
                (
                    number(receiver, "outer_length") - number(mfg, "boss_edge_offset"),
                    number(mfg, "boss_edge_offset"),
                ),
                (
                    number(receiver, "outer_length") - number(mfg, "boss_edge_offset"),
                    number(receiver, "outer_width") - number(mfg, "boss_edge_offset"),
                ),
                (
                    number(mfg, "boss_edge_offset"),
                    number(receiver, "outer_width") - number(mfg, "boss_edge_offset"),
                ),
            ),
            start=1,
        ):
            boss_clearance = rectangle_circle_clearance(
                envelope, boss_x, boss_y, boss_radius
            )
            if boss_clearance < clearance:
                raise CadValidationError(
                    f"{envelope_name} clearance to receiver boss {index} is "
                    f"{boss_clearance:.3f} mm"
                )
            boss_clearances[f"{envelope_name}--boss_{index}"] = boss_clearance

    dock_clearance = {
        "length": number(receiver, "dock_pocket_length")
        - number(pod, "outer_length"),
        "width": number(receiver, "dock_pocket_width")
        - number(pod, "outer_width"),
    }
    for axis, value in dock_clearance.items():
        if value < 2.0 * clearance:
            raise CadValidationError(
                f"dock {axis} clearance {value:.3f} mm is below "
                f"2 * fit_clearance ({2.0 * clearance:.3f} mm)"
            )
    if number(receiver, "dock_pocket_depth") >= number(receiver, "top_height"):
        raise CadValidationError("dock pocket would cut through receiver top")

    components = contract.get("components")
    if not isinstance(components, list) or not components:
        raise CadValidationError("contract must declare components")
    component_names = [entry.get("name") for entry in components]
    if len(component_names) != len(set(component_names)):
        raise CadValidationError("contract component names must be unique")
    manufacturing = [
        entry for entry in components if entry.get("manufacturing_export") is True
    ]
    if len(manufacturing) < 6:
        raise CadValidationError("at least six manufacturing components are required")
    for entry in components:
        if entry.get("role") not in {"assembly", "manufacturing", "reference"}:
            raise CadValidationError(f"invalid role for {entry.get('name')}")
        if not entry.get("provenance"):
            raise CadValidationError(f"missing provenance for {entry.get('name')}")
        if entry.get("manufacturing_export") and not entry.get("output_stem"):
            raise CadValidationError(
                f"missing manufacturing output stem for {entry.get('name')}"
            )

    parameter_count = numeric_parameter_count(parameters)
    declared_minimum = int(contract["minimum_counts"]["user_parameters"])
    if parameter_count < declared_minimum:
        raise CadValidationError(
            f"only {parameter_count} numeric user parameters; minimum is {declared_minimum}"
        )

    return {
        "schema_version": 1,
        "status": "pass",
        "numeric_parameter_count": parameter_count,
        "manufacturing_component_count": len(manufacturing),
        "declared_component_count": len(components),
        "wall_mm": wall,
        "floor_mm": floor,
        "boss_radial_web_mm": boss_radial_web,
        "pod_inner_mm": pod_inner,
        "receiver_inner_mm": receiver_inner,
        "dock_total_clearance_mm": dock_clearance,
        "xiao_closed_height_margin_mm": xiao_closed_margin,
        "pod_vertical_clearance_mm": vertical_clearances,
        "pod_battery_boss_clearance_mm": pod_boss_clearances,
        "uno_vertical_margin_mm": uno_vertical_margin,
        "receiver_envelope_edge_clearance_mm": edge_clearances,
        "receiver_envelope_pair_clearance_mm": pair_clearances,
        "receiver_envelope_boss_clearance_mm": boss_clearances,
    }


def parse_checksum_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if (
            len(parts) != 2
            or len(parts[0]) != 64
            or any(character not in "0123456789abcdef" for character in parts[0])
        ):
            raise CadValidationError(
                f"invalid checksum line {line_number} in {path.name}"
            )
        digest, relative = parts
        relative_parts = Path(relative).parts
        if (
            relative.startswith("/")
            or ".." in relative_parts
            or "\\" in relative
            or not relative_parts
        ):
            raise CadValidationError(f"unsafe checksum path: {relative}")
        if relative in entries:
            raise CadValidationError(f"duplicate checksum path: {relative}")
        entries[relative] = digest
    return entries


def verify_checksums(directory: Path) -> dict[str, str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.is_file():
        raise CadValidationError(f"missing checksum manifest: {manifest}")
    entries = parse_checksum_manifest(manifest)
    resolved_directory = directory.resolve()
    for relative, expected in entries.items():
        candidate = directory / relative
        try:
            candidate.resolve().relative_to(resolved_directory)
        except ValueError as error:
            raise CadValidationError(
                f"checksum target escapes output directory: {relative}"
            ) from error
        if not candidate.is_file():
            raise CadValidationError(f"checksum target missing: {relative}")
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != expected:
            raise CadValidationError(
                f"checksum mismatch for {relative}: {actual} != {expected}"
            )
    return entries


def require_checksum_coverage(
    checksums: dict[str, str], required_relatives: list[str]
) -> None:
    expected = {relative for relative in required_relatives if relative != "SHA256SUMS.txt"}
    missing = expected - set(checksums)
    if missing:
        raise CadValidationError(
            "checksum manifest omits required output(s): " + ", ".join(sorted(missing))
        )


def _require_nonempty(directory: Path, relatives: list[str]) -> None:
    for relative in relatives:
        path = directory / relative
        if not path.is_file() or path.stat().st_size == 0:
            raise CadValidationError(f"missing or empty output: {relative}")


def expected_reference_bounds(parameters: dict[str, Any]) -> dict[str, tuple[float, float, float]]:
    pod = parameters["pod"]
    receiver = parameters["receiver"]
    hardware = parameters["source_hardware"]
    return {
        "CuePod_Bottom": (
            number(pod, "outer_length"),
            number(pod, "outer_width"),
            number(pod, "bottom_height") + number(pod, "dock_tongue_height"),
        ),
        "CuePod_Top": (
            number(pod, "outer_length"),
            number(pod, "outer_width"),
            number(pod, "top_height") + number(pod, "lid_lip_height"),
        ),
        "Receiver_Bottom": (
            number(receiver, "outer_length"),
            number(receiver, "outer_width"),
            number(receiver, "bottom_height"),
        ),
        "Receiver_Top": (
            number(receiver, "outer_length"),
            number(receiver, "outer_width"),
            number(receiver, "top_height")
            + number(receiver, "lid_lip_height")
            + number(receiver, "dock_rail_height"),
        ),
        "Receiver_Carry_Clip": (
            number(receiver, "clip_length"),
            number(receiver, "clip_width"),
            number(receiver, "clip_thickness")
            + number(receiver, "clip_gap")
            + number(receiver, "clip_foot_height"),
        ),
        "Alert_Diffuser": (
            number(receiver, "light_window_length"),
            number(receiver, "light_window_width") - 0.6,
            1.8,
        ),
        "Reference_UNO_Q": (
            number(hardware["uno_q"], "length"),
            number(hardware["uno_q"], "width"),
            number(hardware["uno_q"], "height_envelope"),
        ),
        "Reference_Support_Electronics": (
            number(hardware["support_electronics"], "length"),
            number(hardware["support_electronics"], "width"),
            number(hardware["support_electronics"], "height_envelope"),
        ),
        "Reference_Haptic_LED_Module": (
            number(hardware["haptic_led_module"], "length"),
            number(hardware["haptic_led_module"], "width"),
            number(hardware["haptic_led_module"], "height_envelope"),
        ),
        "Reference_XIAO_Sense": (
            number(hardware["xiao_sense"], "length"),
            number(hardware["xiao_sense"], "width"),
            number(hardware["xiao_sense"], "height_envelope"),
        ),
        "Reference_LiPo_500mAh": (
            number(hardware["lipo_500"], "length"),
            number(hardware["lipo_500"], "width"),
            number(hardware["lipo_500"], "height_envelope"),
        ),
        "Reference_Microphone_Cartridge": (
            number(hardware["microphone_cartridge"], "length"),
            number(hardware["microphone_cartridge"], "width"),
            number(hardware["microphone_cartridge"], "height_envelope"),
        ),
    }


def validate_reference_output(
    directory: Path, parameters: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    source_result = validate_sources(parameters, contract)
    _require_nonempty(directory, list(contract["reference_outputs"]))
    manufacturing = [
        entry for entry in contract["components"] if entry["manufacturing_export"]
    ]
    required_parts: list[str] = []
    for entry in manufacturing:
        required_parts.extend(
            (
                f"manufacturing/{entry['output_stem']}.step",
                f"manufacturing/{entry['output_stem']}.stl",
            )
        )
    _require_nonempty(directory, required_parts)
    checksums = verify_checksums(directory)
    require_checksum_coverage(
        checksums, list(contract["reference_outputs"]) + required_parts
    )

    report = load_json(directory / "CueLoop_Reference_geometry_report.json")
    if report.get("schema_version") != 1 or report.get("status") != "pass":
        raise CadValidationError("reference geometry report is not a schema-v1 pass")
    if report.get("kernel") != "OpenCascade via FreeCAD":
        raise CadValidationError("reference report does not identify OpenCascade")
    if report.get("authoritative") is not False:
        raise CadValidationError("reference report must explicitly be non-authoritative")
    objects = report.get("objects")
    if not isinstance(objects, list):
        raise CadValidationError("reference report objects must be a list")
    object_map = {entry.get("name"): entry for entry in objects}
    expected_bounds = expected_reference_bounds(parameters)
    expected_solids = [
        entry["name"]
        for entry in contract["components"]
        if entry["role"] in {"manufacturing", "reference"}
    ]
    for name in expected_solids:
        record = object_map.get(name)
        if not record:
            raise CadValidationError(f"reference report missing object {name}")
        if record.get("valid") is not True or record.get("solid_count") != 1:
            raise CadValidationError(f"reference object is not one valid solid: {name}")
        if float(record.get("volume_mm3", 0)) <= 0:
            raise CadValidationError(f"reference object has no positive volume: {name}")
        bounds = record.get("bounds_mm", {})
        if any(float(bounds.get(axis, 0)) <= 0 for axis in ("x", "y", "z")):
            raise CadValidationError(f"reference object has invalid bounds: {name}")
        for axis, expected in zip(("x", "y", "z"), expected_bounds[name]):
            actual = float(bounds[axis])
            if abs(actual - expected) > 0.05:
                raise CadValidationError(
                    f"reference {name} {axis} bound {actual:.3f} mm differs "
                    f"from expected {expected:.3f} mm"
                )

    reopened = report.get("reopened_step_validation", {})
    if reopened.get("valid") is not True:
        raise CadValidationError("assembly STEP did not reopen as valid geometry")
    if int(reopened.get("solid_count", 0)) < len(expected_solids):
        raise CadValidationError("reopened assembly STEP lost expected solids")
    reopened_fcstd = report.get("reopened_fcstd_validation", {})
    if reopened_fcstd.get("status") != "pass":
        raise CadValidationError("FreeCAD document did not pass reopen validation")
    if int(reopened_fcstd.get("object_count", 0)) != len(expected_solids):
        raise CadValidationError("reopened FreeCAD document lost expected objects")
    if int(reopened_fcstd.get("solid_count", 0)) != len(expected_solids):
        raise CadValidationError("reopened FreeCAD document lost expected solids")
    interference_checks = report.get("interference_checks")
    if not isinstance(interference_checks, list) or len(interference_checks) < 10:
        raise CadValidationError("reference report lacks the expected interference checks")
    for check in interference_checks:
        if check.get("pass") is not True:
            raise CadValidationError(
                f"reference interference failed: {check.get('left')}--{check.get('right')}"
            )
        if abs(float(check.get("overlap_volume_mm3", -1))) > 1e-5:
            raise CadValidationError("passing interference contains nonzero overlap")

    provenance = load_json(directory / "CueLoop_Reference_provenance.json")
    if provenance.get("authoritative") is not False:
        raise CadValidationError("reference provenance must be non-authoritative")
    if "vendor" not in json.dumps(provenance).lower():
        raise CadValidationError("reference provenance omits vendor-geometry boundary")

    return {
        "schema_version": 1,
        "status": "pass",
        "kind": "freecad_opencascade_reference",
        "source_validation": source_result,
        "reported_object_count": len(objects),
        "reopened_solid_count": reopened["solid_count"],
        "reopened_fcstd_solid_count": reopened_fcstd["solid_count"],
        "interference_check_count": len(interference_checks),
        "verified_file_count": len(checksums),
    }


def validate_fusion_output(
    directory: Path, parameters: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    source_result = validate_sources(parameters, contract)
    _require_nonempty(directory, list(contract["fusion_outputs"]))
    manufacturing = [
        entry for entry in contract["components"] if entry["manufacturing_export"]
    ]
    required_parts: list[str] = []
    for entry in manufacturing:
        for suffix in contract["manufacturing_formats"]:
            required_parts.append(
                f"manufacturing/{entry['output_stem']}.{suffix}"
            )
    _require_nonempty(directory, required_parts)
    checksums = verify_checksums(directory)
    require_checksum_coverage(
        checksums, list(contract["fusion_outputs"]) + required_parts
    )
    source_manifest = load_json(directory / "CueLoop_Bridge_source_manifest.json")
    if source_manifest.get("authoritative") is not True:
        raise CadValidationError("Fusion source manifest is not authoritative")
    source_records = source_manifest.get("sources")
    if not isinstance(source_records, list):
        raise CadValidationError("Fusion source manifest lacks source records")
    if any(not isinstance(record, dict) for record in source_records):
        raise CadValidationError("Fusion source manifest contains a non-object record")
    source_by_role = {record.get("role"): record for record in source_records}
    expected_roles = {
        "fusion_generator",
        "design_parameters",
        "design_contract",
    }
    if set(source_by_role) != expected_roles or len(source_records) != len(expected_roles):
        raise CadValidationError("Fusion source manifest roles differ from contract")
    for role, record in source_by_role.items():
        relative = str(record.get("path", ""))
        path_parts = Path(relative).parts
        if (
            not relative.startswith("sources/")
            or "\\" in relative
            or ".." in path_parts
            or Path(relative).is_absolute()
        ):
            raise CadValidationError(f"unsafe Fusion source path for {role}")
        source_copy = directory / relative
        if not source_copy.is_file():
            raise CadValidationError(f"missing Fusion source snapshot: {relative}")
        digest = hashlib.sha256(source_copy.read_bytes()).hexdigest()
        if digest != record.get("sha256"):
            raise CadValidationError(f"Fusion source manifest digest mismatch: {role}")
        if int(record.get("bytes", -1)) != source_copy.stat().st_size:
            raise CadValidationError(f"Fusion source manifest byte count mismatch: {role}")
    if load_json(
        directory / source_by_role["design_parameters"]["path"]
    ) != parameters:
        raise CadValidationError("Fusion parameter snapshot differs from validation source")
    if load_json(directory / source_by_role["design_contract"]["path"]) != contract:
        raise CadValidationError("Fusion contract snapshot differs from validation source")
    current_generator = CAD_ROOT / "fusion" / "CueLoopBridgeGenerator.py"
    if current_generator.is_file():
        snapshot_generator = (
            directory / source_by_role["fusion_generator"]["path"]
        )
        # Snapshot integrity was checked above using its exact raw hash.
        # This comparison ignores only Windows-versus-Linux line endings.
        current_bytes = current_generator.read_bytes().replace(b"\r\n", b"\n")
        snapshot_bytes = snapshot_generator.read_bytes().replace(b"\r\n", b"\n")
        if current_bytes != snapshot_bytes:
            raise CadValidationError(
                "Fusion generator snapshot differs from the checked-out generator"
            )
    report = load_json(directory / "CueLoop_Bridge_validation.json")
    if report.get("status") != "pass":
        raise CadValidationError("Fusion validation report is not a pass")
    statistics = report.get("statistics", {})
    count_mapping = {
        "components_including_root": "component_count_including_root",
        "solid_bodies": "solid_body_count",
        "native_sketches": "sketch_count",
        "native_features": "feature_count",
        "timeline_entries": "timeline_count",
        "user_parameters": "user_parameter_count",
    }
    for contract_name, report_name in count_mapping.items():
        actual = int(statistics.get(report_name, 0))
        minimum = int(contract["minimum_counts"][contract_name])
        if actual < minimum:
            raise CadValidationError(
                f"Fusion {contract_name} below minimum: {actual} < {minimum}"
            )
    reported_names = {
        entry.get("name") for entry in statistics.get("components", [])
    }
    for entry in contract["components"]:
        if entry["name"] not in reported_names:
            raise CadValidationError(
                f"Fusion report missing component {entry['name']}"
            )
    return {
        "schema_version": 1,
        "status": "pass",
        "kind": "autodesk_fusion_native",
        "source_validation": source_result,
        "statistics": statistics,
        "verified_file_count": len(checksums),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=DEFAULT_PARAMETERS)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--reference-output", type=Path)
    parser.add_argument("--fusion-output", type=Path)
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args()

    parameters = load_json(args.parameters)
    contract = load_json(args.contract)
    if args.reference_output and args.fusion_output:
        raise CadValidationError("choose reference or Fusion output, not both")
    if args.reference_output:
        result = validate_reference_output(
            args.reference_output, parameters, contract
        )
    elif args.fusion_output:
        result = validate_fusion_output(args.fusion_output, parameters, contract)
    else:
        result = validate_sources(parameters, contract)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
