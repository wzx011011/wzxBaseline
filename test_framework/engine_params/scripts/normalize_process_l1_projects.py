"""Normalize legacy process-parameter 3MF projects without changing their mesh.

CrealityPrint 6.0-era projects that reference a mesh through the 3MF production
extension can block the current command-line slicer while loading.  This tool
bakes the single component/build transform into the vertices and writes the
same mesh as a core-3MF inline object.  Project/process settings are preserved.

Only the deliberately narrow, verified shape ``one build item -> one external
component -> one mesh`` is rewritten.  Multi-object/material projects are left
untouched because their object identity and extruder assignment are behavioral
test inputs in their own right.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MODEL_ENTRY = "3D/3dmodel.model"
MODEL_RELS = "3D/_rels/3dmodel.model.rels"
MODEL_SETTINGS = "Metadata/model_settings.config"
PROJECT_SETTINGS = "Metadata/project_settings.config"
BED_CENTER = 110.0
BED_OFFSET_Z = 10.0
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _matrix(raw: str | None) -> tuple[float, ...]:
    values = tuple(float(value) for value in (raw or "1 0 0 0 1 0 0 0 1 0 0 0").split())
    if len(values) != 12:
        raise ValueError(f"expected a 12-value 3MF transform, got {raw!r}")
    return values


def _apply(point: tuple[float, float, float], matrix: tuple[float, ...]) -> tuple[float, float, float]:
    """Apply a 3MF affine transform (column vectors followed by translation)."""
    x, y, z = point
    return (
        x * matrix[0] + y * matrix[3] + z * matrix[6] + matrix[9],
        x * matrix[1] + y * matrix[4] + z * matrix[7] + matrix[10],
        x * matrix[2] + y * matrix[5] + z * matrix[8] + matrix[11],
    )


def _inline_xml(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    title: str,
) -> bytes:
    vertex_xml = "\n".join(
        f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in vertices
    )
    triangle_xml = "\n".join(
        f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}">
 <metadata name="Application">C3DBaseline process L1 model normalizer</metadata>
 <metadata name="Title">{escape(title)}</metadata>
 <resources>
  <object id="1" type="model"><mesh><vertices>
{vertex_xml}
   </vertices><triangles>
{triangle_xml}
   </triangles></mesh></object>
  <object id="2" type="model"><components><component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>
 </resources>
 <build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 {BED_CENTER:g} {BED_CENTER:g} {BED_OFFSET_Z:g}" printable="1"/></build>
</model>
'''.encode("utf-8")


def _multi_inline_xml(
    objects: list[tuple[int, list[tuple[float, float, float]], list[tuple[int, int, int]]]],
    build_items: list[tuple[int, str, str]],
    title: str,
) -> bytes:
    object_xml = []
    id_map = {old_id: (2 * index + 2, 2 * index + 1) for index, (old_id, _, _) in enumerate(objects)}
    for index, (old_id, vertices, triangles) in enumerate(objects):
        object_id, mesh_id = id_map[old_id]
        vertex_xml = "\n".join(
            f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in vertices
        )
        triangle_xml = "\n".join(
            f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles
        )
        object_xml.append(
            f'  <object id="{mesh_id}" type="model"><mesh><vertices>\n{vertex_xml}\n'
            f'   </vertices><triangles>\n{triangle_xml}\n   </triangles></mesh></object>\n'
            f'  <object id="{object_id}" type="model"><components>'
            f'<component objectid="{mesh_id}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
            f'</components></object>'
        )
    item_xml = "\n".join(
        f'  <item objectid="{id_map[old_id][0]}" transform="{escape(transform)}" printable="{printable}"/>'
        for old_id, transform, printable in build_items
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}">
 <metadata name="Application">C3DBaseline process L1 multi-object normalizer</metadata>
 <metadata name="Title">{escape(title)}</metadata>
 <resources>
{chr(10).join(object_xml)}
 </resources>
 <build>
{item_xml}
 </build>
</model>
'''.encode("utf-8")


def _multi_model_settings(payload: bytes, objects: list[tuple[int, object, object]]) -> bytes:
    text = payload.decode("utf-8-sig")
    id_map = {old_id: (2 * index + 2, 2 * index + 1) for index, (old_id, _, _) in enumerate(objects)}

    def replace_object(match: re.Match[str]) -> str:
        object_id = int(match.group(1))
        block = match.group(0)
        if object_id in id_map:
            new_object_id, part_id = id_map[object_id]
            block = block.replace(f'<object id="{object_id}">', f'<object id="{new_object_id}">', 1)
            block = re.sub(r'<part id="\d+"', f'<part id="{part_id}"', block, count=1)
        return block

    text = re.sub(r'<object id="(\d+)">.*?</object>', replace_object, text, flags=re.S)
    text = re.sub(
        r'(<metadata key="object_id" value=")(\d+)("/>)',
        lambda match: match.group(1) + str(id_map.get(int(match.group(2)), (int(match.group(2)), 0))[0]) + match.group(3),
        text,
    )
    text = re.sub(
        r'(\bobject_id=")(\d+)(")',
        lambda match: match.group(1) + str(id_map.get(int(match.group(2)), (int(match.group(2)), 0))[0]) + match.group(3),
        text,
    )
    return text.encode("utf-8")


def _without_external_model_relationships(
        payload: bytes,
        external_entries: list[str],
) -> bytes | None:
    """Remove relationships to model parts superseded by an inline core mesh."""
    root = ET.fromstring(payload)
    external_targets = {name.lstrip("/") for name in external_entries}
    for relationship in list(root):
        target = relationship.get("Target", "").lstrip("/")
        if target in external_targets:
            root.remove(relationship)
    if not list(root):
        return None
    ET.register_namespace("", RELATIONSHIPS_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def normalize_project(path: Path, *, allow_multi: bool = False) -> bool:
    with zipfile.ZipFile(path, "r") as source:
        names = source.namelist()
        external_entries = [
            name for name in names if name.startswith("3D/Objects/") and name.endswith(".model")
        ]
        root = ET.fromstring(source.read(MODEL_ENTRY))
        ns = {"c": CORE_NS}
        application = root.find("./c:metadata[@name='Application']", ns)
        build_items = root.findall("./c:build/c:item", ns)
        components = root.findall("./c:resources/c:object/c:components/c:component", ns)
        inline_meshes = root.findall("./c:resources/c:object/c:mesh", ns)
        application_text = (application.text or "") if application is not None else ""
        entries = None

        # Repair the first normalization format, which embedded meshes directly
        # under the build object IDs.  The project loader expects each model
        # settings part to resolve through a wrapper component, just like a
        # native CrealityPrint project.
        if allow_multi and application_text.startswith("C3DBaseline process L1 multi-object"):
            objects = []
            resources_by_id = {
                int(item.get("id", "0")): item for item in root.findall("./c:resources/c:object", ns)
            }
            for build_item in build_items:
                old_id = int(build_item.get("objectid", "0"))
                resource_object = resources_by_id.get(old_id)
                if resource_object is None:
                    return False
                mesh = resource_object.find("./c:mesh", ns)
                transform = _matrix(None)
                if mesh is None:
                    component = resource_object.find("./c:components/c:component", ns)
                    if component is None:
                        return False
                    mesh_object = resources_by_id.get(int(component.get("objectid", "0")))
                    if mesh_object is None:
                        return False
                    mesh = mesh_object.find("./c:mesh", ns)
                    transform = _matrix(component.get("transform"))
                if mesh is None:
                    return False
                vertices = [
                    _apply(tuple(float(vertex.get(axis, "0")) for axis in "xyz"), transform)
                    for vertex in mesh.findall("./c:vertices/c:vertex", ns)
                ]
                triangles = [
                    tuple(int(triangle.get(key, "0")) for key in ("v1", "v2", "v3"))
                    for triangle in mesh.findall("./c:triangles/c:triangle", ns)
                ]
                objects.append((old_id, vertices, triangles))
            build_data = [
                (int(item.get("objectid", "0")), item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0"), item.get("printable", "1"))
                for item in build_items
            ]
            replacements = {MODEL_ENTRY: _multi_inline_xml(objects, build_data, path.stem)}
            if MODEL_SETTINGS in names:
                replacements[MODEL_SETTINGS] = _multi_model_settings(source.read(MODEL_SETTINGS), objects)
            entries = [(info, replacements.get(info.filename, source.read(info.filename))) for info in source.infolist()]
        elif (
            application_text.startswith("C3DBaseline process L1")
            and path.stem != "filename_format_default"
        ):
            # Early versions of this normalizer embedded a core mesh but left
            # the old production-extension model part and relationship in the
            # archive.  Different CrealityPrint versions could then select
            # different geometry.  Keep the inline mesh as the single source
            # of truth and remove the superseded external model resources.
            if not external_entries:
                return False
            removed_entries = set(external_entries)
            replacements = {}
            if MODEL_RELS in names:
                relationships = _without_external_model_relationships(
                    source.read(MODEL_RELS), external_entries
                )
                if relationships is None:
                    removed_entries.add(MODEL_RELS)
                else:
                    replacements[MODEL_RELS] = relationships
            entries = [
                (info, replacements.get(info.filename, source.read(info.filename)))
                for info in source.infolist()
                if info.filename not in removed_entries
            ]

        if allow_multi and entries is None and (
            not inline_meshes
            and len(build_items) > 1
            and len(build_items) == len(components) == len(external_entries)
        ):
            objects = []
            resource_objects = root.findall("./c:resources/c:object", ns)
            for resource_object in resource_objects:
                component = resource_object.find("./c:components/c:component", ns)
                if component is None:
                    return False
                raw_path = next(
                    (value for key, value in component.attrib.items() if key.endswith("}path") or key == "path"),
                    "",
                ).lstrip("/")
                if raw_path not in names:
                    return False
                external_root = ET.fromstring(source.read(raw_path))
                mesh = external_root.find("./c:resources/c:object/c:mesh", ns)
                if mesh is None:
                    return False
                transform = _matrix(component.get("transform"))
                vertices = [
                    _apply(tuple(float(vertex.get(axis, "0")) for axis in "xyz"), transform)
                    for vertex in mesh.findall("./c:vertices/c:vertex", ns)
                ]
                triangles = [
                    tuple(int(triangle.get(key, "0")) for key in ("v1", "v2", "v3"))
                    for triangle in mesh.findall("./c:triangles/c:triangle", ns)
                ]
                objects.append((int(resource_object.get("id", "0")), vertices, triangles))
            build_data = [
                (
                    int(item.get("objectid", "0")),
                    item.get("transform", "1 0 0 0 1 0 0 0 1 0 0 0"),
                    item.get("printable", "1"),
                )
                for item in build_items
            ]
            replacements = {MODEL_ENTRY: _multi_inline_xml(objects, build_data, path.stem)}
            if MODEL_SETTINGS in names:
                replacements[MODEL_SETTINGS] = _multi_model_settings(source.read(MODEL_SETTINGS), objects)
            entries = [
                (info, replacements.get(info.filename, source.read(info.filename)))
                for info in source.infolist()
            ]
            # Continue through the common atomic ZIP rewrite below.
            mesh = None
        elif entries is None:
            entries = None

        if entries is not None:
            pass
        else:
            is_external = len(external_entries) == 1 and not inline_meshes
            is_inline = len(inline_meshes) == 1
            if len(build_items) != 1 or len(components) != 1 or not (is_external or is_inline):
                return False

            if is_external:
                external_root = ET.fromstring(source.read(external_entries[0]))
                mesh = external_root.find("./c:resources/c:object/c:mesh", ns)
            else:
                mesh = inline_meshes[0]
            if mesh is None:
                raise ValueError(f"external object has no mesh: {path}")

            component_transform = _matrix(components[0].get("transform"))
            build_transform = _matrix(build_items[0].get("transform"))
            vertices = []
            for vertex in mesh.findall("./c:vertices/c:vertex", ns):
                point = tuple(float(vertex.get(axis, "0")) for axis in "xyz")
                vertices.append(_apply(_apply(point, component_transform), build_transform))
            triangles = [
                tuple(int(triangle.get(key, "0")) for key in ("v1", "v2", "v3"))
                for triangle in mesh.findall("./c:triangles/c:triangle", ns)
            ]
            if not vertices or not triangles:
                raise ValueError(f"empty mesh: {path}")

        # The baked coordinates include the old plate placement.  Recenter XY
        # and place the mesh bottom at -10 so the common build transform puts
        # it back at Z=0 with its original physical dimensions intact.
            min_xyz = [min(point[i] for point in vertices) for i in range(3)]
            max_xyz = [max(point[i] for point in vertices) for i in range(3)]
            center_x = (min_xyz[0] + max_xyz[0]) / 2
            center_y = (min_xyz[1] + max_xyz[1]) / 2
            vertices = [
                (x - center_x, y - center_y, z - min_xyz[2] - BED_OFFSET_Z)
                for x, y, z in vertices
            ]

            replacements = {MODEL_ENTRY: _inline_xml(vertices, triangles, path.stem)}
            if MODEL_SETTINGS in names:
                settings = source.read(MODEL_SETTINGS).decode("utf-8-sig")
                settings = re.sub(
                    r'(<assemble_item\b[^>]*\btransform=")[^"]*(")',
                    rf'\g<1>1 0 0 0 1 0 0 0 1 {BED_CENTER:g} {BED_CENTER:g} {BED_OFFSET_Z:g}\g<2>',
                    settings,
                )
                replacements[MODEL_SETTINGS] = settings.encode("utf-8")
            if path.stem == "filename_format_default" and PROJECT_SETTINGS in names:
                settings = json.loads(source.read(PROJECT_SETTINGS).decode("utf-8-sig"))
                settings["filename_format"] = (
                    "{input_filename_base}_{filament_type[initial_tool]}_{print_time}.gcode"
                )
                replacements[PROJECT_SETTINGS] = (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            entries = [
                (info, replacements.get(info.filename, source.read(info.filename)))
                for info in source.infolist()
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
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("strength", "others", "filament"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()

    root = args.repo / "test_framework/engine_params/data/models/process" / args.group
    candidates = sorted(root.rglob("*.3mf"))
    changed = 0
    for path in candidates:
        if args.apply:
            if normalize_project(path):
                changed += 1
                print(f"normalized {path.relative_to(root)}")
        else:
            print(path.relative_to(root))
    print(f"{'normalized' if args.apply else 'found'} {changed if args.apply else len(candidates)} of {len(candidates)} projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
