#!/usr/bin/env python3
"""Build a support-enabled project 3MF from an STL using a Creality 3MF as host.

Swaps the host's mesh for the STL geometry (recentered on the bed), flips
enable_support on in the embedded project_settings.config, and keeps every
other embedded parameter — so both owzx-cli (via --load-settings) and Orca
(native) slice with byte-identical settings.

Usage: make_support_tower_3mf.py <model.stl> <host.3mf> <out.3mf>
"""

import json
import re
import struct
import sys
import zipfile


def read_stl_triangles(path):
    with open(path, "rb") as f:
        f.seek(80)
        (n,) = struct.unpack("<I", f.read(4))
        tris = []
        for _ in range(n):
            vals = struct.unpack("<12fH", f.read(50))
            tris.append((vals[3:6], vals[6:9], vals[9:12]))
        return tris


def main(stl, host, dst):
    tris = read_stl_triangles(stl)

    verts, faces = [], []
    idx = 0
    for a, b, c in tris:
        for v in (a, b, c):
            verts.append(f'<vertex x="{v[0]+110:.4f}" y="{v[1]+110:.4f}" z="{v[2]:.4f}"/>')
        faces.append(f'<triangle v1="{idx}" v2="{idx+1}" v3="{idx+2}"/>')
        idx += 3

    obj_model = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
        'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
        'requiredextensions="p">\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <resources>\n  <object id="1" type="model">\n   <mesh>\n    <vertices>\n'
        + "\n".join(verts)
        + "\n    </vertices>\n    <triangles>\n"
        + "\n".join(faces)
        + "\n    </triangles>\n   </mesh>\n  </object>\n </resources>\n</model>\n"
    )

    with zipfile.ZipFile(host) as zf:
        entries = {n: zf.read(n) for n in zf.namelist()}

    root = entries["3D/3dmodel.model"].decode("utf-8")
    root = re.sub(
        r'(<item objectid="\d+"[^>]*transform=")[^"]*(")',
        r"\g<1>1 0 0 0 1 0 0 0 1 0 0 0\g<2>",
        root,
    )
    entries["3D/3dmodel.model"] = root.encode("utf-8")
    entries["3D/Objects/object_3.model"] = obj_model.encode("utf-8")

    cfg = json.loads(entries["Metadata/project_settings.config"])
    cfg["enable_support"] = "1"
    entries["Metadata/project_settings.config"] = json.dumps(
        cfg, ensure_ascii=False, indent="\t"
    ).encode("utf-8")

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            if name.startswith("Metadata/") and name.endswith(".png"):
                continue  # stale thumbnails for swapped geometry
            zf.writestr(name, data)

    print(f"written: {dst} ({len(tris)} triangles, enable_support=1)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
