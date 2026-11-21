"""Offline Blender: LOD generation, dense sweep intersections, final asset previews."""
import argparse
import hashlib
import json
import math
import copy
from pathlib import Path
import sys
import bpy
import bmesh
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
OUT=HERE.parents[1]/'out/ship_design/rh_elite/prototypes/concept_b/final_v1'
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))


def mesh_object(entry,name,position_decimals=5):
    verts=[];faces=[];uvs=[];normals=[];mats=[];slots=[];lookup={}
    for g in entry['groups']:
        if g['material'] not in slots:slots.append(g['material'])
        for tri in g['corners']:
            face=[]
            for v in tri:
                key=tuple(round(x,position_decimals) for x in v[:3])
                if key not in lookup:lookup[key]=len(verts);verts.append(C@Vector(v[:3]))
                face.append(lookup[key]);uvs.append((v[6],1-v[7]));normals.append(C@Vector(v[3:6]))
            faces.append(face);mats.append(slots.index(g['material']))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    for m in slots:me.materials.append(bpy.data.materials.get(str(m)) or bpy.data.materials.new(str(m)))
    uv=me.uv_layers.new(name='NativeUV')
    for p,mi in zip(me.polygons,mats):
        p.material_index=mi;p.use_smooth=False
        for i in p.loop_indices:uv.data[i].uv=uvs[i]
    # Blender 5.2's corner-normal setter crashes on welded nonmanifold islands.
    # These work meshes use geometric normals; accepted LOD0 remains unchanged.
    obj=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(obj)
    return obj,slots


def groups_from_mesh(me,slots,area_epsilon=1e-8):
    me.calc_loop_triangles();by={}
    uv=me.uv_layers.active
    for tri in me.loop_triangles:
        out=[]
        for i in tri.loops:
            p=C.transposed()@me.vertices[me.loops[i].vertex_index].co
            n=C.transposed()@me.corner_normals[i].vector
            t=uv.data[i].uv
            out.append([*p,*n,t.x,1-t.y])
        a,bb,c=[Vector(t[:3]) for t in out]
        if (bb-a).cross(c-a).length<area_epsilon:continue
        by.setdefault(slots[tri.material_index],[]).append(out)
    return [dict(material=m,corners=ts,unused=204) for m,ts in by.items()]


