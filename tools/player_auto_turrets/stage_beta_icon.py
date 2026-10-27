"""Stage the user's beta icon in the workspace, with private resource names.

No game installation is modified. No proprietary bitmap/model is committed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
from generate_station_lods import read_tree, write_tree, crc


def stage(source: Path, output: Path, prefix='player_auto_turret', ui_materials=True):
    source, output = source.resolve(), output.resolve()
    if not output.is_relative_to(REPO / "src" / "obj"):
        raise ValueError("Output must stay under this workspace's src/obj directory")
    if source == output:
        raise ValueError("Source must not be overwritten")
    raw = source.read_bytes()
    header, roots = read_tree(raw)
    root = roots[0]
    libraries = {node.name.lower(): node for node in root.children}
    materials = libraries["material library"]
    textures = libraries["texture library"]
    meshes = libraries["vmeshlibrary"]
    material_ids, mesh_ids, texture_names = {}, {}, {}
    for i, node in enumerate(textures.children):
        name = f"{prefix}_texture_{i}.tga"
        texture_names[node.name.lower()] = name
        node.name = name
    for i, node in enumerate(materials.children):
        if node.blob is not None:
            continue
        name = f"{'UI_' if ui_materials else ''}{prefix}_material_{i}"
        material_ids[crc(node.name)] = crc(name)
        node.name = name
        for leaf in node.children:
            if leaf.name.lower() == "dt_name":
                old = leaf.blob.rstrip(b"\0").decode("ascii").lower()
                leaf.blob = texture_names[old].encode("ascii") + b"\0"
    for i, node in enumerate(meshes.children):
        name = f"{prefix}_mesh_{i}.vms"
        mesh_ids[crc(node.name)] = crc(name)
        node.name = name
        for leaf in node.children:
            if leaf.name.lower() == "vmeshdata":
                blob = bytearray(leaf.blob)
                count = struct.unpack_from("<H", blob, 8)[0]
                for group in range(count):
                    offset = 16 + group * 12
                    old = struct.unpack_from("<I", blob, offset)[0]
                    struct.pack_into("<I", blob, offset, material_ids[old])
                leaf.blob = bytes(blob)

    def fix_refs(nodes):
        for node in nodes:
            if node.name.lower() in ("vmeshref", "vwiredata"):
                blob = bytearray(node.blob)
                old = struct.unpack_from("<I", blob, 4)[0]
                struct.pack_into("<I", blob, 4, mesh_ids[old])
                node.blob = bytes(blob)
            fix_refs(node.children)
    fix_refs(roots)
    result = write_tree(header, roots)
    # Ensure the repacked UTF is parseable and every leaf round-trips byte-for-byte.
    _, check = read_tree(result)
    def leaves(nodes, path=""):
        return {key: value for node in nodes for key, value in
                (leaves(node.children, path + "/" + node.name).items() if node.blob is None
                 else [(path + "/" + node.name, node.blob)])}
    assert leaves(roots) == leaves(check)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    manifest = {"source": str(source), "source_sha256": hashlib.sha256(raw).hexdigest(),
                "output": str(output), "sha256": hashlib.sha256(result).hexdigest(),
                "materials": len(material_ids), "meshes": len(mesh_ids), "textures": len(texture_names)}
    output.with_suffix(".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=REPO / "src/obj/player_auto_turrets/stage/DATA/INTERFACE/HUD/HUD_player_auto_turret.3db")
    parser.add_argument("--prefix", default="player_auto_turret")
    parser.add_argument("--background", action="store_true", help="Preserve authored background colours instead of button UI tinting")
    args = parser.parse_args()
    stage(args.source, args.output, args.prefix, not args.background)
