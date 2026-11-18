"""Carve the Q13/04 cargo hold and real telescopic pockets. Offline Blender."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,groups_from_mesh,C

ROOT=HERE.parents[1]
SOURCE=ROOT/'out/ship_design/rh_freighter/prototypes/q13_04/geometry.json'
OUT=SOURCE.parents[1]/'rig_01'


def primitive(name,verts,faces,mat=3):
    me=bpy.data.meshes.new(name);me.from_pydata([C@Vector(v) for v in verts],[],faces);me.update()
    me.materials.append(bpy.data.materials.get(str(mat)))
    obj=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(obj)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    return obj


def prism(name,side,z,y,r,x0,x1,mat=3):
    k=math.sqrt(2)-1
    poly=[(-r,-r*k),(-r*k,-r),(r*k,-r),(r,-r*k),(r,r*k),(r*k,r),(-r*k,r),(-r,r*k)]
    verts=[(side*x,y+dy,z+dz) for x in (x0,x1) for dz,dy in poly]
    faces=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    return primitive(name,verts,faces,mat)


def box(name,lo,hi):
    x,y,z=lo;X,Y,Z=hi
    return primitive(name,[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


def boolean(obj,cutter,operation='DIFFERENCE'):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Functional clearance','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.update()


def overlaps(a,b):
    al=[min(v.co[i] for v in a.data.vertices) for i in range(3)];ah=[max(v.co[i] for v in a.data.vertices) for i in range(3)]
    bl=[min(v.co[i] for v in b.data.vertices) for i in range(3)];bh=[max(v.co[i] for v in b.data.vertices) for i in range(3)]
    return all(al[i]<bh[i] and bl[i]<ah[i] for i in range(3))


def main():
    OUT.mkdir(parents=True,exist_ok=True);raw=SOURCE.read_bytes();data=json.loads(raw)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in (1,2,3,4,5):bpy.data.materials.new(str(mat))
    objects={};entries={e['name']:e for e in data['objects']}
    for e in data['objects']:objects[e['name']]=mesh_object(e,e['name'])[0]
    core=next(o for n,o in objects.items() if n.startswith('Continuous hull'))
    hold=box('Cargo clearance',(-2.39,-3.10,-3.72),(2.39,12,5.72))
    for n,o in objects.items():
        if n.startswith(('Continuous hull','Rear engine transition')):boolean(o,hold)
    bpy.data.objects.remove(hold,do_unlink=True)
    modifications=[]
    for side in (-1,1):
        shell=objects[f'Faceted shoulder and intake well {side:+}']
        for i,z,r in [(0,-2.76,.72),(1,.66,1.11),(2,3.94,.72)]:
            back=1.33 if i==1 else 2.03
            housing=prism('Blind pocket outer wall',side,z,2.08,r*1.10,back,2.77)
            boolean(shell,housing,'UNION');bpy.data.objects.remove(housing,do_unlink=True)
            cut=prism('Full transverse travel clearance',side,z,2.08,r*1.04,back+.08,4.90)
            for name,obj in objects.items():
                if name.startswith(('Original','New transverse','Curved roof','Engine casing','Intake vane')):continue
                if overlaps(obj,cut):
                    before=len(obj.data.polygons);boolean(obj,cut)
                    modifications.append(dict(object=name,pocket=i,side=side,faces_before=before,faces_after=len(obj.data.polygons)))
            bpy.data.objects.remove(cut,do_unlink=True)
    output=[];checks=[]
    for name,obj in objects.items():
        e=entries[name]
        # Exact source cabin and glazing bytes are retained, never re-normalized.
        if name.startswith('Original'):output.append(e);continue
        bm=bmesh.new();bm.from_mesh(obj.data)
        # Booleans may leave collinear edges. Remove only geometric zero-area noise.
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        nonman=sum(not ed.is_manifold for ed in bm.edges)
        assert not nonman,(name,nonman)
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        if not obj.data.uv_layers:obj.data.uv_layers.new(name='Authoring UV')
        slots=[int(m.name) for m in obj.data.materials]
        gs=groups_from_mesh(obj.data,slots)
        output.append(dict(e,groups=gs));checks.append(dict(name=name,closed=True,triangles=sum(len(g['corners']) for g in gs)))
    data['objects']=output;data['mechanics']=dict(source_geometry=str(SOURCE),source_geometry_sha256=hashlib.sha256(raw).hexdigest(),
        hold_clearance=dict(x=[-2.39,2.39],y=[-3.10,12],z=[-3.72,5.72]),
        modifications=modifications,closed_shells=checks)
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    (OUT/'mechanics_prepare.json').write_text(json.dumps(data['mechanics'],indent=2),encoding='utf8')
    print('MECHANICS_READY',len(output),'objects',flush=True)


if __name__=='__main__':main()
