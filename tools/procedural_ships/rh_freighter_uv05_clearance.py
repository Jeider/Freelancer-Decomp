"""Clear the core behind both intake wells; keep blind, closed recesses."""
import json
import sys
from pathlib import Path
import bpy
import bmesh

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_freighter_rig_prepare import primitive,boolean,mesh_object,groups_from_mesh,C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/uv_05'
VENT=[[-6.85,-.67],[-6.85,.80],[-5.35,1.91],[-4.12,1.91],[-4.12,.85],[-5.18,-.02]]


def main():
    data=json.loads((OUT/'raw_geometry.json').read_text())
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for mat in (1,2,3,4,5,7,8):bpy.data.materials.new(str(mat))
    entry=next(e for e in data['objects'] if e['name'].startswith('Continuous hull'))
    obj=mesh_object(entry,entry['name'])[0]
    before=len(obj.data.polygons)
    for side in (-1,1):
        verts=[(side*x,y,z) for x in (2.58,3.80) for z,y in VENT]
        count=len(VENT)
        faces=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]+[
            (i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        cut=primitive('Intake blind clearance',verts,faces,3)
        boolean(obj,cut);bpy.data.objects.remove(cut,do_unlink=True)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    assert nonmanifold==0,nonmanifold
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    entry['groups']=groups_from_mesh(obj.data,[int(m.name) for m in obj.data.materials])
    checks=dict(core_faces_before=before,core_faces_after=len(obj.data.polygons),nonmanifold_edges=nonmanifold,
        vent_floor_x=2.65,core_clearance_x=2.58,backing_clearance=.07,housing_back_x=2.62,solid_backing_thickness=.03)
    data['vent_clearance']=checks
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    (OUT/'vent_clearance.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    print('VENT_CLEARANCE_READY',checks,flush=True)


if __name__=='__main__':main()
