"""Author all five wounds from the accepted intact meshes, with thick torn edges."""
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0, str(HERE))
from rh_concept_b_final_blender import mesh_object, groups_from_mesh, C
OUT = HERE.parents[1]/'out/ship_design/rh_elite/rh_pir_elite/tail_rim/damage_04'
DATA = json.loads((OUT/'input.json').read_text())
DM, EQ = DATA['damage_material'], DATA['equipment_material']
PALE = 4138378680


def dump(name, value):
    (OUT/name).write_text(json.dumps(value, default=lambda x:x.tolist() if isinstance(x, np.ndarray) else float(x), indent=2)+'\n', encoding='utf8')


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.file_preview_type = 'NONE'; bpy.context.preferences.filepaths.save_version = 0
    for key in DATA['materials']:
        mat = bpy.data.materials.new(key); mat.diffuse_color = (*DATA['materials'][key]['colour'], 1)


def topology(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=2e-5)
    # Native atlas patches split the red cheek floor midway along its wall.
    # Conform those UV-only T junctions before booleaning the closed skin.
    for _ in range(300):
        boundary = [e for e in bm.edges if e.is_boundary]
        candidates = {v for e in boundary for v in e.verts}; match = None
        for e in boundary:
            a, c = e.verts; d = c.co-a.co
            if d.length_squared < 1e-12:continue
            for v in candidates:
                if v in e.verts or any(v in p.verts for p in e.link_faces):continue
                t = (v.co-a.co).dot(d)/d.length_squared
                if 1e-5 < t < 1-1e-5 and (a.co+d*t-v.co).length < 3e-5:
                    match = e,a,v,t;break
            if match:break
        if match is None:break
        e,a,v,t = match; _,new = bmesh.utils.edge_split(e,a,t);new.co=v.co.copy()
        bmesh.ops.weld_verts(bm,targetmap={new:v})
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.dissolve_degenerate(bm,dist=1e-5,edges=list(bm.edges))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    result = dict(vertices=len(bm.verts), faces=len(bm.faces), boundary_edges=sum(e.is_boundary for e in bm.edges),
                  nonmanifold_edges=sum(not e.is_manifold for e in bm.edges), volume=abs(bm.calc_volume(signed=True)))
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    assert result['nonmanifold_edges'] == 0 and result['volume'] > 1e-7, (ob.name, result)
    return result


def object_points(name, points, faces, mid):
    me = bpy.data.meshes.new(name); me.from_pydata([C@Vector(p) for p in points], [], faces); me.update()
    me.materials.append(bpy.data.materials[str(mid)]); me.uv_layers.new(name='NativeUV')
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); topology(ob)
    return ob


def prism(name, poly, axes, lo, hi, mid=DM):
    other = next(i for i in range(3) if i not in axes); verts = []
    for value in (lo, hi):
        for pair in poly:
            p = np.zeros(3); p[list(axes)] = pair; p[other] = value; verts.append(p)
    n = len(poly); faces = [tuple(range(n-1, -1, -1)), tuple(range(n, n*2))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return object_points(name, verts, faces, mid)


def tube(name, cx, cy, z0, z1, r0, r1, mid=EQ, count=10):
    angles = np.arange(count)*2*math.pi/count
    points = [(cx+rad*math.cos(a), cy+rad*math.sin(a), z) for z, rad in ((z0, r0), (z1, r1)) for a in angles]
    faces = [tuple(range(count-1, -1, -1)), tuple(range(count, count*2))]
    faces += [(i, (i+1)%count, (i+1)%count+count, i+count) for i in range(count)]
    return object_points(name, points, faces, mid)


def cut(ob, cutter, operation='DIFFERENCE'):
    mids = list(dict.fromkeys([m.name for m in ob.data.materials]+[m.name for m in cutter.data.materials]))
    for target in (ob, cutter):
        old = [m.name for m in target.data.materials]; ids = [mids.index(old[p.material_index]) for p in target.data.polygons]
        target.data.materials.clear()
        for mid in mids:target.data.materials.append(bpy.data.materials[mid])
        for p, index in zip(target.data.polygons, ids):p.material_index = index
    bpy.context.view_layer.objects.active = ob
    mod = ob.modifiers.new('Authored rupture', 'BOOLEAN'); mod.operation = operation; mod.solver = 'MANIFOLD'; mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name); bpy.data.objects.remove(cutter, do_unlink=True)
    assert len(ob.data.polygons), ob.name
    topology(ob)


