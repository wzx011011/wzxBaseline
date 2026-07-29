"""Replace placeholder cubes in quality L1 projects with behavior-oriented meshes.

The project settings stored in every case-specific 3MF are preserved.  Only the
model mesh and settings required to reach the target C3DSlicer code path are
changed.  Run without ``--apply`` to list the planned replacements.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape


MODEL_ENTRY = "3D/3dmodel.model"
PROJECT_SETTINGS = "Metadata/project_settings.config"
MODEL_SETTINGS = "Metadata/model_settings.config"
BED_Z = -10.0


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]] = field(default_factory=list)
    triangles: list[tuple[int, int, int]] = field(default_factory=list)

    def add_vertex(self, point: tuple[float, float, float]) -> int:
        self.vertices.append(point)
        return len(self.vertices) - 1

    def quad(self, a: int, b: int, c: int, d: int) -> None:
        self.triangles.extend(((a, b, c), (a, c, d)))

    def box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
        base = len(self.vertices)
        self.vertices.extend(
            (
                (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
            )
        )
        self.triangles.extend(
            (tuple(base + i for i in tri) for tri in (
                (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
            ))
        )

    def prism(self, points: list[tuple[float, float]], z0: float, z1: float) -> None:
        """Add a convex polygon prism with counter-clockwise XY points."""
        bottom = [self.add_vertex((x, y, z0)) for x, y in points]
        top = [self.add_vertex((x, y, z1)) for x, y in points]
        for i in range(1, len(points) - 1):
            self.triangles.extend(((bottom[0], bottom[i + 1], bottom[i]),
                                   (top[0], top[i], top[i + 1])))
        for i in range(len(points)):
            j = (i + 1) % len(points)
            self.quad(bottom[i], bottom[j], top[j], top[i])

    def cylinder(
        self, cx: float, cy: float, radius: float, z0: float, z1: float, segments: int = 64
    ) -> None:
        bottom = [
            self.add_vertex((cx + radius * math.cos(2 * math.pi * i / segments),
                             cy + radius * math.sin(2 * math.pi * i / segments), z0))
            for i in range(segments)
        ]
        top = [self.add_vertex((self.vertices[i][0], self.vertices[i][1], z1)) for i in bottom]
        cb = self.add_vertex((cx, cy, z0))
        ct = self.add_vertex((cx, cy, z1))
        for i in range(segments):
            j = (i + 1) % segments
            self.triangles.extend(((cb, bottom[j], bottom[i]), (ct, top[i], top[j])))
            self.quad(bottom[i], bottom[j], top[j], top[i])

    def tube(
        self,
        cx: float,
        cy: float,
        outer: float,
        inner_x: float,
        inner_y: float,
        z0: float,
        z1: float,
        segments: int = 96,
    ) -> None:
        rings: list[list[int]] = []
        for z, rx, ry in ((z0, outer, outer), (z0, inner_x, inner_y),
                          (z1, outer, outer), (z1, inner_x, inner_y)):
            rings.append([
                self.add_vertex((cx + rx * math.cos(2 * math.pi * i / segments),
                                 cy + ry * math.sin(2 * math.pi * i / segments), z))
                for i in range(segments)
            ])
        ob, ib, ot, it = rings
        for i in range(segments):
            j = (i + 1) % segments
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it[i], it[j])
            self.quad(ob[j], ob[i], ib[i], ib[j])
            self.quad(ot[i], ot[j], it[j], it[i])

    def distorted_tube(
        self, cx: float, cy: float, outer: float, inner: float, deviation: float,
        z0: float, z1: float, segments: int = 96,
    ) -> None:
        """Tube whose hole has a controlled radial deviation from a fitted circle."""
        rings: list[list[int]] = []
        for z, is_inner in ((z0, False), (z0, True), (z1, False), (z1, True)):
            ring = []
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                radius = inner + deviation * math.cos(6 * angle) if is_inner else outer
                ring.append(self.add_vertex((cx + radius * math.cos(angle),
                                             cy + radius * math.sin(angle), z)))
            rings.append(ring)
        ob, ib, ot, it = rings
        for i in range(segments):
            j = (i + 1) % segments
            self.quad(ob[i], ob[j], ot[j], ot[i])
            self.quad(ib[j], ib[i], it[i], it[j])
            self.quad(ob[j], ob[i], ib[i], ib[j])
            self.quad(ot[i], ot[j], it[j], it[i])

    def frustum(
        self, cx: float, cy: float, lower: float, upper: float, z0: float, z1: float, segments: int = 64
    ) -> None:
        bottom = [
            self.add_vertex((cx + lower * math.cos(2 * math.pi * i / segments),
                             cy + lower * math.sin(2 * math.pi * i / segments), z0))
            for i in range(segments)
        ]
        top = [
            self.add_vertex((cx + upper * math.cos(2 * math.pi * i / segments),
                             cy + upper * math.sin(2 * math.pi * i / segments), z1))
            for i in range(segments)
        ]
        cb, ct = self.add_vertex((cx, cy, z0)), self.add_vertex((cx, cy, z1))
        for i in range(segments):
            j = (i + 1) % segments
            self.triangles.extend(((cb, bottom[j], bottom[i]), (ct, top[i], top[j])))
            self.quad(bottom[i], bottom[j], top[j], top[i])

    def wedge(
        self, x0: float, x1: float, cy: float, width0: float, width1: float, z0: float, z1: float
    ) -> None:
        points = ((x0, cy - width0 / 2), (x1, cy - width1 / 2),
                  (x1, cy + width1 / 2), (x0, cy + width0 / 2))
        base = [self.add_vertex((x, y, z0)) for x, y in points]
        top = [self.add_vertex((x, y, z1)) for x, y in points]
        self.triangles.extend(((base[0], base[2], base[1]), (base[0], base[3], base[2]),
                               (top[0], top[1], top[2]), (top[0], top[2], top[3])))
        for i in range(4):
            j = (i + 1) % 4
            self.quad(base[i], base[j], top[j], top[i])


def bridge() -> Mesh:
    mesh = Mesh()
    mesh.box(-16, -10, -12, 12, BED_Z, BED_Z + 8)
    mesh.box(10, 16, -12, 12, BED_Z, BED_Z + 8)
    mesh.box(-16, 16, -12, 12, BED_Z + 8, BED_Z + 10)
    return mesh


def internal_bridge() -> Mesh:
    mesh = Mesh()
    # The filter shrinks unsupported areas by either one or three solid-infill
    # spacings.  Include sub-spacing, intermediate and control cavities so the
    # three enum values retain observably different candidates.
    for cx, cavity_width in ((-13, 1.2), (-7, 2.2), (2, 3.4), (13, 8.0)):
        x0, x1 = cx - cavity_width / 2 - 2, cx + cavity_width / 2 + 2
        mesh.box(x0, x1, -8, 8, BED_Z, BED_Z + 2)
        mesh.box(x0, x0 + 2, -8, 8, BED_Z + 2, BED_Z + 10)
        mesh.box(x1 - 2, x1, -8, 8, BED_Z + 2, BED_Z + 10)
        mesh.box(x0 + 2, x1 - 2, -8, -6, BED_Z + 2, BED_Z + 10)
        mesh.box(x0 + 2, x1 - 2, 6, 8, BED_Z + 2, BED_Z + 10)
        mesh.box(x0, x1, -8, 8, BED_Z + 10, BED_Z + 12)
    return mesh


def counterbore() -> Mesh:
    mesh = Mesh()
    # The smaller through-hole starts above a larger lower recess.  At the
    # transition an annulus of material appears over air, which is precisely
    # the surface handled by PerimeterGenerator::process_no_bridge().
    mesh.tube(0, 0, 15, 6, 6, BED_Z, BED_Z + 6)
    mesh.tube(0, 0, 15, 3, 3, BED_Z + 6, BED_Z + 12)
    return mesh


def ironing_steps() -> Mesh:
    mesh = Mesh()
    mesh.box(-15, 15, -12, 12, BED_Z, BED_Z + 4)
    mesh.box(-9, 9, -12, 12, BED_Z + 4, BED_Z + 8)
    mesh.box(-4, 4, -12, 12, BED_Z + 8, BED_Z + 12)
    return mesh


def overhang() -> Mesh:
    mesh = Mesh()
    mesh.box(-8, 8, -12, 12, BED_Z, BED_Z + 4)
    mesh.box(-3, 17, -12, 12, BED_Z + 4, BED_Z + 8)
    mesh.box(2, 22, -12, 12, BED_Z + 8, BED_Z + 12)
    return mesh


def overhang_bands() -> Mesh:
    mesh = Mesh()
    # PerimeterGenerator compares the displacement from the preceding layer
    # with ``(threshold - 50%) * extrusion_width``.  At a 0.2 mm layer and
    # about 0.45 mm wall width, these radial changes per layer sit on opposite
    # sides of the 40/50/60% cut-offs: +0.19, +0.24 and +0.29 mm.
    # Continuous slopes also ensure that an even zero-based layer (the layers
    # on which CrealityPrint alternates the direction) contains the feature.
    for cx, upper in ((-24, 9.8), (0, 10.8), (24, 11.8)):
        mesh.frustum(cx, 0, 6.0, upper, BED_Z, BED_Z + 4, 64)
    return mesh


def overhang_holes() -> Mesh:
    mesh = Mesh()
    for cx, inner in ((-18, 1), (0, 1.5), (18, 2)):
        mesh.tube(cx, 0, 7, inner, inner, BED_Z, BED_Z + 6, 64)
        mesh.cylinder(cx, 0, 7, BED_Z + 6, BED_Z + 10, 64)
    return mesh


def fine_features() -> Mesh:
    mesh = Mesh()
    mesh.cylinder(-9, 0, 7, BED_Z, BED_Z + 10, 128)
    mesh.cylinder(9, 0, 7, BED_Z, BED_Z + 10, 48)
    for i in range(9):
        x = -12 + i * 3
        mesh.box(x, x + 0.18, 8, 14, BED_Z, BED_Z + 6)
    return mesh


def closing_gaps() -> Mesh:
    mesh = Mesh()
    x = -15.0
    for width, gap in ((8, 0.04), (8, 0.08), (8, 0.12), (8, 0)):
        mesh.box(x, x + width, -10, 10, BED_Z, BED_Z + 6)
        x += width + gap
    return mesh


def polyholes(kind: str) -> Mesh:
    mesh = Mesh()
    if kind == "threshold":
        for cx, deviation in ((-18, 0.005), (0, 0.015), (18, 0.03)):
            mesh.distorted_tube(cx, 0, 7, 3, deviation, BED_Z, BED_Z + 10)
    else:
        mesh.tube(0, 0, 15, 5, 5, BED_Z, BED_Z + 12, 128)
    return mesh


def seam_model(mixed: bool = False, overhanging: bool = False) -> Mesh:
    mesh = Mesh()
    if overhanging:
        mesh.frustum(-20, 0, 9, 11, BED_Z, BED_Z + 12)
        mesh.frustum(0, 0, 8, 12, BED_Z, BED_Z + 12)
        mesh.frustum(20, 0, 7, 13, BED_Z, BED_Z + 12)
    else:
        # A 16-gon keeps the base scarf arc coarse enough for seam_slope_steps
        # to add observable subdivisions (the setting is a minimum, not an
        # exact output segment count).
        mesh.cylinder(-20 if mixed else 0, 0, 8, BED_Z, BED_Z + 12, 96 if mixed else 16)
        if mixed:
            mesh.prism([(0, 8), (-6.928, -4), (6.928, -4)], BED_Z, BED_Z + 12)
            mesh.prism([(20, -8), (17, 7), (23, 7)], BED_Z, BED_Z + 12)
    return mesh


def top_widths() -> Mesh:
    mesh = Mesh()
    mesh.box(-20, 20, -12, 12, BED_Z, BED_Z + 5)
    # Upper bars cover the base except for four exposed top-surface channels.
    # Their widths straddle the Arachne filter's 150/200/250% effective limits.
    cursor = -20.0
    for gap in (0.36, 0.48, 0.60, 0.78):
        mesh.box(cursor, cursor + 7.0, -12, 12, BED_Z + 5, BED_Z + 10)
        cursor += 7.0 + gap
    mesh.box(cursor, 20.0, -12, 12, BED_Z + 5, BED_Z + 10)
    return mesh


def thin_ribs() -> Mesh:
    mesh = Mesh()
    for x, width in zip((-12, -7, -2, 3, 8, 13), (0.08, 0.12, 0.2, 0.28, 0.36, 0.48)):
        mesh.box(x - width / 2, x + width / 2, -10, 10, BED_Z, BED_Z + 8)
    mesh.box(17, 20, -10, 10, BED_Z, BED_Z + 8)  # printable control rib
    return mesh


def small_islands() -> Mesh:
    mesh = Mesh()
    for x, side in zip((-15, -8, 0, 9, 18), (0.45, 0.8, 1.4, 2.2, 3.4)):
        mesh.box(x - side / 2, x + side / 2, -side / 2, side / 2, BED_Z, BED_Z + 5)
    return mesh


def arachne_wedges() -> Mesh:
    mesh = Mesh()
    for cy, end_width in ((-9, 0.7), (0, 1.2), (9, 1.8)):
        mesh.wedge(-16, 16, cy, 0.08, end_width, BED_Z, BED_Z + 8)
    return mesh


def distribution_tube() -> Mesh:
    mesh = Mesh()
    # A circular outside and elliptical hole make the wall thickness vary
    # smoothly from 3 to 5 mm around one closed contour.  Six requested wall
    # loops give DistributedBeadingStrategy enough neighboring beads for its
    # radius 1/2/3 weighting to be observable.
    mesh.tube(0, 0, 15, 10, 12, BED_Z, BED_Z + 8, 128)
    return mesh


def plain_box(height: float = 12) -> Mesh:
    mesh = Mesh()
    mesh.box(-12, 12, -12, 12, BED_Z, BED_Z + height)
    return mesh


BUILDERS = {
    "bridge": bridge,
    "internal_bridge": internal_bridge,
    "counterbore": counterbore,
    "ironing_steps": ironing_steps,
    "overhang": overhang,
    "overhang_bands": overhang_bands,
    "overhang_frustum": lambda: (lambda m: (m.frustum(0, 0, 5, 35, BED_Z, BED_Z + 12), m)[1])(Mesh()),
    "overhang_holes": overhang_holes,
    "fine_features": fine_features,
    "closing_gaps": closing_gaps,
    "polyholes": lambda: polyholes("normal"),
    "polyhole_threshold": lambda: polyholes("threshold"),
    "box": plain_box,
    "precise_z": lambda: plain_box(10.13),
    "seam": seam_model,
    "seam_mixed": lambda: seam_model(mixed=True),
    "seam_overhang": lambda: seam_model(overhanging=True),
    "top_widths": top_widths,
    "thin_ribs": thin_ribs,
    "small_islands": small_islands,
    "arachne_wedges": arachne_wedges,
    "distribution_tube": distribution_tube,
}


ARCHETYPE_BY_PARAM = {
    **{key: "bridge" for key in ("bridge_angle", "bridge_density", "bridge_flow", "bridge_speed", "thick_bridges")},
    **{key: "internal_bridge" for key in ("dont_filter_internal_bridges", "internal_bridge_speed", "thick_internal_bridges")},
    "counterbore_hole_bridging": "counterbore",
    **{key: "ironing_steps" for key in ("ironing_type", "ironing_pattern", "ironing_flow", "ironing_spacing", "ironing_speed", "ironing_angle")},
    "line_width": "box",
    "internal_solid_infill_line_width": "ironing_steps",
    **{key: "overhang" for key in ("extra_perimeters_on_overhangs", "overhang_optimization")},
    **{key: "overhang_frustum" for key in ("make_overhang_printable", "make_overhang_printable_angle")},
    "make_overhang_printable_hole_size": "overhang_holes",
    "slice_closing_radius": "closing_gaps",
    "resolution": "fine_features",
    "hole_to_polyhole": "polyholes",
    "hole_to_polyhole_threshold": "polyhole_threshold",
    "hole_to_polyhole_twisted": "polyholes",
    "precise_outer_wall": "box",
    "precise_z_height": "precise_z",
    **{key: "seam" for key in ("seam_position", "seam_gap", "staggered_inner_seams", "seam_slope_type",
                                "scarf_joint_flow_ratio", "seam_slope_entire_loop", "seam_slope_inner_walls",
                                "seam_slope_min_length", "seam_slope_start_height", "seam_slope_steps", "scarf_joint_speed")},
    **{key: "seam_mixed" for key in ("seam_slope_conditional", "scarf_angle_threshold")},
    "scarf_overhang_threshold": "seam_overhang",
    "min_width_top_surface": "top_widths",
    "is_infill_first": "box",
    "only_one_wall_first_layer": "box",
    "detect_thin_wall": "thin_ribs",
    **{key: "overhang" for key in ("detect_overhang_wall", "overhang_reverse", "overhang_reverse_internal_only")},
    "overhang_reverse_threshold": "overhang_bands",
    **{key: "seam" for key in ("wipe_on_loops", "wipe_before_external_loop")},
    **{key: "small_islands" for key in ("small_area_infill_flow_compensation", "small_area_infill_flow_compensation_model")},
    **{key: "arachne_wedges" for key in ("wall_transition_angle", "wall_transition_filter_deviation",
                                          "wall_transition_length", "min_feature_size",
                                          "min_bead_width", "initial_layer_min_bead_width")},
    "wall_distribution_count": "distribution_tube",
}


DEPENDENCIES = {
    "ironing": {"ironing_type": "top", "top_shell_layers": "3"},
    "polyhole": {"hole_to_polyhole": "1"},
    "precise_outer_wall": {"wall_sequence": "inner-outer", "wall_loops": "4",
                           "outer_wall_line_width": "0.36", "inner_wall_line_width": "0.52"},
    "seam": {"wall_loops": "4", "seam_position": "aligned"},
    "scarf": {"wall_loops": "4", "seam_position": "aligned", "seam_slope_type": "external",
              "seam_slope_conditional": "0", "seam_slope_min_length": "12", "seam_slope_steps": "8"},
    "overhang": {"detect_overhang_wall": "1", "enable_support": "0"},
    "make_overhang": {"make_overhang_printable": "1", "enable_support": "0"},
    "arachne": {"wall_generator": "arachne", "wall_loops": "4"},
    "small_area": {"small_area_infill_flow_compensation": "1", "sparse_infill_density": "100%",
                   "top_shell_layers": "0", "bottom_shell_layers": "0"},
}


def dependency_settings(parameter: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if parameter == "line_width":
        # Zero means inherit the common line_width instead of retaining the
        # printer preset's explicit 0.45-mm inner-wall override.
        result.update({"inner_wall_line_width": "0", "wall_loops": "3"})
    if parameter.startswith("ironing_"):
        result.update(DEPENDENCIES["ironing"])
    if parameter.startswith("hole_to_polyhole"):
        result.update(DEPENDENCIES["polyhole"])
        result["enable_arc_fitting"] = "0"
    if parameter == "resolution":
        result["enable_arc_fitting"] = "0"
    if parameter == "precise_outer_wall":
        result.update(DEPENDENCIES["precise_outer_wall"])
    if parameter.startswith("seam_") or parameter.startswith("scarf_") or parameter == "staggered_inner_seams":
        result.update(DEPENDENCIES["seam"])
        result["enable_arc_fitting"] = "0"
    if parameter.startswith("seam_slope_") or parameter.startswith("scarf_"):
        result.update(DEPENDENCIES["scarf"])
    if parameter in {"seam_slope_conditional", "scarf_angle_threshold", "scarf_overhang_threshold"}:
        result["seam_slope_conditional"] = "1"
    if parameter in {"extra_perimeters_on_overhangs", "overhang_optimization", "detect_overhang_wall",
                     "overhang_reverse", "overhang_reverse_internal_only", "overhang_reverse_threshold"}:
        result.update(DEPENDENCIES["overhang"])
    if parameter in {"overhang_reverse_internal_only", "overhang_reverse_threshold"}:
        result.update({"overhang_reverse": "1", "enable_arc_fitting": "0"})
    if parameter == "min_width_top_surface":
        # The top-surface polygon filter is implemented by the Arachne branch
        # of PerimeterGenerator.
        result.update(DEPENDENCIES["arachne"])
    if parameter.startswith("make_overhang_printable"):
        result.update(DEPENDENCIES["make_overhang"])
    if parameter.startswith("wall_transition_") or parameter in {
        "wall_distribution_count", "min_feature_size", "min_bead_width", "initial_layer_min_bead_width"
    }:
        result.update(DEPENDENCIES["arachne"])
    if parameter == "wall_distribution_count":
        result["wall_loops"] = "6"
    if parameter in {"only_one_wall_first_layer", "staggered_inner_seams", "wipe_on_loops", "wipe_before_external_loop"}:
        result["wall_loops"] = "4"
    if parameter.startswith("small_area_infill_flow_compensation"):
        result.update(DEPENDENCIES["small_area"])
    if parameter == "overhang_optimization":
        # The engine validates that this beta adaptive-height feature is not
        # combined with Organic supports. Keep support out of this geometry-only
        # behavior case and inspect generated layer heights/widths directly.
        result.update({"enable_support": "0", "support_type": "normal(auto)", "support_style": "default"})
    return result


def mark_process_overrides(settings: dict[str, object], keys: list[str]) -> None:
    """Tell GUI project loading which process values must override the preset.

    CrealityPrint CLI consumes every value from ``project_settings.config``,
    while the GUI project loader reapplies the selected system preset and only
    preserves process keys listed in the first
    ``different_settings_to_system`` slot.  Generated behavioral projects must
    therefore register both the parameter under test and all prerequisite
    settings, otherwise GUI pytest and CLI validation slice different configs.
    """
    raw_slots = settings.get("different_settings_to_system")
    slots = [str(value) for value in raw_slots] if isinstance(raw_slots, list) else ["", "", ""]
    if not slots:
        slots = ["", "", ""]

    process_keys = [key for key in slots[0].split(";") if key]
    for key in keys:
        if key and key not in process_keys:
            process_keys.append(key)
    slots[0] = ";".join(process_keys)
    settings["different_settings_to_system"] = slots


def model_xml(mesh: Mesh, title: str) -> bytes:
    vertices = "\n".join(
        f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in mesh.vertices
    )
    triangles = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.triangles
    )
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">C3DBaseline quality L1 model designer</metadata>
 <metadata name="Title">{escape(title)}</metadata>
 <resources>
  <object id="1" type="model"><mesh><vertices>
{vertices}
   </vertices><triangles>
{triangles}
   </triangles></mesh></object>
  <object id="2" type="model"><components><component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>
 </resources>
 <build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 110 110 10" printable="1"/></build>
</model>
'''
    return xml.encode("utf-8")


def rewrite_project(path: Path, parameter: str, archetype: str) -> None:
    mesh = BUILDERS[archetype]()
    replacements: dict[str, bytes] = {MODEL_ENTRY: model_xml(mesh, f"{parameter}: {archetype}")}
    with zipfile.ZipFile(path, "r") as source:
        settings = json.loads(source.read(PROJECT_SETTINGS).decode("utf-8-sig"))
        # Normalize legacy values in the original placeholder projects to the
        # current C3DSlicer schema before adding behavioral dependencies.
        if parameter == "seam_slope_type" and settings.get(parameter) == "linear":
            settings[parameter] = "external"
        elif parameter == "scarf_joint_flow_ratio":
            raw = str(settings.get(parameter, "1")).strip()
            settings[parameter] = str(float(raw.rstrip("%")) / 100.0) if raw.endswith("%") else raw
        elif parameter == "scarf_joint_speed" and str(settings.get(parameter)) == "0":
            settings[parameter] = "1"
        elif parameter == "seam_slope_steps" and str(settings.get(parameter)) == "0":
            settings[parameter] = "1"
        elif parameter == "seam_slope_start_height":
            legacy_start_heights = {"0.5": "0.1", "1.0": "0.15", "1": "0.15"}
            raw = str(settings.get(parameter))
            settings[parameter] = legacy_start_heights.get(raw, raw)
        dependencies = dependency_settings(parameter)
        for key, value in dependencies.items():
            if key != parameter:
                settings[key] = value
        mark_process_overrides(settings, [parameter, *dependencies])
        replacements[PROJECT_SETTINGS] = (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if MODEL_SETTINGS in source.namelist():
            model_settings = source.read(MODEL_SETTINGS).decode("utf-8-sig")
            model_settings = re.sub(r'(<metadata key="name" value=")[^"]*("/>)',
                                    rf'\1quality_{archetype}\2', model_settings)
            replacements[MODEL_SETTINGS] = model_settings.encode("utf-8")
        entries = [
            (info, replacements.get(info.filename, source.read(info.filename)))
            for info in source.infolist()
        ]

    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".3mf", delete=False) as temporary:
        temp_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as target:
            for info, payload in entries:
                target.writestr(info, payload)
        temp_path.replace(path)
    finally:
        temp_path.unlink(missing_ok=True)


def iter_projects(repo: Path):
    case_root = repo / "test_framework/engine_params/data/case_input/process/quality"
    model_root = repo / "test_framework/engine_params/data/models/process/quality"
    for case_json in sorted(case_root.rglob("*.json")):
        parameter = case_json.stem
        archetype = ARCHETYPE_BY_PARAM.get(parameter)
        group = case_json.parent.name
        # quality/ironing_type is the existing extrusion-block (non-L1) suite;
        # only quality/ironing/test_ironing.py::test_ironing_type is in scope.
        if archetype is None or group == "ironing_type":
            continue
        data = json.loads(case_json.read_text(encoding="utf-8-sig"))
        for case in data["cases"]:
            yield parameter, archetype, model_root / group / parameter / case["input_3mf"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rewrite the 3MF projects")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument(
        "--parameter",
        action="append",
        dest="parameters",
        help="limit rewriting to one parameter; may be supplied more than once",
    )
    args = parser.parse_args()

    count = 0
    for parameter, archetype, path in iter_projects(args.repo):
        if args.parameters and parameter not in args.parameters:
            continue
        if not path.exists():
            raise FileNotFoundError(path)
        print(f"{parameter:45s} {archetype:20s} {path.name}")
        if args.apply:
            rewrite_project(path, parameter, archetype)
        count += 1
    print(f"{'updated' if args.apply else 'planned'} {count} quality L1 3MF projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
