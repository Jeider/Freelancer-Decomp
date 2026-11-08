"""Export matching Beta HUD meshes and release-priority marker contours.

Requires NumPy/SciPy offline only. Does not modify game assets.
python tools/targeting_hud/export_beta_markers.py BETA_HUD --retail-atlas ButtonTextures.txm
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from generate_station_lods import read_tree, child
from trace_retail_marker import trace


def load(folder, name, plane='xz', region=None):
    raw = (folder / (name + '.3db')).read_bytes()
    root = read_tree(raw)[1][0]
    blob = child(child(root, 'VMeshLibrary').children[0], 'VMeshData').blob
    flags, primitive, groups, count, fvf, vertices = struct.unpack_from('<II4H', blob)
    assert primitive == 4
    stride = 12 + (12 if fvf & 16 else 0) + (4 if fvf & 64 else 0) + (4 if fvf & 128 else 0) + 8*((fvf >> 8) & 15)
    offset = 16 + 12*groups
    start = offset + 2*count
    positions = [struct.unpack_from('<3f', blob, start + stride*i) for i in range(vertices)]
    points = [(v[0], -v[1]) if plane == 'xy' else (v[0], v[2]) for v in positions]
    ids = []
    for group in range(groups):
        _, lo, _, n, _ = struct.unpack_from('<I4H', blob, 16+12*group)
        ids.extend(i + (lo if flags & 1 else 0) for i in struct.unpack_from(f'<{n}H', blob, offset))
        offset += n*2
    # Weld exporter duplicates and remove back faces/degenerate triangles. Keep
    # native triangle positions/topology; ignore only sub-micrometre depth offsets.
    unique, remap = [], {}
    for i, p in enumerate(points):
        match = next((k for k, q in enumerate(unique) if math.dist(p, q) < 1e-7), None)
        if match is None:
            match = len(unique)
            unique.append(p)
        remap[i] = match
    triangles, seen = [], set()
    for i in range(0, len(ids), 3):
        face = tuple(remap[j] for j in ids[i:i+3])
        p = [unique[j] for j in face]
        if region and not region(np.mean(p, axis=0)):
            continue
        area = (p[1][0]-p[0][0])*(p[2][1]-p[0][1])-(p[1][1]-p[0][1])*(p[2][0]-p[0][0])
        key = tuple(sorted(face))
        if abs(area) < 1e-12 or key in seen:
            continue
        seen.add(key)
        triangles.append(face if area > 0 else face[::-1])
    used = sorted({i for f in triangles for i in f})
    mesh = {'points': np.array([unique[i] for i in used]),
            'triangles': np.array([[used.index(i) for i in f] for f in triangles]),
            'source': name, 'sha256': hashlib.sha256(raw).hexdigest()}
    assert len(triangles) and len(used)
    return mesh


def rotate(mesh, angle):
    a = math.radians(angle)
    mesh['points'] = mesh['points'] @ np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]])


def fit(meshes, span=208):
    # One affine transform for an arrow and its hats/quotes preserves Beta alignment.
    points = np.concatenate([m['points'] for m in meshes])
    lo, hi = points.min(axis=0), points.max(axis=0)
    factor = span/max(hi-lo)
    for mesh in meshes:
        mesh['points'] = (mesh['points']-(lo+hi)/2)*factor+128


def boundary(mesh):
    edges = Counter(tuple(sorted((int(a), int(b)))) for f in mesh['triangles']
                    for a, b in zip(f, np.roll(f, -1)))
    # Beta's hat repeats its centre triangles with different diagonals. Classify
    # edges against the union, so those internal diagonals cannot acquire an AA fringe.
    result = []
    for i, j in edges:
        a, b = mesh['points'][i], mesh['points'][j]
        d = b-a
        n = np.array([-d[1],d[0]])/np.linalg.norm(d)*.001
        probes = np.array([(a+b)/2+n,(a+b)/2-n])
        if inside_mesh(probes,mesh)[0] != inside_mesh(probes,mesh)[1]:
            result.append((i,j))
    return result


def inside_mesh(points, mesh):
    inside = np.zeros(len(points), dtype=bool)
    for face in mesh['triangles']:
        a, b, c = mesh['points'][face]
        def cross(p, q): return p[..., 0]*q[..., 1]-p[..., 1]*q[..., 0]
        inside |= ((cross(b-a, points-a) >= -1e-7) & (cross(c-b, points-b) >= -1e-7) &
                   (cross(a-c, points-c) >= -1e-7))
    return inside


def remove_hat_overlaps(mesh):
    # The original repeats the filled bottom bar with different diagonals.
    # Retriangulate its single boundary using ONLY the original vertices.
    adjacent = {}
    for a,b in boundary(mesh):
        adjacent.setdefault(a,[]).append(b)
        adjacent.setdefault(b,[]).append(a)
    assert all(len(v)==2 for v in adjacent.values())
    order=[next(iter(adjacent))]
    previous=None
    while True:
        current=order[-1]
        following=next(i for i in adjacent[current] if i!=previous)
        if following==order[0]:break
        order.append(following);previous=current
    assert len(order)==len(adjacent)
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    p=mesh['points']
    if sum(cross(p[a],p[b]) for a,b in zip(order,order[1:]+order[:1]))<0:order.reverse()
    faces=[]
    while len(order)>2:
        for i,b in enumerate(order):
            a,c=order[i-1],order[(i+1)%len(order)]
            if cross(p[b]-p[a],p[c]-p[b])<=1e-7:continue
            if any(cross(p[b]-p[a],p[k]-p[a])>=-1e-7 and
                   cross(p[c]-p[b],p[k]-p[b])>=-1e-7 and
                   cross(p[a]-p[c],p[k]-p[c])>=-1e-7
                   for k in order if k not in (a,b,c)):continue
            faces.append((a,b,c));order.pop(i);break
        else:raise ValueError('Cannot triangulate Beta hat boundary')
    mesh['triangles']=np.array(faces)


def export_geometry(mesh):
    edges=boundary(mesh)
    # Orient each silhouette edge so the filled core lies to its left.
    oriented=[]
    for i,j in edges:
        a,b=mesh['points'][i],mesh['points'][j]
        delta=b-a;normal=np.array([-delta[1],delta[0]])/np.linalg.norm(delta)
        if not inside_mesh(np.array([(a+b)/2+normal*.001]),mesh)[0]:i,j=j,i
        oriented.append((i,j))
    normals={}
    for i,j in oriented:
        d=mesh['points'][j]-mesh['points'][i]
        n=np.array([d[1],-d[0]])/np.linalg.norm(d)
        normals.setdefault(i,[]).append(n);normals.setdefault(j,[]).append(n)
    vertices=[]
    for i,p in enumerate(mesh['points']):
        ns=normals.get(i,[])
        if len(ns)==2:
            divisor=max(.00001,1+float(ns[0]@ns[1]))
            n=(ns[0]+ns[1])/divisor
            if np.linalg.norm(n)>4:n=n*4/np.linalg.norm(n)
        elif ns:n=ns[0]
        else:n=np.zeros(2)
        vertices.append((float(p[0]),float(p[1]),float(n[0]),float(n[1])))
    return vertices,mesh['triangles'].tolist(),oriented


def outlined(mesh, width):
    """Stroke the native silhouette instead of reusing its solid background."""
    vertices, _, edges = export_geometry(mesh)
    vertices = np.array(vertices)
    outer = vertices[:,:2] + vertices[:,2:]*width/2
    inner = vertices[:,:2] - vertices[:,2:]*width/2
    points = np.concatenate((outer,inner))
    n = len(vertices)
    triangles = []
    for a,b in edges:
        for face in ((a,b,b+n),(a,b+n,a+n)):
            p,q,r=points[list(face)]
            area=(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
            if abs(area)>1e-8:triangles.append(face if area>0 else face[::-1])
    return {**mesh,'points':points,'triangles':np.array(triangles)}


def combine(a,b):
    return {**a,'points':np.concatenate((a['points'],b['points'])),
            'triangles':np.concatenate((a['triangles'],b['triangles']+len(a['points'])))}


def scaled(mesh, scale, center=None):
    if center is None: center=mesh['points'].mean(axis=0)
    return {**mesh,'points':(mesh['points']-center)*scale+center}


def align_target_group(meshes):
    # Retail's raster arrow is displaced sideways inside its tile. The health
    # and shield meshes rotate about the tile centre, so that displacement makes
    # the arrow sit off their common axis. Register the whole arrow group using
    # the bisector of its two long outside edges; retain every contour/detail.
    points = meshes['TargetDetail']['points']
    hull = points[ConvexHull(points).vertices]
    sides = sorted(zip(hull, np.roll(hull, -1, axis=0)),
                   key=lambda e: np.linalg.norm(e[1]-e[0]), reverse=True)[:2]
    lines = []
    for a, b in sides:
        if (b-a).sum() < 0: a, b = b, a
        lines.append((a, (b-a)/np.linalg.norm(b-a)))
    (a, u), (b, v) = lines
    apex = a + np.linalg.solve(np.column_stack((u, -v)), b-a)[0]*u
    axis = (u+v)/np.linalg.norm(u+v)
    angle = math.pi/4-math.atan2(axis[1], axis[0])
    rotation = np.array([[math.cos(angle), -math.sin(angle)],
                         [math.sin(angle), math.cos(angle)]])
    normal = np.array([1., -1.])/math.sqrt(2)
    offset = -float(((apex-128) @ rotation.T) @ normal)*normal
    for key in ('Target', 'TargetDetail', 'TargetHat', 'Quotes'):
        meshes[key]['points'] = (meshes[key]['points']-128) @ rotation.T+128+offset
        meshes[key]['alignment'] = {'angle': angle, 'offset': offset.tolist()}


def align_contact_hat(meshes, atlas):
    # NSTargetHat belongs to the retail contact triangle. Our contact/detail
    # use the smaller Beta triangle: sharing the tile centre alone displaces
    # the hat into the arrow. Register the three outside edges, retaining the
    # retail hat's contour, opening and spacing relative to its own arrow.
    def triangle(mesh):
        points = mesh['points']
        hull = points[ConvexHull(points).vertices]
        lines = sorted(zip(hull, np.roll(hull, -1, axis=0)),
                       key=lambda e: np.linalg.norm(e[1]-e[0]), reverse=True)[:3]
        corners = []
        for i, (a, b) in enumerate(lines):
            c, d = lines[(i+1) % 3]
            u, v = b-a, d-c
            corners.append(a + np.linalg.solve(np.column_stack((u, -v)), c-a)[0]*u)
        corners = np.array(corners)
        tip = int(np.argmin(corners.sum(axis=1)))
        rest = sorted((i for i in range(3) if i != tip), key=lambda i: corners[i, 1])
        return corners[[tip]+rest]
    source = triangle(trace(atlas, 8, 'NSTargetArrow'))
    target = triangle(meshes['ContactDetail'])
    transform = np.linalg.solve(np.column_stack((source, np.ones(3))), target)
    hat = meshes['ContactHat']
    hat['points'] = np.column_stack((hat['points'], np.ones(len(hat['points'])))) @ transform
    linear = transform[:2].T
    offset = linear @ np.array([128., 128.]) + transform[2] - 128
    hat['alignment'] = {'matrix': linear.tolist(), 'offset': offset.tolist()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    parser.add_argument('--retail-atlas',type=Path,required=True)
    args = parser.parse_args()
    folder = args.folder
    meshes = {}
    for key, name in [('Target','HUD_targetarrow'), ('TargetHat','HUD_targetarrowhat'),
                      ('Player','HUD_targetarrowplayer'), ('Quotes','HUD_targetarrowquotes'),
                      ('Contact','HUD_nonselectedarrow'), ('ContactHat','HUD_nonselectedarrowhat'),
                      ('SmallPlayer','HUD_nonselectedplayerarrow'), ('Loot','HUD_lootarrow')]:
        meshes[key] = load(folder, name)
        rotate(meshes[key], -45)
    fit([meshes[k] for k in ('Target','TargetHat','Player','Quotes')], 218)
    remove_hat_overlaps(meshes['TargetHat'])
    fit([meshes[k] for k in ('Contact','ContactHat','SmallPlayer')], 218)
    fit([meshes['Loot']], 174)
    meshes['Corner'] = load(folder, 'HUD_reticle', 'xy', lambda p:p[0]<0 and p[1]<0)
    fit([meshes['Corner']], 192)
    meshes['Hat'] = load(folder, 'HUD_reticle_arrows', 'xy', lambda p:p[0]<0)
    fit([meshes['Hat']], 184)
    meshes['Waypoint'] = load(folder, 'HUD_waypointhat', 'xy')
    fit([meshes['Waypoint']], 208)
    # The Beta waypoint texture itself is a raster quad. Use its native diamond
    # hat and derive only the retail's inner ring/background from that same mesh.
    # Beta's wide solid bands made both rings too thick. Trace the release's
    # narrow outer/inner contours instead, preserving their separate openings.
    meshes['WaypointDouble'] = trace(args.retail_atlas,11,'WaypointArrow')
    hull = ConvexHull(meshes['Waypoint']['points']).vertices
    meshes['WaypointBack'] = {**meshes['Waypoint'], 'points': meshes['Waypoint']['points'][hull],
                             'triangles': np.array([(0,i,i+1) for i in range(1,len(hull)-1)])}
    # Retail uses separate filled backgrounds and detailed foregrounds. Keep the
    # Beta silhouette, but never substitute the filled mesh for an outline tile.
    meshes['ContactDetail'] = combine(outlined(meshes['Contact'],7),
                                      outlined(scaled(meshes['Contact'],.53),4))
    # The selected arrow differs substantially from Beta: retain the release's
    # actual outer frame and inner inset, rather than constructing a generic triangle.
    meshes['Target'] = trace(args.retail_atlas,2,'CurrentTargetArrow')
    meshes['TargetDetail'] = trace(args.retail_atlas,5,'CurrentTargetArrowOutline')
    meshes['Corner'] = trace(args.retail_atlas,0,'CurrentTargetCorner')
    meshes['TargetHat'] = trace(args.retail_atlas,3,'CurrentTargetArrowHat')
    meshes['Quotes'] = trace(args.retail_atlas,4,'CurrentTargetArrowQuotes')
    meshes['ContactHat'] = trace(args.retail_atlas,7,'NSTargetHat')
    align_target_group(meshes)
    align_contact_hat(meshes, args.retail_atlas)
    meshes['LootDetail'] = outlined(meshes['Loot'],7)
    meshes['PlayerDetail'] = outlined(meshes['Player'],7)
    meshes['SmallPlayerDetail'] = outlined(meshes['SmallPlayer'],7)
    mapping = [('CurrentTargetCorner','Corner'), ('NSArrowBackground','Contact'),
               ('CurrentTargetArrow','Target'), ('CurrentTargetArrowHat','TargetHat'),
               ('CurrentTargetArrowQuotes','Quotes'), ('CurrentTargetArrowOutline','TargetDetail'),
               ('CurrentTargetHat','Hat'), ('NSTargetHat','ContactHat'),
               ('NSTargetArrow','ContactDetail'), ('WaypointTarget','Waypoint'),
               ('LootArrow','LootDetail'), ('WaypointArrow','WaypointDouble'),
               ('PlayerArrow','PlayerDetail'), ('LootArrowBackground','Loot'),
               ('PlayerArrowBackground','Player'), ('WaypointArrowBackground','WaypointBack')]
    header = '// Generated by tools/targeting_hud/export_beta_markers.py. Do not edit.\n'
    manifest = {}
    maximum = 0
    for key, mesh in meshes.items():
        vertices, triangles, edges = export_geometry(mesh)
        maximum = max(maximum, len(vertices))
        source_file=mesh.get('source_file',mesh['source']+'.3db')
        header += f'// {source_file} SHA256 {mesh["sha256"]}\n'
        header += f'inline constexpr MeshVertex {key}Vertices[] = {{\n'
        header += ''.join('    {'+', '.join(f'{v:.6f}f' for v in row)+'},\n' for row in vertices)
        header += f'}};\ninline constexpr unsigned short {key}Triangles[][3] = {{\n'
        header += ''.join('    {'+', '.join(str(i) for i in row)+'},\n' for row in triangles)
        header += f'}};\ninline constexpr unsigned short {key}Edges[][2] = {{\n'
        header += ''.join('    {'+', '.join(str(i) for i in row)+'},\n' for row in edges)
        header += f'}};\ninline constexpr Mesh {key}Mesh = {{{key}Vertices, {len(vertices)}, {key}Triangles, {len(triangles)}, {key}Edges, {len(edges)}}};\n'
        manifest[key] = {'source': mesh['source'], 'sha256': mesh['sha256'], 'vertices':len(vertices),
                         'triangles':len(triangles), 'native_vertices':mesh['points'].tolist(),
                         'native_triangles':mesh['triangles'].tolist()}
        if 'alignment' in mesh: manifest[key]['alignment'] = mesh['alignment']
    header += f'inline constexpr int MaxMeshVertices = {maximum};\n'
    header += 'inline constexpr Shape Shapes[] = {\n'
    for name,key in mapping:
        small = ', &SmallPlayerMesh' if key=='Player' else ', &SmallPlayerDetailMesh' if key=='PlayerDetail' else ''
        header += f'    {{"{name}", &{key}Mesh{small}}},\n'
    header += '};\n'
    (ROOT/'src/freelancer/Client/hud_marker_beta_data.h').write_text(header)
    out = ROOT/'src/obj/hud_geometry'; out.mkdir(parents=True, exist_ok=True)
    (out/'beta_marker_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Exported {len(meshes)} native/derived meshes, max {maximum} vertices; no game files changed.')


if __name__ == '__main__':
    main()