def groups(ob):return groups_from_mesh(ob.data, [int(m.name) for m in ob.data.materials])


def tree(ob):return BVHTree.FromPolygons([v.co for v in ob.data.vertices], [tuple(p.vertices) for p in ob.data.polygons])


def remap(ob, burn=None, whole_wing=False, wing_root=0, wing_end=1):
    uv = ob.data.uv_layers.active
    points=np.array([C.transposed()@v.co for v in ob.data.vertices]);lo=points.min(0);span=np.maximum(np.ptp(points,axis=0),.01)
    center=(points.min(0)+points.max(0))/2
    for mid in (DM, EQ):
        if str(mid) not in [m.name for m in ob.data.materials]:ob.data.materials.append(bpy.data.materials[str(mid)])
    slots = [int(m.name) for m in ob.data.materials]
    for p in ob.data.polygons:
        coords = [np.array(C.transposed()@ob.data.vertices[ob.data.loops[li].vertex_index].co) for li in p.loop_indices]
        center = np.mean(coords, axis=0); mid = slots[p.material_index]
        if whole_wing or (burn is not None and burn(center)):
            mid = DM; p.material_index = slots.index(DM)
        if mid not in (DM, EQ):continue
        normal = np.array(C.transposed()@p.normal); axes = np.argsort(abs(normal))[:2]
        angles=np.unwrap([math.atan2(c[1]-center[1],c[0]-center[0]) for c in coords])
        angles-=math.floor(float(np.mean(angles))/(2*math.pi))*2*math.pi
        for li, co in zip(p.loop_indices, coords):
            if whole_wing:
                u = co[2]/1.9
                v = .48+.45*np.clip((abs(co[0])-wing_root)/(wing_end-wing_root), 0, 1)
                if abs(normal[1]) < .5:v = .78+(co[1]+1.82)*.30
            elif mid == DM:
                u = co[axes[0]]*.65; v = .47+.43*(co[axes[1]]-lo[axes[1]])/span[axes[1]]
            else:
                # Shared machinery atlas TOP LEFT quarter, not its pale hull quadrants.
                if abs(normal[2]) < .85:
                    u=.025+.44*(co[2]-lo[2])/span[2]
                    v=.025+.43*angles[list(p.loop_indices).index(li)]/(2*math.pi)
                else:
                    u=.025+.44*(co[0]-lo[0])/span[0];v=.025+.44*(co[1]-lo[1])/span[1]
            uv.data[li].uv = (u, 1-v)