def generate_lods(data):
    report=[];levels=[]
    for level,ratio in ((1,.53),(2,.22)):
        objects={};stats=[]
        for entry in data['objects']:
            working=copy.deepcopy(entry);preserved=[]
            if entry['name']=='Root':
                working['groups']=[]
                for g in entry['groups']:
                    front=[t for t in g['corners'] if min(v[2] for v in t)<.11]
                    rest=[t for t in g['corners'] if min(v[2] for v in t)>=.11]
                    if front:preserved.append(dict(g,corners=front))
                    if rest:working['groups'].append(dict(g,corners=rest))
            obj,slots=mesh_object(working,entry['name'])
            # Flat cargo doors, rigid U sockets and glass contours must remain closed.
            count=sum(len(g['corners']) for g in entry['groups'])
            mod=obj.modifiers.new('Distance geometry','DECIMATE');mod.ratio=ratio
            if level==2:
                mod.ratio=.44 if entry['name']=='Root' else .53 if 'tail' in entry['name'].lower() else .40
            mod.use_collapse_triangulate=True
            if 'upperarm' in obj.name.lower() or obj.name.lower().startswith('baydoor'):mod.ratio=1
            evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh()
            groups=groups_from_mesh(me,slots)
            if '_glass_' in entry['name'].lower():
                groups=copy.deepcopy(entry['groups'])
            groups+=preserved
            reduced=sum(len(g['corners']) for g in groups)
            objects[entry['file']]=groups
            stats.append(dict(part=entry['name'],before=count,after=reduced))
            evaluated.to_mesh_clear();bpy.data.objects.remove(obj,do_unlink=True)
        levels.append(objects);report.append(dict(level=level,parts=stats,triangles=sum(s['after'] for s in stats)))
    (OUT/'lod_geometry.json').write_text(json.dumps(levels,separators=(',',':')))
    (OUT/'lod_generation.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256((OUT/'rh_concept_b.cmp').read_bytes()).hexdigest(),levels=report),indent=2))
    print('LODS',[(r['level'],r['triangles']) for r in report],flush=True)


def check_motion(data):
    objects={};entries={e['name']:e for e in data['objects']}
    for e in data['objects']:objects[e['name']]=mesh_object(e,e['name'])[0]
    for e in data['objects']:
        o=objects[e['name']];j=e['joint']
        if j['parent']:o.parent=objects[j['parent']]
        o.location=C@Vector(j['origin']);o.rotation_mode='QUATERNION'
        o.rotation_quaternion=(C@Matrix(j['rotation'])@C.transposed()).to_quaternion()
    def pose(tracks,phase):
        for track in tracks:
            keys=track['keys'];t=keys[-1][0]*phase
            angle=keys[-1][1]
            for a,bb in zip(keys,keys[1:]):
                if a[0]<=t<=bb[0]:angle=a[1]+(bb[1]-a[1])*(t-a[0])/(bb[0]-a[0]);break
            j=entries[track['object']]['joint'];o=objects[track['object']]
            o.rotation_quaternion=Quaternion(C@Vector(j['axis']),angle)@(C@Matrix(j['rotation'])@C.transposed()).to_quaternion()
        bpy.context.view_layer.update()
    def tree(obj):return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=0)
    overlaps=[]
    for i in range(121):
        phase=i/120;pose(data['animation'],phase)
        trees={n:tree(o) for n,o in objects.items()}
        for name in (n for n in objects if '_wing_' in n.lower()):
            for other in (n for n in objects if n!=name and not n.startswith('BayDoor')):
                hits=trees[name].overlap(trees[other])
                if hits:overlaps.append(dict(phase=round(phase,5),part=name,other=other,pairs=len(hits)))
    pose(data['animation'],0)
    doors=[]
    for i in range(61):
        pose(data['doors'],i/60);trees={n:tree(o) for n,o in objects.items()}
        for name in (n for n in objects if n.startswith('BayDoor')):
            for other in ('Root','Rh_glass_lod1','Rh_tail_lod1'):
                hits=trees[name].overlap(trees[other])
                if hits:doors.append(dict(phase=round(i/60,5),part=name,other=other,pairs=len(hits)))
    report=dict(cmp_sha256=hashlib.sha256((OUT/'rh_concept_b.cmp').read_bytes()).hexdigest(),wing_phases=121,
                wing_intersections=overlaps,door_phases=61,door_intersections=doors)
    (OUT/'motion_intersections.json').write_text(json.dumps(report,indent=2))
    print('MOTION',len(overlaps),'wing intersections;',len(doors),'door intersections',flush=True)


def search_pivot(data):
    objects={e['name']:mesh_object(e,e['name'])[0] for e in data['objects']}
    for e in data['objects']:
        j=e['joint'];o=objects[e['name']]
        if j['parent']:o.parent=objects[j['parent']]
        o.location=C@Vector(j['origin']);o.rotation_mode='QUATERNION'
        o.rotation_quaternion=(C@Matrix(j['rotation'])@C.transposed()).to_quaternion()
    bpy.context.view_layer.update()
    def tree(obj):return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=0)
    wing=objects['Rh_starboard_wing_lod1'];wp=[wing.matrix_world@v.co for v in wing.data.vertices]
    faces=[tuple(p.vertices) for p in wing.data.polygons]
    fixed={n:tree(o) for n,o in objects.items() if n in ('Root','Rh_tail_lod1','Rh_starboard_upperarm','Rh_starboard_engine_lod1')}
    winners=[];best=[]
    for xi in range(10):
        for zi in range(12):
            x=2.50+xi*.15;z=7.2+zi*.15;origin=C@Vector((x,-.5,z));hits=0
            for i in range(1,16):
                r=Quaternion(C@Vector((0,1,0)),math.radians(62)*i/15)
                tris=BVHTree.FromPolygons([origin+r@(p-origin) for p in wp],faces,all_triangles=True,epsilon=0)
                hits+=sum(len(tris.overlap(t)) for t in fixed.values())
            best.append((hits,x,z))
            if not hits:winners.append((x,z))
    print('PIVOT SEARCH',sorted(best)[:20],flush=True)
    (OUT/'pivot_search.json').write_text(json.dumps(dict(best=sorted(best)[:30],clear=winners),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lods',action='store_true');parser.add_argument('--motion',action='store_true');parser.add_argument('--search',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    data=json.loads((OUT/'blender_scene.json').read_text())
    if args.lods:generate_lods(data)
    if args.motion:check_motion(data)
    if args.search:search_pivot(data)
