"""Bounded PN-triangle refinement of a rigid Freelancer asteroid (offline prototype).

Preserves both UV sets, material IDs and the original vertex prefix used by VMeshWire.
Source/game files are read-only. Outputs belong under src/obj/procedural_asteroids.
Requires numpy and Pillow. No neural model, game executable or renderer build is used.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
from generate_station_lods import read_tree, write_tree, child
from repair_panel_normals import leaves


def crc(name):
    text = (REPO / "src/dacom/dacom.cpp").read_text()
    import re
    block = text.split("G_Crc32Table[256] = {", 1)[1].split("};", 1)[0]
    table = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)u", block)]
    if len(table) != 256:
        raise ValueError("Unknown DACOM CRC table")
    value = 0xffffffff
    for byte in name.lower().encode("ascii"):
        value = table[(value & 255) ^ byte] ^ (value >> 8)
    return value ^ 0xffffffff


def decode(blob):
    h = struct.unpack_from("<II4H", blob)
    flags, primitive, groups, count, fvf, nv = h
    if primitive != 4 or groups != 1 or fvf not in (0x112, 0x212, 0x252) or count % 3:
        raise ValueError("Prototype supports one XYZ/N/UV[2] triangle-list material")
    material, low, high, used, unused = struct.unpack_from("<I4H", blob, 16)
    tex_count = (fvf >> 8) & 15
    stride = 6 + 2*tex_count + (1 if fvf & 0x40 else 0)
    if used != count or len(blob) != 28 + 2*count + 4*stride*nv:
        raise ValueError("Unexpected mesh ranges")
    indices = np.frombuffer(blob, "<u2", count, 28).astype(np.int64)
    if flags & 1:
        indices += low
    if indices.max() >= nv or high >= nv:
        raise ValueError("Invalid vertex range")
    raw = np.frombuffer(blob, "<f4", nv*stride, 28+2*count).reshape(nv, stride)
    if fvf & 0x40:
        packed = raw[:, 6].copy().view("<u4")
        colors = np.stack([(packed >> shift) & 255 for shift in (16, 8, 0, 24)], axis=1).astype(float)/255
        vertices = np.concatenate((raw[:, :6], raw[:, 7:], colors), axis=1)
    else:
        vertices = raw.astype(float)
    return h, (material, unused), vertices, indices.reshape(-1, 3)


def encode_vertices(vertices, fvf):
    if not (fvf & 0x40):
        return vertices.astype("<f4").tobytes()
    count = (fvf >> 8) & 15
    result = np.empty((len(vertices), 7+2*count), dtype="<f4")
    result[:, :6] = vertices[:, :6]
    result[:, 7:] = vertices[:, 6:6+2*count]
    colors = np.rint(np.clip(vertices[:, -4:], 0, 1)*255).astype("<u4")
    packed = colors[:, 0] << 16 | colors[:, 1] << 8 | colors[:, 2] | colors[:, 3] << 24
    result[:, 6] = packed.view("<f4")
    return result.tobytes()


def topology(points, faces, allow_open=False):
    edges = collections.Counter(tuple(sorted((int(a), int(b))))
                                for tri in faces for a, b in zip(tri, np.roll(tri, -1)))
    if any(count > 2 or (count != 2 and not allow_open) for count in edges.values()):
        raise ValueError("Expected closed manifold asteroid")
    # Also require opposite directed uses, not merely incidence two.
    directed = collections.Counter((int(a), int(b)) for tri in faces
                                   for a, b in zip(tri, np.roll(tri, -1)))
    if any(edges[tuple(sorted((a, b)))] == 2 and directed[(a, b)] != directed[(b, a)] for a, b in directed):
        raise ValueError("Inconsistent winding")
    euler = len(set(faces.flat)) - len(edges) + len(faces)
    return euler


def normals(points, faces):
    tris = points[faces]
    face = np.cross(tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0])
    if np.min(np.linalg.norm(face, axis=1)) < 1e-10:
        raise ValueError("Degenerate triangle")
    result = np.zeros_like(points)
    for corner in range(3):
        np.add.at(result, faces[:, corner], face)
    length = np.linalg.norm(result, axis=1)
    if np.min(length) <= 1e-12:
        raise ValueError("Unused or cancelling geometric vertex")
    return result / length[:, None]


def barycentric_triangles(levels):
    triangles = [np.eye(3)]
    for _ in range(levels):
        refined = []
        for a, b, c in triangles:
            ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
            refined.extend(((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)))
        triangles = refined
    return np.asarray(triangles)


def pn_points(p, n, bary, fixed_edges=()):
    # Cubic position patch; shared edge controls depend only on the endpoints.
    edge = {}
    for i, j in ((0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1)):
        edge[i, j] = (2*p[i]+p[j]-np.dot(p[j]-p[i], n[i])*n[i])/3
        if tuple(sorted((i, j))) in fixed_edges:
            edge[i, j] = (2*p[i]+p[j])/3
    mean = np.mean(list(edge.values()), axis=0)
    center = mean + (mean-p.mean(axis=0))/2
    u, v, w = bary.T
    result = u[:, None]**3*p[0] + v[:, None]**3*p[1] + w[:, None]**3*p[2]
    for i, j in edge:
        result += (3*bary[:, i]**2*bary[:, j])[:, None]*edge[i, j]
    return result + (6*u*v*w)[:, None]*center


def noise(p, seed):
    cell = np.floor(p).astype(np.int64)
    f = p-cell
    f = f*f*(3-2*f)
    out = np.zeros(len(p))
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                key = (cell[:, 0]+x)*73856093 ^ (cell[:, 1]+y)*19349663 ^ (cell[:, 2]+z)*83492791 ^ seed
                key = key.astype(np.uint64) & np.uint64(0xffffffff)
                key = ((key ^ (key >> 13))*np.uint64(1274126177)) & np.uint64(0xffffffff)
                val = ((key ^ (key >> 16)) & np.uint64(0xffffff)).astype(float)/8388607.5-1
                weight = (f[:, 0] if x else 1-f[:, 0]) * (f[:, 1] if y else 1-f[:, 1]) * (f[:, 2] if z else 1-f[:, 2])
                out += weight*val
    return out


def refine(vertices, faces, levels, seed, smooth, relief, deviation, allow_open=False, preserve_shading=False):
    low, high = vertices[:, :3].min(axis=0), vertices[:, :3].max(axis=0)
    center = (low+high)/2
    radius = np.linalg.norm(vertices[:, :3]-center, axis=1).max()
    # Weld only geometry; UVs are kept per triangle corner.
    weld, points, ids = {}, [], []
    for point in vertices[:, :3]:
        key = tuple(np.round((point-center)/radius, 7))
        if key not in weld:
            weld[key] = len(points)
            points.append(point)
        ids.append(weld[key])
    points = np.array(points)
    # Some retail small mineable rocks contain exact same-winding duplicate faces.
    # Remove only attribute-identical duplicates, never opposite-facing sheets/UV overlays.
    unique_faces, seen = [], set()
    for face in faces:
        rotations = [np.roll(face, -i) for i in range(3)]
        keys = [vertices[r].astype("<f4").tobytes() for r in rotations]
        key = min(keys)
        if key not in seen:
            unique_faces.append(face); seen.add(key)
    removed_duplicates = len(faces)-len(unique_faces)
    faces = np.asarray(unique_faces)
    base_faces = np.array(ids)[faces]
    source_euler = topology(points, base_faces, allow_open)
    base_edges = collections.Counter(tuple(sorted((int(a), int(b))))
                                    for tri in base_faces for a, b in zip(tri, np.roll(tri, -1)))
    boundary = [edge for edge, count in base_edges.items() if count == 1]
    ns = normals(points, base_faces)
    source_normals = ns.copy()
    bary = barycentric_triangles(levels).reshape(-1, 3)
    geo, base, attributes, geo_ids, originals = [], [], [], [], []
    shading, reference_shading = [], []
    welded = {}
    for original_face, (face, original) in enumerate(zip(base_faces, faces)):
        ref = bary @ points[face]
        fixed = [tuple(sorted((i, j))) for i, j in ((0, 1), (1, 2), (2, 0))
                 if base_edges[tuple(sorted((int(face[i]), int(face[j]))))] == 1]
        patch = pn_points(points[face], ns[face], bary, fixed)
        positions = ref + smooth*(patch-ref)
        uv = bary @ vertices[original, 6:]
        shading.extend(bary @ vertices[original, 3:6])
        reference_shading.extend(bary @ ns[face])
        for a, b, tex in zip(ref, positions, uv):
            key = tuple(np.round((a-center)/radius, 7))
            if key not in welded:
                welded[key] = len(geo)
                geo.append(b); base.append(a)
            geo_ids.append(welded[key])
            attributes.append(tex)
        originals.extend([original_face]*(len(bary)//3))
    geo, base = np.array(geo), np.array(base)
    fine_faces = np.array(geo_ids).reshape(-1, 3)
    ns = normals(geo, fine_faces)
    q = (geo-center)/radius
    # Broad rock relief plus narrow, spatially continuous fracture depressions.
    height = relief*(0.55*noise(q*3.4, seed)+0.30*noise(q*9.1, seed+37)+0.15*noise(q*17.3, seed+71))
    cracks = np.exp(-np.abs(noise(q*4.7, seed+101))*32)
    height -= relief*0.5*cracks
    # Broad shallow impacts/scallops. Their locations are independent of subdivision level.
    rng = np.random.default_rng(seed)
    for _ in range(8):
        face = base_faces[rng.integers(len(base_faces))]
        weights = rng.uniform(0.15, 1, 3); weights /= weights.sum()
        hit = weights @ points[face]
        hit += smooth*(pn_points(points[face], source_normals[face], weights[None])[0]-hit)
        distance = np.linalg.norm(geo-hit, axis=1)/(radius*rng.uniform(0.16, 0.28))
        bowl = np.maximum(0, 1-distance*distance)**2
        rim = np.exp(-((distance-0.9)/0.16)**2)
        height += relief*rng.uniform(0.35, 0.65)*(-bowl+0.12*rim)
    nearest = np.sqrt(((base[:, None]-points[None, :])**2).sum(axis=2)).min(axis=1)/radius
    anchor = np.clip(nearest/0.18, 0, 1)
    anchor = anchor*anchor*(3-2*anchor)
    for a, b in boundary:
        edge = points[b]-points[a]
        t = np.clip((base-points[a]) @ edge / np.dot(edge, edge), 0, 1)
        distance = np.linalg.norm(base-(points[a]+t[:, None]*edge), axis=1)/radius
        anchor *= np.clip(distance/0.06, 0, 1)
    geo += ns*(radius*height*anchor)[:, None]
    delta = geo-base
    lengths = np.linalg.norm(delta, axis=1)
    geo = base + delta*np.minimum(1, deviation*radius/np.maximum(lengths, 1e-20))[:, None]
    # Retain the authored box and all original corner positions.
    geo = np.minimum(high, np.maximum(low, geo))
    if topology(geo, fine_faces, allow_open) != source_euler:
        raise ValueError("Refinement changed source topology")
    new_tri = geo[fine_faces]
    cross = np.cross(new_tri[:, 1]-new_tri[:, 0], new_tri[:, 2]-new_tri[:, 0])
    old_tri = points[base_faces]
    old_cross = np.cross(old_tri[:, 1]-old_tri[:, 0], old_tri[:, 2]-old_tri[:, 0])
    alignment = (cross*old_cross[np.array(originals)]).sum(axis=1)
    if np.any(alignment <= 0):
        raise ValueError("Refinement folded a triangle; reduce relief/smoothing")
    ns = normals(geo, fine_faces)
    shade = ns[np.array(geo_ids)]
    if preserve_shading:
        authored, reference = np.array(shading), np.array(reference_shading)
        authored /= np.maximum(np.linalg.norm(authored, axis=1, keepdims=True), 1e-12)
        reference /= np.maximum(np.linalg.norm(reference, axis=1, keepdims=True), 1e-12)
        shade = authored + shade - reference
        shade /= np.maximum(np.linalg.norm(shade, axis=1, keepdims=True), 1e-12)
    corners = np.concatenate((geo[np.array(geo_ids)], shade, np.array(attributes)), axis=1)
    volume = lambda p, f: abs(np.einsum("ij,ij->i", p[f[:, 0]], np.cross(p[f[:, 1]], p[f[:, 2]])).sum()/6)
    metrics = {
        "triangles": len(fine_faces), "geometric_vertices": len(geo),
        "radius": float(radius), "max_deviation": float(np.linalg.norm(geo-base, axis=1).max()),
        "max_deviation_radius_percent": float(np.linalg.norm(geo-base, axis=1).max()/radius*100),
        "volume_ratio": float(volume(geo, fine_faces)/volume(points, base_faces)),
        "bbox_before": [low.tolist(), high.tolist()],
        "bbox_after": [geo.min(axis=0).tolist(), geo.max(axis=0).tolist()],
        "closed_manifold": not boundary, "euler": source_euler, "flipped_triangles": 0,
        "original_boundary_edges": len(boundary), "removed_identical_faces": removed_duplicates,
    }
    return corners, metrics


def pack_mesh(header, descriptor, original_vertices, corners):
    # Preserve original indices for the sparse HUD wireframe (not drawn by face indices).
    encoded = encode_vertices(original_vertices, header[4])
    stride = len(encoded)//len(original_vertices)
    vertex_bytes = [encoded[i:i+stride] for i in range(0, len(encoded), stride)]
    by_value = {v: i for i, v in enumerate(vertex_bytes)}
    indices = []
    encoded_corners = encode_vertices(corners, header[4])
    for i in range(0, len(encoded_corners), stride):
        raw = encoded_corners[i:i+stride]
        if raw not in by_value:
            by_value[raw] = len(vertex_bytes); vertex_bytes.append(raw)
        indices.append(by_value[raw])
    if len(vertex_bytes) >= 65536 or len(indices) >= 65536:
        raise ValueError("16-bit VMesh limits exceeded")
    blob = struct.pack("<II4H", 1, 4, 1, len(indices), header[4], len(vertex_bytes))
    blob += struct.pack("<I4H", descriptor[0], 0, len(vertex_bytes)-1, len(indices), descriptor[1])
    blob += np.asarray(indices, "<u2").tobytes() + b"".join(vertex_bytes)
    _, _, check_v, check_f = decode(blob)
    if encode_vertices(check_v[check_f.flat], header[4]) != encoded_corners:
        raise ValueError("Mesh serialization changed rendered attributes")
    return blob


def write_model(source_data, blob, name, destination):
    header, roots = read_tree(source_data)
    root = roots[0]
    library = child(root, "VMeshLibrary")
    if len(library.children) != 1:
        raise ValueError("Expected a single rigid mesh")
    mesh = library.children[0]
    mesh.name = name
    child(mesh, "VMeshData").blob = blob
    ref_node = child(child(root, "VMeshPart"), "VMeshRef")
    original_ref = ref_node.blob
    old_mesh = next(b for p, _, b in leaves(source_data)[1] if p.lower().endswith("/vmeshdata"))
    old_h, _, _, _ = decode(old_mesh)
    if struct.unpack_from("<6H", original_ref, 8) != (0, old_h[-1], 0, old_h[3], 0, 1):
        raise ValueError("Partial mesh references unsupported")
    h, _, verts, _ = decode(blob)
    _, _, old_verts, _ = decode(old_mesh)
    if not np.array_equal(verts[:len(old_verts)], old_verts):
        raise ValueError("Original wireframe vertices changed")
    ref = bytearray(original_ref)
    struct.pack_into("<I6H", ref, 4, crc(name), 0, h[-1], 0, h[3], 0, 1)
    low, high = verts[:, :3].min(axis=0), verts[:, :3].max(axis=0)
    center = (low+high)/2
    radius = np.linalg.norm(verts[:, :3]-center, axis=1).max()
    struct.pack_into("<10f", ref, 20, high[0], low[0], high[1], low[1], high[2], low[2], *center, radius)
    ref_node.blob = bytes(ref)
    wire = child(child(root, "VMeshWire"), "VWireData")
    w = bytearray(wire.blob)
    struct.pack_into("<I", w, 4, crc(name))
    wire.blob = bytes(w)
    output = write_tree(header, roots)
    before = {p: b for p, _, b in leaves(source_data)[1]}
    after = {p: b for p, _, b in leaves(output)[1]}
    output_blob = next(b for p, b in after.items() if p.lower().endswith("/vmeshdata"))
    if output_blob != blob:
        raise ValueError("UTF round-trip changed mesh data")
    stored_ref = next(b for p, b in after.items() if p.lower().endswith("/vmeshref"))
    if struct.unpack_from("<I6H", stored_ref, 4) != (crc(name), 0, h[-1], 0, h[3], 0, 1):
        raise ValueError("UTF round-trip changed full-mesh reference")
    for path, data in before.items():
        if path.lower().endswith(("/vmeshref", "/vmeshdata", "/vwiredata")):
            continue
        if after[path] != data:
            raise ValueError("Unrelated UTF leaf changed")
    before_wire = next(b for p, b in before.items() if p.lower().endswith("/vwiredata"))
    if wire.blob[:4] != before_wire[:4] or wire.blob[8:] != before_wire[8:]:
        raise ValueError("Original wireframe indices changed")
    destination.write_bytes(output)
    return hashlib.sha256(output).hexdigest()


def export_obj(path, corners):
    # Expanded OBJ is for DCC inspection, not the compact game representation.
    with path.open("w", encoding="ascii") as out:
        out.write("# Procedural asteroid; OBJ exposes primary UV only. Game mesh preserves both.\n")
        for v in corners:
            out.write("v %.9g %.9g %.9g\n" % tuple(v[:3]))
        for v in corners:
            out.write("vt %.9g %.9g\n" % tuple(v[6:8]))
        for v in corners:
            out.write("vn %.9g %.9g %.9g\n" % tuple(v[3:6]))
        for i in range(0, len(corners), 3):
            out.write("f " + " ".join(f"{j}/{j}/{j}" for j in (i+1, i+2, i+3)) + "\n")


def render(corners, center, radius, angle, size=480, wire=False):
    # Orthographic software preview: geometry + vertex normals, no texture/normal map.
    p = corners[:, :3]-center
    yaw, pitch = angle, -0.28
    ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    rx = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
    rotation = rx @ ry
    pos, normal = p @ rotation.T, corners[:, 3:6] @ rotation.T
    image = np.full((size, size, 3), (24, 29, 37), dtype=np.uint8)
    depth = np.full((size, size), -np.inf)
    screen = pos[:, :2]*size*0.40/radius
    screen[:, 0] += size/2
    screen[:, 1] = size/2-screen[:, 1]
    light = np.array([-0.55, 0.7, 1.0]); light /= np.linalg.norm(light)
    for start in range(0, len(corners), 3):
        xy, z, ns = screen[start:start+3], pos[start:start+3, 2], normal[start:start+3]
        low = np.maximum(0, np.floor(xy.min(axis=0)).astype(int))
        high = np.minimum(size-1, np.ceil(xy.max(axis=0)).astype(int))
        if np.any(high < low): continue
        x, y = np.meshgrid(np.arange(low[0], high[0]+1)+0.5, np.arange(low[1], high[1]+1)+0.5)
        a, b, c = xy
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-8: continue
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        w = 1-u-v
        zs = u*z[0]+v*z[1]+w*z[2]
        region = np.s_[low[1]:high[1]+1, low[0]:high[0]+1]
        mask = (u >= 0) & (v >= 0) & (w >= 0) & (zs > depth[region])
        n = u[..., None]*ns[0]+v[..., None]*ns[1]+w[..., None]*ns[2]
        n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-10)
        shade = 0.20+0.80*np.maximum(0, n @ light)
        rgb = np.clip(shade[..., None]*np.array([196, 185, 163]), 0, 255).astype(np.uint8)
        if wire:
            # Screen-space constant-width edges, including only frontmost triangles.
            area = abs(den)
            distances = np.stack([u*area/np.linalg.norm(b-c), v*area/np.linalg.norm(c-a), w*area/np.linalg.norm(a-b)])
            rgb[distances.min(axis=0) < 0.55] = [47, 84, 101]
        image[region][mask] = rgb[mask]
        depth[region][mask] = zs[mask]
    return Image.fromarray(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=REPO/"src/obj/procedural_asteroids/rock60")
    parser.add_argument("--subdivisions", type=int, choices=(2, 3, 4), default=3)
    parser.add_argument("--seed", type=int, default=6028)
    parser.add_argument("--smooth", type=float, default=0.35)
    parser.add_argument("--relief", type=float, default=0.045)
    parser.add_argument("--max-deviation", type=float, default=0.06)
    args = parser.parse_args()
    stage = args.output.resolve()
    stage_root = (REPO/"src/obj/procedural_asteroids").resolve()
    if not stage.is_relative_to(stage_root) or args.source.resolve().is_relative_to(stage):
        raise ValueError("Output must be under src/obj/procedural_asteroids and separate from source")
    for value, low, high in ((args.smooth, 0, 1), (args.relief, 0, 0.08), (args.max_deviation, 0.001, 0.10)):
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError("Parameters outside conservative prototype limits")
    source = args.source.read_bytes()
    nodes = leaves(source)[1]
    blobs = [b for p, _, b in nodes if p.lower().endswith("/vmeshdata")]
    if len(blobs) != 1:
        raise ValueError("Expected single asteroid mesh")
    header, descriptor, vertices, faces = decode(blobs[0])
    original = vertices[faces.flat]
    stage.mkdir(parents=True, exist_ok=True)
    report = {"source": str(args.source.resolve()), "source_sha256": hashlib.sha256(source).hexdigest(),
              "original_triangles": len(faces), "uv_channels": (header[4] >> 8) & 15,
              "parameters": {k: v for k, v in vars(args).items() if k not in ("source", "output")},
              "collision": "Original SUR is not modified; gameplay clearance needs validation.",
              "deployment": "Separate alternatives, not automatically installed or selected as LODs.",
              "levels": []}
    variants = [("Original", original)]
    export_obj(stage/"original.obj", original)
    for label, level in (("Medium", args.subdivisions-1), ("High", args.subdivisions)):
        corners, metrics = refine(vertices, faces, level, args.seed, args.smooth, args.relief, args.max_deviation)
        blob = pack_mesh(header, descriptor, vertices, corners)
        model = stage/(args.source.stem+"_"+label.lower()+".3db")
        private_name = f"procedural_{args.source.stem}_{hashlib.sha256(blob).hexdigest()[:12]}_{label.lower()}-{header[4]:x}.vms"
        metrics["sha256"] = write_model(source, blob, private_name, model)
        metrics["model"] = model.name
        metrics["render_vertices"] = decode(blob)[0][-1]
        metrics["homogeneous_16bit_block_instance_ceiling"] = 65535 // metrics["render_vertices"]
        export_obj(model.with_suffix(".obj"), corners)
        # Verify determinism of the actual algorithm, not just serialization.
        repeat, _ = refine(vertices, faces, level, args.seed, args.smooth, args.relief, args.max_deviation)
        if not np.array_equal(corners, repeat):
            raise ValueError("Non-deterministic geometry")
        report["levels"].append(metrics)
        variants.append((label, corners))
    if args.source.read_bytes() != source:
        raise ValueError("Source changed during generation")
    center = (vertices[:, :3].min(axis=0)+vertices[:, :3].max(axis=0))/2
    radius = np.linalg.norm(vertices[:, :3]-center, axis=1).max()
    size = 480
    sheet = Image.new("RGB", (size*3, size*3+120), (24, 29, 37))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    font = ImageFont.truetype(str(font_path), 22)
    small = ImageFont.truetype(str(font_path), 17)
    for col, (label, corners) in enumerate(variants):
        draw.text((col*size+22, 16), f"{label} | {len(corners)//3:,} triangles", font=font, fill=(231, 235, 240))
        for row, (angle, wire) in enumerate(((0.5, False), (2.2, False), (0.5, True))):
            sheet.paste(render(corners, center, radius, angle, size, wire), (col*size, 55+row*size))
    draw = ImageDraw.Draw(sheet)
    draw.text((22, size*3+66), "Identical camera / lighting / scale. Geometry only: no textures, normal maps or ambient occlusion.", font=small, fill=(196, 203, 214))
    draw.text((22, size*3+91), "Offline preview; original collision mesh retained. Game installation unchanged.", font=small, fill=(151, 164, 181))
    sheet.save(stage/"comparison.png")
    (stage/"report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