def ribbon(name, host, rows, width_axis, thickness=.055):
    rows = np.array(rows, float); axis = np.array(width_axis, float)
    surface = tree(host); root = C@Vector(rows[0, :3]); loc, normal, _, dist = surface.find_nearest(root)
    assert loc is not None and dist < .6, (name, 'unattached proposed root', dist)
    rows[0, :3] = np.array(C.transposed()@(loc-normal*.025))
    centers, widths = rows[:, :3], rows[:, 3]; verts = []; uvs = []
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(centers, axis=0), axis=1))]; lengths /= lengths[-1]
    for j, (center, width) in enumerate(zip(centers, widths)):
        tangent = centers[min(j+1, len(rows)-1)]-centers[max(j-1, 0)]
        w = axis-axis.dot(tangent)*tangent/tangent.dot(tangent); w /= np.linalg.norm(w)
        n = np.cross(w, tangent); n /= np.linalg.norm(n); angle = math.radians(rows[j, 4])
        w, n = w*math.cos(angle)+n*math.sin(angle), n*math.cos(angle)-w*math.sin(angle)
        for depth in (-1, 1):
            for edge in (-1, 1):
                verts.append(center+w*width*.5*edge+n*thickness*.5*depth)
                uvs.append((.08+(edge+1)*.32, .35+lengths[j]*.58))
    faces = []
    for j in range(len(rows)-1):
        a = j*4; c = a+4
        faces += [(a, a+1, c+1, c), (a+2, c+2, c+3, a+3), (a, c, c+2, a+2), (a+1, a+3, c+3, c+1)]
    faces += [(0, 2, 3, 1), (len(verts)-4, len(verts)-3, len(verts)-1, len(verts)-2)]
    ob = object_points(name, verts, faces, DM)
    for p in ob.data.polygons:
        for li in p.loop_indices:
            vi=ob.data.loops[li].vertex_index;u,v=uvs[vi]
            depth=(vi%4)//2;edge=vi%2
            if p.index >= (len(rows)-1)*4:
                u,v=.10+edge*.60,.70+depth*.25
            elif p.index%4 in (2,3):
                u,v=.12+depth*.10,.35+lengths[vi//4]*.58
            ob.data.uv_layers.active.data[li].uv = (u, 1-v)
    pairs = len(surface.overlap(tree(ob))); assert pairs > 0, (name, 'ribbon root floating')
    stats = topology(ob); stats.update(root_adjustment=dist, attached_triangle_pairs=pairs)
    return ob, stats


def projected_area(gs):
    total = 0
    for g in gs:
        a = np.array(g['corners'])[:, :, :3]
        n = np.cross(a[:, 1]-a[:, 0], a[:, 2]-a[:, 0])
        total += np.maximum(n[:, 1], 0).sum()/2
    return float(total)


def author():
    clear(); out = {}; stats = {}
    for side, label in ((-1, 'port'), (1, 'starboard')):
        source = DATA['wings'][label]
        ob, _ = mesh_object(dict(groups=source), label+' ripped wing'); topology(ob)
        full_area = projected_area(groups(ob))
        # Find the retained inner span giving 30-32% projected wing area, then
        # use a nonuniform tear profile instead of an axis-aligned cut.
        points = np.concatenate([np.array(g['corners'])[:, :, :3].reshape(-1, 3) for g in source])
        from mathutils.geometry import tessellate_polygon
        lo, hi = min(abs(points[:, 0])), max(abs(points[:, 0]))
        def clipped_area(bound):
            area = 0
            for g in source:
                for tri in g['corners']:
                    p = np.array(tri)[:, :3]; n = np.cross(p[1]-p[0], p[2]-p[0])
                    if n[1] <= 1e-8:continue
                    poly = p[:, [0, 2]].copy(); poly[:, 0] *= side; clipped = []
                    for a, c in zip(poly, np.roll(poly, -1, axis=0)):
                        ia, ic = a[0] <= bound, c[0] <= bound
                        if ia:clipped.append(a)
                        if ia != ic:clipped.append(a+(c-a)*(bound-a[0])/(c[0]-a[0]))
                    if len(clipped)>2:
                        q = np.array(clipped); area += abs(np.sum(q[:, 0]*np.roll(q[:, 1], -1)-q[:, 1]*np.roll(q[:, 0], -1)))/2
            return area
        a, c = lo, hi
        for _ in range(30):
            mid = (a+c)/2
            if clipped_area(mid)/full_area < (.31 if side<0 else .33):a = mid
            else:c = mid
        baseline = (a+c)/2
        zs = np.array([-.5, 1.5, 2.1, 2.5, 2.9, 3.3, 3.7, 4.1, 4.5, 5.2, 6.5])
        offsets = np.array([0, .12, -.10, .24, -.22, .15, -.12, .27, -.18, .07, 0])
        if side>0:offsets = -offsets*.8
        cuts = baseline+offsets
        poly = [[side*x, z] for x, z in zip(cuts, zs)]+[[side*12, zs[-1]], [side*12, zs[0]]]
        cut(ob, prism('jagged wing tear', poly, (0, 2), -6, 5))
        for v in ob.data.vertices:
            p = np.array(C.transposed()@v.co); edge = np.interp(p[2], zs, cuts)
            weight = max(0, 1-abs(abs(p[0])-edge)/.48)
            p[1] += weight*.18*math.sin(p[2]*7+side); p[0] += side*weight*.05*math.cos(p[2]*6)
            v.co = C@Vector(p)
        stat = topology(ob); remap(ob, whole_wing=True, wing_root=lo, wing_end=baseline+.2)
        body = groups(ob); area = projected_area(body); ratio = area/full_area
        assert .20 <= ratio < .45, (label, ratio)
        extras = []; ribbons = []
        for i, z in enumerate([2.85, 3.55, 4.30]):
            x = np.interp(z, zs, cuts); sign = 1 if i%2 else -1
            rows = [[side*(x-.12), -1.66, z, .35, 0], [side*(x+.18), -1.66+sign*.20, z+.08, .36, 15],
                    [side*(x+.62), -1.66+sign*.40, z-.10, .22, sign*48], [side*(x+.79), -1.66+sign*.33, z-.15, .06, sign*65]]
            rib, s = ribbon(label+' wing peeled skin '+str(i), ob, rows, (0, 0, 1), .045)
            extras += groups(rib); ribbons.append(s); bpy.data.objects.remove(rib, do_unlink=True)
        out[label+'_wing'] = body+extras; stats[label+'_wing'] = dict(core=stat, intact_plan_area=full_area,
            retained_plan_area=area, retained_fraction=ratio, tear_x=baseline, ribbons=ribbons)
        bpy.data.objects.remove(ob, do_unlink=True)

        # Bore and split the actual 120% engine longitudinally. The upper skin
        # remains attached to BOTH existing supports; the outboard/bottom opens.
        name = 'Rh_'+label+'_engine_lod1'; ob, _ = mesh_object(dict(groups=DATA['parts'][name]), label+' ripped engine'); topology(ob)
        p = np.array([C.transposed()@v.co for v in ob.data.vertices]); cx, cy, cz = (p.min(0)+p.max(0))/2
        cut(ob, tube('internal engine cavity', cx, cy, 3.14, 7.8, .72, .70))
        zs = np.array([3.44, 3.72, 4.1, 4.44, 4.8, 5.18, 5.55, 5.9, 6.25, 6.65, 7.7])
        ys = cy+np.array([.17, -.12, .15, -.18, .06, -.13, .20, -.10, .07, -.16, -.05])
        if side>0:ys += np.array([0, .10, -.08, .04, -.10, .15, -.12, .05, -.08, .09, 0])
        cutter = prism('longitudinal torn half', [[y,z] for y,z in zip(ys,zs)]+[[-6.5,zs[-1]],[-6.5,zs[0]]], (1,2), cx-2, cx+2)
        for v in cutter.data.vertices:
            p = np.array(C.transposed()@v.co); p[1] += side*.42*(p[0]-cx); v.co = C@Vector(p)
        cut(ob, cutter)
        for v in ob.data.vertices:
            p = np.array(C.transposed()@v.co); edge = np.interp(p[2], zs, ys)+side*.42*(p[0]-cx)
            weight = max(0, 1-abs(p[1]-edge)/.18)*max(0, min(1, (p[2]-3.3)/.3))
            p[0] += side*weight*.11*math.sin(p[2]*8); p[1] -= weight*.045; v.co = C@Vector(p)
        stat = topology(ob)
        remap(ob, lambda p:p[2]>3.25 and abs(p[1]-(np.interp(p[2],zs,ys)+side*.42*(p[0]-cx)))<.30)
        core = tube(label+' fractured inner core', cx, cy+.10, 2.94, 5.12, .31, .23, EQ, 8)
        for v in core.data.vertices:
            p = np.array(C.transposed()@v.co)
            if p[2]>5:p[2] += .14*math.sin(math.atan2(p[1]-cy-.1,p[0]-cx)*3)
            v.co = C@Vector(p)
        topology(core); remap(core); extras = groups(core); bpy.data.objects.remove(core, do_unlink=True)
        ribs = []
        for i,z in enumerate([3.95,5.12,6.15]):
            x = cx+side*.62; y = np.interp(z,zs,ys)+.26
            rows = [[x,y+.04,z,.31,0],[x+side*.22,y-.12,z+.12,.35,side*12],
                    [x+side*.52,y-.48,z+.38,.25,side*45],[x+side*.43,y-.67,z+.55,.08,side*70]]
            rib,s = ribbon(label+' engine rolled lip '+str(i),ob,rows,(0,0,1),.055)
            extras += groups(rib); ribs.append(s); bpy.data.objects.remove(rib,do_unlink=True)
        out[label+'_engine'] = groups(ob)+extras; stats[label+'_engine'] = dict(shell=stat, ribbons=ribs,
            method='120% intact pod bored and torn longitudinally; upper supported shell and inner core remain')
        bpy.data.objects.remove(ob,do_unlink=True)

    # A deep, ragged opening through the outer sleeve. The complete live rim
    # behind it belongs to Root and is intentionally untouched.
    tail = []; tail_stats = []; tail_objects=[];tail_ribbons=[];shell = DATA['tail_shell']
    profile_y = np.array([-.18,.25,.50,.92,1.25,1.62,1.95,2.32,2.65])
    profile_z = np.array([8.42,8.15,8.34,7.74,8.04,7.62,7.96,8.38,8.22])
    for side, source in [(-1,shell[:3]),(1,shell[3:6]),(0,shell[6:])]:
        ob,_ = mesh_object(dict(groups=source),'torn tail sleeve '+str(side)); topology(ob)
        poly = [[y,z] for y,z in zip(profile_y,profile_z)]+[[profile_y[-1],10.5],[profile_y[0],10.5]]
        cut(ob,prism('tail opening',poly,(1,2),-5,5))
        if side:
            for v in ob.data.vertices:
                p = np.array(C.transposed()@v.co); edge = np.interp(p[1],profile_y,profile_z)
                weight = max(0,1-abs(p[2]-edge)/.35)*max(0,min(1,(abs(p[0])-.65)/.4))
                p[0] += side*weight*.16*math.sin(p[1]*7+.5); p[2] += weight*.07; v.co=C@Vector(p)
        stat=topology(ob);remap(ob,lambda p:abs(p[2]-np.interp(p[1],profile_y,profile_z))<.5)
        ribs=[];extras=[]
        if side:
            for i,y in enumerate([.0,1.1,2.7]):
                z=np.interp(y,profile_y,profile_z)
                rows=[[side*1.03,y,z-.12,.38,0],[side*1.24,y+.13,z+.16,.44,side*18],
                      [side*1.65,y+(.40 if i%2 else -.32),z+.43,.28,side*50],
                      [side*1.74,y+(.55 if i%2 else -.46),z+.64,.08,side*72]]
                rib,s=ribbon('tail peeled cheek '+str(side)+' '+str(i),ob,rows,(0,1,0),.06)
                extras+=groups(rib);ribs.append(s);tail_ribbons.append(rib)
        tail+=groups(ob)+extras;tail_stats.append(dict(side=side,shell=stat,ribbons=ribs));tail_objects.insert(0,ob)
    # Unite the two cheeks and rear returns: their native seam shares exact
    # vertices, so exporting touching solids would leave four nonmanifold edges.
    joined=tail_objects[0]
    for other in tail_objects[1:]:cut(joined,other,'UNION')
    out['tail']=groups(joined)+[g for rib in tail_ribbons for g in groups(rib)]
    stats['tail']=dict(pieces=tail_stats,joined=topology(joined),method='Current sleeve ripped open, curled cheek edges and six attached strips; complete inner rim survives')
    dump('damage_world.json',out);dump('damage_geometry_check.json',stats)
    print('ALL FIVE DAMAGE ZONES READY',[(k,sum(len(g['corners']) for g in v)) for k,v in out.items()],flush=True)


if __name__ == '__main__':author()
