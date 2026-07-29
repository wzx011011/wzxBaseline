"""Design two-material behavior models for filament L1 parameter cases.

The legacy projects configured two filaments but contained only one material
part, so C3DSlicer legitimately removed the otherwise unnecessary wipe tower.
This tool preserves every process/printer/filament setting and replaces only
the model graph with a current core-3MF two-part object.  The parts use T0/T1,
contain sparse infill and include an overhang so flush-to-infill, flush-to-
support and wipe-tower behavior all have observable G-code evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


MODEL_ENTRY = "3D/3dmodel.model"
MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
PROCESS_SETTINGS = "Metadata/process_settings_1.config"
CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
CURRENT_PROJECT_VERSION = "7.2.1"


@dataclass
class Mesh:
    vertices: list[tuple[float, float, float]] = field(default_factory=list)
    triangles: list[tuple[int, int, int]] = field(default_factory=list)

    def box(self, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
        base = len(self.vertices)
        self.vertices.extend((
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
        ))

    def extrude_y(self, profile: list[tuple[float, float]], y0: float, y1: float) -> None:
        """Extrude a convex X/Z profile into one watertight mesh."""
        base = len(self.vertices)
        self.vertices.extend((x, y0, z) for x, z in profile)
        self.vertices.extend((x, y1, z) for x, z in profile)
        count = len(profile)
        # End caps.  The profile is counter-clockwise in the X/Z plane.
        for index in range(1, count - 1):
            self.triangles.append((base, base + index + 1, base + index))
            self.triangles.append((base + count, base + count + index, base + count + index + 1))
        for index in range(count):
            next_index = (index + 1) % count
            a, b = base + index, base + next_index
            c, d = base + count + next_index, base + count + index
            self.triangles.extend(((a, b, c), (a, c, d)))
        self.triangles.extend(tuple(base + value for value in triangle) for triangle in (
            (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
            (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
            (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
        ))


def behavior_mesh() -> Mesh:
    mesh = Mesh()
    # A single watertight body avoids the coincident internal faces produced by
    # stacked boxes.  Its narrow lower section exposes sparse infill while the
    # widening shoulder exceeds the support threshold and creates real support.
    mesh.extrude_y(
        [(-7, -10), (7, -10), (11, -2), (11, 10), (-11, 10), (-11, -2)],
        -9,
        9,
    )
    return mesh


def _mesh_xml(mesh: Mesh, object_id: int) -> str:
    vertices = "\n".join(
        f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in mesh.vertices
    )
    triangles = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.triangles
    )
    return (
        f'  <object id="{object_id}" type="model"><mesh><vertices>\n{vertices}\n'
        f'   </vertices><triangles>\n{triangles}\n   </triangles></mesh></object>'
    )


def model_xml(title: str) -> bytes:
    mesh = behavior_mesh()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">
 <metadata name="Application">Creality_Print V7.0.0.3676 Beta</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{title}</metadata>
 <resources>
{_mesh_xml(mesh, 1)}
{_mesh_xml(mesh, 2)}
  <object id="3" type="model"><components>
   <component objectid="1" transform="1 0 0 0 1 0 0 0 1 4.77800735 1.37154748 0"/>
   <component objectid="2" transform="1 0 0 0 1 0 0 0 1 -4.77800735 -1.37154748 0"/>
  </components></object>
 </resources>
 <build><item objectid="3" transform="1 0 0 0 1 0 0 0 1 125.221993 128.628453 10" printable="1"/></build>
</model>
'''.encode("utf-8")


def reshape_native_model(payload: bytes) -> bytes:
    """Keep the native topology/IDs and only reshape its cube vertices."""
    text = payload.decode("utf-8")

    def replace_vertex(match: re.Match[str]) -> str:
        x, y, z = (float(match.group(name)) for name in ("x", "y", "z"))
        width = 7.0
        # Shift the top strongly in +X.  With the original eight-vertex cube
        # topology this produces a valid slanted overhang that auto-support can
        # detect, while retaining all native object/volume relationships.
        shift = 0.0 if z < 0 else 50.0
        new_x = (width if x > 0 else -width) + shift
        new_y = 9.0 if y > 0 else -9.0
        return f'<vertex x="{new_x:g}" y="{new_y:g}" z="{z:g}"/>'

    return re.sub(
        r'<vertex x="(?P<x>[-+0-9.eE]+)" y="(?P<y>[-+0-9.eE]+)" z="(?P<z>[-+0-9.eE]+)"\s*/>',
        replace_vertex,
        text,
    ).encode("utf-8")


def configure_wall_part_extruders(payload: bytes, wall_filament: int) -> bytes:
    """Keep wall-filament cases valid while exposing role-level reassignment.

    The native two-material fixture binds its two parts to T0/T1.  That is
    required for wipe-tower and flushing tests, but it masks wall_filament:
    The ``=1`` fixture binds both parts to T0, so all wall paths must remain on
    T0.  The ``=2`` fixture retains the native T0/T1 material declarations;
    its assertion requires at least 95% of wall extrusion on T1, which proves
    the wall role overrides the otherwise mixed part distribution.
    """
    text = payload.decode("utf-8")
    if wall_filament == 2:
        return payload

    def use_t0(match: re.Match[str]) -> str:
        return re.sub(
            r'(<metadata key="extruder" value=")\d+("/>)',
            r'\g<1>1\2',
            match.group(0),
        )

    text = re.sub(r'<part\b[^>]*>.*?</part>', use_t0, text, flags=re.DOTALL)
    return text.encode("utf-8")


def model_settings_xml(title: str) -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="3">
    <metadata key="name" value="{title}"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="material_1_overhang"/>
      <metadata key="matrix" value="1 0 0 -14 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="1"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
    <part id="2" subtype="normal_part">
      <metadata key="name" value="material_2_overhang"/>
      <metadata key="matrix" value="1 0 0 14 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="2"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <metadata key="thumbnail_no_light_file" value="Metadata/plate_no_light_1.png"/>
    <metadata key="top_file" value="Metadata/top_1.png"/>
    <metadata key="pick_file" value="Metadata/pick_1.png"/>
    <model_instance><metadata key="object_id" value="3"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="301"/></model_instance>
  </plate>
  <assemble><assemble_item object_id="3" instance_id="0" transform="1 0 0 0 1 0 0 0 1 110 110 10" offset="0 0 0"/></assemble>
</config>
'''.encode("utf-8")


def rewrite_project(path: Path, parameter: str) -> None:
    repo = Path(__file__).resolve().parents[3]
    template = (
        repo / "test_framework/engine_params/data/models/process/filament/"
        "interlocking/interlocking_beam/interlocking_beam_false.3mf"
    )
    with zipfile.ZipFile(path, "r") as source:
        settings = json.loads(source.read(PROJECT_SETTINGS).decode("utf-8-sig"))
    # Keep the behavior visible on a compact model and prevent top/bottom
    # shells from consuming the complete lower body.
    settings["sparse_infill_density"] = "20%"
    settings["top_shell_layers"] = "3"
    settings["bottom_shell_layers"] = "3"
    if parameter == "wall_filament":
        # Parameter tests load projects through the GUI.  Mark role-filament
        # fixtures as current projects so 7.2 does not reinterpret the legacy
        # 1/1/1 role assignment as the new 0/0/0 default/inherited value.
        settings["version"] = CURRENT_PROJECT_VERSION
    replacements = {
        PROJECT_SETTINGS: (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    # CrealityPrint resolves volume/extruder assignments through several
    # companion metadata files (plate, slice, process and filament records).
    # Start from the complete known-good native two-material project and only
    # replace the mesh and the case-specific project settings.
    with zipfile.ZipFile(template, "r") as source_template:
        native_project = json.loads(source_template.read(PROJECT_SETTINGS).decode("utf-8-sig"))
        for key, native_value in native_project.items():
            current_value = settings.get(key)
            if not isinstance(native_value, list) or not isinstance(current_value, list):
                continue
            if len(native_value) == 2 and len(current_value) == 1:
                settings[key] = [current_value[0], current_value[0]]
            elif key in {
                "flush_volumes_matrix",
                "flush_volumes_vector",
                "wiping_volumes_extruders",
                "wiping_volumes_matrix",
            } and len(current_value) < len(native_value):
                settings[key] = native_value
        replacements[PROJECT_SETTINGS] = (
            json.dumps(settings, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        replacements[MODEL_ENTRY] = reshape_native_model(source_template.read(MODEL_ENTRY))
        process_settings = json.loads(source_template.read(PROCESS_SETTINGS).decode("utf-8-sig"))
        process_settings.update({key: value for key, value in settings.items() if key in process_settings})
        if parameter == "wall_filament":
            process_settings["version"] = CURRENT_PROJECT_VERSION
        replacements[PROCESS_SETTINGS] = (
            json.dumps(process_settings, ensure_ascii=False, indent=4) + "\n"
        ).encode("utf-8")
        if parameter == "wall_filament":
            replacements[MODEL_SETTINGS] = configure_wall_part_extruders(
                source_template.read(MODEL_SETTINGS), int(settings["wall_filament"])
            )
            replacements[MODEL_ENTRY] = replacements[MODEL_ENTRY].replace(
                b"Creality_Print V7.0.0.3676 Beta",
                b"C3DBaseline filament L1 model",
            )
            replacements["Metadata/creality.config"] = re.sub(
                rb'(<metadata key="AppVersion" value=")[^"]+("/>)',
                rf'\g<1>{CURRENT_PROJECT_VERSION}\2'.encode("ascii"),
                source_template.read("Metadata/creality.config"),
            )
        entries = [
            (info, replacements.get(info.filename, source_template.read(info.filename)))
            for info in source_template.infolist()
        ]

    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".3mf", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as target:
            for info, payload in entries:
                target.writestr(info, payload)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def iter_projects(repo: Path):
    case_root = repo / "test_framework/engine_params/data/case_input/process/filament"
    model_root = repo / "test_framework/engine_params/data/models/process/filament"
    selected_groups = {"extruder_assignment", "flush_options", "prime_tower"}
    for case_json in sorted(case_root.rglob("*.json")):
        relative = case_json.parent.relative_to(case_root)
        if relative.parts[0] not in selected_groups or case_json.stem == "tc_wt_007":
            continue
        data = json.loads(case_json.read_text(encoding="utf-8-sig"))
        for case in data["cases"]:
            nested = model_root / relative / case_json.stem / case["input_3mf"]
            direct = model_root / case_json.stem / case["input_3mf"]
            # Match model_or_baseline_path(): a direct parameter directory has
            # priority over the optional feature-subgroup directory.
            yield case_json.stem, direct if direct.exists() else nested


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--parameter", action="append", default=[])
    parser.add_argument("--project", action="append", default=[])
    args = parser.parse_args()
    count = 0
    for parameter, path in iter_projects(args.repo):
        if args.parameter and parameter not in args.parameter:
            continue
        if args.project and path.stem not in args.project:
            continue
        print(f"{parameter:35s} {path.name}")
        if args.apply:
            rewrite_project(path, parameter)
        count += 1
    print(f"{'updated' if args.apply else 'planned'} {count} filament behavior projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
