"""Build support-sensitive 3MF projects for L2 parameter validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_SETTINGS = "Metadata/project_settings.config"

_TREE_PARAMETERS = {
    "max_bridge_length",
    "support_base_pattern_tree",
    "support_interface_min_area",
    "tree_hybrid_cross_height",
    "tree_support_branch_diameter",
    "tree_support_branch_angle",
    "tree_support_wall_count",
    "tree_support_wall_count_tree",
    "tree_support_branch_distance",
    "tree_support_tip_diameter",
}
_RAFT_PARAMETERS = {
    "raft_layers",
    "raft_contact_distance",
    "raft_first_layer_density",
    "raft_first_layer_expansion",
}
_INTERFACE_PARAMETERS = {
    "ironing_support_layer",
    "support_interface_filament",
    "support_interface_not_for_body",
    "support_interface_top_layers",
    "support_interface_bottom_layers",
    "support_interface_pattern",
    "support_interface_spacing",
    "support_bottom_interface_spacing",
    "support_interface_loop_pattern",
    "support_interface_speed",
    "support_interface_min_area",
}
_DUAL_FILAMENT_PARAMETERS = {
    "ironing_support_layer",
    "support_filament",
    "support_interface_filament",
    "support_interface_not_for_body",
}

# These parameters need geometry that contains the feature they operate on.
# Keep one canonical geometry for every value of a parameter so differences in
# the exported G-code can only come from the process setting under test.
_SPECIALIZED_TEMPLATES = {
    "bridge_no_support": "support_advanced/bridge_no_support/bridge_no_support_0.3mf",
    "max_bridge_length": "support_advanced/max_bridge_length/max_bridge_length_5.3mf",
    "support_bottom_interface_spacing": (
        "support_basic/support_on_build_plate_only/"
        "support_on_build_plate_only_disabled.3mf"
    ),
    "support_bottom_z_distance": (
        "support_advanced/support_bottom_z_distance/"
        "support_bottom_z_distance_0.1.3mf"
    ),
    "support_interface_bottom_layers": (
        "support_advanced/support_interface_bottom_layers/"
        "support_interface_bottom_layers_1.3mf"
    ),
    "support_interface_min_area": (
        "support_advanced/support_interface_min_area/"
        "support_interface_min_area_0.25.3mf"
    ),
    "support_object_first_layer_gap": (
        "support_advanced/support_object_first_layer_gap/"
        "support_object_first_layer_gap_0.3mf"
    ),
    "support_critical_regions_only": (
        "support_basic/support_critical_regions_only/"
        "support_critical_regions_only_disabled.3mf"
    ),
}

_SYNTHETIC_GEOMETRY_PARAMETERS = {
    "bridge_no_support",
    "max_bridge_length",
    "support_bottom_interface_spacing",
    "support_bottom_z_distance",
    "support_interface_bottom_layers",
    "support_interface_min_area",
    "support_object_first_layer_gap",
    "support_critical_regions_only",
    "support_on_build_plate_only",
    "support_top_z_distance",
    "tree_hybrid_cross_height",
}

_CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
_PRODUCTION_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"


def _synthetic_support_model() -> bytes:
    """Return a mesh containing bridges and support-on-object contacts.

    The three bridge spans exercise length thresholds.  The elevated shelves
    exercise support floors, Z gaps, first-layer XY clearance and small contact
    regions.  All values of a parameter use this exact mesh.
    """
    boxes = [
        # Three bridges with unsupported spans of roughly 8, 14 and 24 mm.
        (-32, -28, -30, -24, 0, 18), (-20, -16, -30, -24, 0, 18),
        (-32, -16, -30, -24, 18, 20),
        (-10, -6, -30, -24, 0, 18), (8, 12, -30, -24, 0, 18),
        (-10, 12, -30, -24, 18, 20),
        (18, 22, -30, -24, 0, 18), (46, 50, -30, -24, 0, 18),
        (18, 50, -30, -24, 18, 20),
        # A lower body and a large shelf.  Support below the left portion lands
        # on the body while support below the right portion starts on the bed.
        (-30, -5, -12, 12, 0, 10),
        (-30, 30, -12, 12, 20, 22),
        # Small elevated contacts make support_interface_min_area observable.
        (-30, -27, 18, 21, 12, 14),
        (-20, -15, 18, 21, 15, 17),
        (-8, 0, 18, 21, 18, 20),
    ]
    vertices = []
    triangles = []
    faces = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    for xmin, xmax, ymin, ymax, zmin, zmax in boxes:
        offset = len(vertices)
        vertices.extend((
            (xmin, ymin, zmin), (xmax, ymin, zmin),
            (xmax, ymax, zmin), (xmin, ymax, zmin),
            (xmin, ymin, zmax), (xmax, ymin, zmax),
            (xmax, ymax, zmax), (xmin, ymax, zmax),
        ))
        triangles.extend(tuple(offset + index for index in face) for face in faces)

    vertex_xml = "".join(
        f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in vertices
    )
    triangle_xml = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{_CORE_NS}" '
        f'xmlns:p="{_PRODUCTION_NS}" requiredextensions="p">'
        '<resources><object id="1" p:UUID="00020000-81cb-4c03-9d28-80fed5dfa1dc" '
        'type="model"><mesh><vertices>' + vertex_xml + '</vertices><triangles>' +
        triangle_xml + '</triangles></mesh></object></resources></model>'
    ).encode("utf-8")


def _place_synthetic_model_on_bed(data: bytes) -> bytes:
    ElementTree.register_namespace("", _CORE_NS)
    ElementTree.register_namespace("p", _PRODUCTION_NS)
    root = ElementTree.fromstring(data)
    for item in root.iter(f"{{{_CORE_NS}}}item"):
        transform = item.get("transform", "").split()
        if len(transform) == 12:
            transform[11] = "0"
            item.set("transform", " ".join(transform))
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def _serialized(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _template_path(repo: Path, parameter: str) -> Path:
    models = repo / "test_framework" / "engine_params" / "data" / "models"
    if parameter in _DUAL_FILAMENT_PARAMETERS:
        return (
            models
            / "process"
            / "filament"
            / "flush_into_support"
            / "flush_into_support_on.3mf"
        )
    if parameter in _SPECIALIZED_TEMPLATES:
        return models / "process" / "support" / _SPECIALIZED_TEMPLATES[parameter]
    return (
        models
        / "process"
        / "support"
        / "support_basic"
        / "enable_support"
        / "support_enabled.3mf"
    )


def _configure(settings: dict, parameter: str, expected_value: Any) -> dict:
    original = dict(settings)
    settings = dict(settings)
    settings["enable_support"] = "1"
    settings[parameter] = _serialized(expected_value)

    if parameter == "enable_support":
        settings["enable_support"] = _serialized(expected_value)

    if parameter in _TREE_PARAMETERS:
        settings["support_type"] = "tree(auto)"
        settings["support_style"] = "tree_slim"
    if parameter == "tree_hybrid_cross_height":
        settings["support_style"] = "tree_hybrid"
    if parameter == "tree_support_wall_count":
        # support_new/SupportParameters.hpp reads tree_support_wall_count for
        # normal support and tree_support_wall_count_tree for tree support.
        settings["support_type"] = "normal(auto)"
        settings["support_style"] = "default"
    if parameter == "support_style":
        value = _serialized(expected_value)
        settings["support_type"] = (
            "tree(auto)"
            if value.startswith("tree_") or value == "organic"
            else "normal(auto)"
        )
    if parameter == "support_type":
        value = _serialized(expected_value)
        settings["support_style"] = "tree_slim" if value.startswith("tree") else "default"

    if parameter in _RAFT_PARAMETERS and parameter != "raft_layers":
        settings["raft_layers"] = "2"

    if parameter in _INTERFACE_PARAMETERS:
        settings["support_interface_top_layers"] = "2"
        settings["support_interface_bottom_layers"] = "2"
        settings["support_interface_min_area"] = "0"
    if parameter == "ironing_support_layer":
        settings["support_interface_not_for_body"] = "0"

    if parameter in _DUAL_FILAMENT_PARAMETERS:
        settings["enable_prime_tower"] = "1"
        settings["support_filament"] = "1"
        settings["support_interface_filament"] = "2"
    if parameter == "support_interface_not_for_body":
        # GCode.cpp only applies this option when the support base extruder is
        # "don't care" (0) and a dedicated interface extruder is selected.
        settings["support_filament"] = "0"

    # Prerequisites establish a valid scenario, but the parameter under test
    # always wins when it is itself one of those prerequisite keys.
    settings[parameter] = _serialized(expected_value)

    # Creality Print only restores process values recorded as differences from
    # the selected system preset. Keep this index in sync with generated values.
    differences = list(settings.get("different_settings_to_system") or ["", "", ""])
    while len(differences) < 3:
        differences.append("")
    changed = {
        key for key, value in settings.items()
        if original.get(key) != value
    }
    changed.add(parameter)
    changed.update(filter(None, str(differences[0]).split(";")))
    differences[0] = ";".join(sorted(changed))
    settings["different_settings_to_system"] = differences

    return settings


def build_support_l2_project(
    *,
    repo: Path,
    output_path: Path,
    parameter: str,
    expected_value: Any,
    source_project: Path | None = None,
) -> Path:
    """Create a temporary 3MF whose geometry exercises the support parameter."""
    template = source_project or _template_path(repo, parameter)
    if not template.is_file():
        raise FileNotFoundError(f"support L2 template not found: {template}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(template, "r") as source:
        settings = json.loads(source.read(PROJECT_SETTINGS).decode("utf-8"))
        settings = _configure(settings, parameter, expected_value)
        encoded_settings = json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8")
        object_models = [
            name for name in source.namelist()
            if name.startswith("3D/Objects/") and name.endswith(".model")
        ]
        with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as target:
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename == PROJECT_SETTINGS:
                    data = encoded_settings
                elif parameter in _SYNTHETIC_GEOMETRY_PARAMETERS:
                    if info.filename in object_models[:1]:
                        data = _synthetic_support_model()
                    elif info.filename == "3D/3dmodel.model":
                        data = _place_synthetic_model_on_bed(data)
                target.writestr(info, data)
    return output_path
