"""Cut the carrier and inspect the actual surviving assembly with culling."""
import json
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_elite_torn_damage_blender as a
OLD=a.OUT;OUT=OLD.parent/'damage_05';a.OUT=OUT


def main():
    data=json.loads((OUT/'input.json').read_text());a.DATA=data;a.clear();low,high=data['split_height']
    frame=data['frame_source'];pieces={};stats={}
    for name in ('upper','lower','tail'):
        ob,_=a.mesh_object(dict(groups=frame),'Frame_'+name)
        bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.index_update();seen=set();duplicates=[]
        for face in bm.faces:
            key=tuple(sorted(v.index for v in face.verts))
            if key in seen:duplicates.append(face)
            else:seen.add(key)
        if duplicates:bmesh.ops.delete(bm,geom=duplicates,context='FACES_ONLY')
        bm.to_mesh(ob.data);bm.free();a.topology(ob)
        if name in ('upper','tail'):
            bound=high if name=='upper' else low
            a.cut(ob,a.prism('Below plane',[[-8,0],[bound,0],[bound,12],[-8,12]],(1,2),-3,3))
        if name in ('lower','tail'):
            bound=low if name=='lower' else high
            a.cut(ob,a.prism('Above plane',[[bound,0],[8,0],[8,12],[bound,12]],(1,2),-3,3))
        a.remap(ob);pieces[name]=a.groups(ob);stats[name]=a.topology(ob)
        if name!='tail':bpy.data.objects.remove(ob,do_unlink=True)
        else:tail_ob=ob
    data['parts_override']={'Root':data['root_without_frame']+pieces['upper']+pieces['lower'],
        'Rh_tail_lod1':data['base_parts']['Rh_tail_lod1']+pieces['tail']}
    data['ownership_split']=dict(from_part='Root',to_part='Rh_tail_lod1',native_y_planes=[low,high],
        full_frame_retained=False,drum_unchanged=True,upper_and_lower_stay_on_root=True,
        moved_triangles=sum(len(g['corners']) for g in pieces['tail']))
    # Tear right through the newly transferred core. Only its short irregular
    # upper/lower ends remain, connecting to the fixed frame at the split planes.
    zs=np.array([6.6,7.15,7.48,7.78,8.06,8.33,8.60,9.2])
    bottom=np.array([-.46,-.42,-.31,-.52,-.33,-.50,-.28,-.44])
    top=np.array([2.96,2.91,2.78,3.04,2.83,3.02,2.79,2.94])
    poly=[[y,z] for y,z in zip(bottom,zs)]+[[y,z] for y,z in zip(top[::-1],zs[::-1])]
    a.cut(tail_ob,a.prism('Through rupture',poly,(1,2),-3,3))
    a.remap(tail_ob,lambda p:min(abs(p[1]-np.interp(p[2],zs,top)),abs(p[1]-np.interp(p[2],zs,bottom)))<.23)
    core_damage=a.groups(tail_ob);stats['torn_core']=a.topology(tail_ob)
    wounds=json.loads((OLD/'damage_world.json').read_text());wounds['tail']+=core_damage
    data['parts']=dict(data['parts'],**data['parts_override'])
    a.dump('input.json',data);a.dump('damage_world.json',wounds)
    a.dump('frame_split_geometry.json',dict(pieces=pieces,core_damage=core_damage,stats=stats,low=low,high=high))
    geom=json.loads((OLD/'damage_geometry_check.json').read_text());geom['tail']['carrier_cut']=stats
    geom['tail']['method']='Outer torn sleeve plus short ruptured carrier ends; middle carrier detaches with Tail'
    a.dump('damage_geometry_check.json',geom)
    print('FRAME CUT: middle carrier now Tail; top/bottom and drum stay Root',flush=True)


def review():
    import rh_elite_torn_damage_review as reviewer
    reviewer.OUT=OUT;reviewer.main()
    data=json.loads((OUT/'review_data.json').read_text());parts=data['assembly'];allgroups=[g for gs in parts.values() for g in gs]
    tree=reviewer.tree(allgroups);rays=[]
    # These center rays hit the unbroken rear post in damage_04. All must now
    # pass through the tail opening; the drum itself lies forward of z=7.98.
    for x in (-.35,0,.35):
        for y in (.25,1.65,2.25):
            origin=Vector((x,y,10.0));loc,normal,_,dist=tree.ray_cast(origin,Vector((0,0,-1)),2.02)
            assert loc is None,('rear opening still blocked',x,y,loc)
            rays.append(dict(x=x,y=y,clear=True))
    a.dump('opening_check.json',dict(cmp_sha256=data['cmp_sha256'],rays=rays,clearance_z=[7.98,10.0]))
    print('OPENING VERIFIED: 9 center rays no longer hit an intact rear post',flush=True)


if __name__=='__main__':
    review() if '--review' in sys.argv else main()
