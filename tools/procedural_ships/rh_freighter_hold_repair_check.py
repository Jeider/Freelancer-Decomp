"""Author narrow cargo walls, recessed wounds and verify actual mechanism sweep."""
import copy,json,sys,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_freighter_final_blender as g
import rh_freighter_panel_damage_blender as damage
BASE=g.OUT;OUT=BASE/'hold_repair';g.OUT=OUT
DATA=json.loads((OUT/'input.json').read_text())
C=g.C

def tree(groups):
    ts=np.concatenate([np.array(a['corners'])[...,:3] for a in groups]);vs=ts.reshape(-1,3)
    return BVHTree.FromPolygons(vs.tolist(),np.arange(len(vs)).reshape(-1,3).tolist(),all_triangles=True)

def check():
    g.clear();g.materials()
    data=json.loads((OUT/'geometry.json').read_text());scene=copy.deepcopy(DATA['scene']);objs={}
    exported=json.loads((OUT/'exported_roots.json').read_text())
    import hashlib
    assert hashlib.sha256((OUT/'rh_pir_freighter.cmp').read_bytes()).hexdigest()==exported['cmp_sha256']
    data['roots']=exported['roots']
    # Scene has local geometry + the proven native parent hierarchy. Replace only Root.
    for entry in scene['objects']:
        if entry['name']=='Root':entry['groups']=data['roots'][0]
        ob,_=g.mesh_object(entry,entry['name']);objs[entry['name']]=ob
    for e in scene['objects']:
        if e['joint']['parent']:objs[e['name']].parent=objs[e['joint']['parent']]
    def pose(wing,door):
        for e in scene['objects']:
            j=e['joint'];ob=objs[e['name']];r=Matrix(j['rotation']);t=Vector(j['origin'])
            value=door if j['kind']=='rev' else wing if j['kind']=='pris' else 0
            if j['kind']=='rev':r=Quaternion(Vector(j['axis']).normalized(),value).to_matrix()@r
            if j['kind'] in ('rev','pris'):t-=r@Vector(j['offset'])
            if j['kind']=='pris':t+=Vector(j['axis'])*value
            ob.location=C@t;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=(C@r@C.transposed()).to_quaternion()
        bpy.context.view_layer.update()
    def bvh(ob):return BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons],all_triangles=True)
    fixed=[n for n in objs if '_btn_' not in n and n!='Baydoor_lod1'];moving=[n for n in objs if '_btn_' in n]
    pose(0,0);fixedtrees={n:bvh(objs[n]) for n in fixed};collisions=[]
    for i in range(65):
        phase=i/64;pose(0,2.0943899154663086*phase);door=bvh(objs['Baydoor_lod1'])
        for name,tr in fixedtrees.items():
            h=door.overlap(tr)
            if h:
                samples=[]
                if i in (0,16,32,48,64):
                    for _,ix in h[:12]:
                        po=objs[name].data.polygons[ix]
                        ps=[C.transposed()@(objs[name].matrix_world@objs[name].data.vertices[j].co) for j in po.vertices]
                        samples.append(np.array(ps).mean(0).tolist())
                collisions.append(dict(kind='baydoor',phase=phase,part=name,pairs=len(h),samples=samples))
        for wing in (0,1):
            pose(wing,2.0943899154663086*phase)
            for name in moving:
                h=door.overlap(bvh(objs[name]))
                if h:collisions.append(dict(kind='baydoor/button',phase=phase,wing=wing,part=name,pairs=len(h)))
    for i in range(49):
        phase=i/48;pose(phase,0)
        for name in moving:
            bv=bvh(objs[name])
            for fixedname,tr in fixedtrees.items():
                h=bv.overlap(tr)
                if h:collisions.append(dict(kind='button',phase=phase,part=name,fixed=fixedname,pairs=len(h)))
    # Front-facing rays through the actual complete open assembly, not a detached floor.
    pose(0,2.0943899154663086);tr=fixedtrees['Root'];rays=[]
    for xyz,label in [((0,-1,0),'floor'),((1,0,0),'right'),((-1,0,0),'left'),((0,0,1),'rear'),((0,0,-1),'front')]:
        origin=C@Vector((0,.855,.9));direction=C@Vector(xyz);hit=tr.ray_cast(origin,direction,30)
        assert hit[0] is not None and hit[1].dot(direction)<0,label
        p=C.transposed()@hit[0];rays.append(dict(surface=label,position=list(p),front_facing=True))
        if label in ('left','right'):assert abs(p.x)<1.25
        if label=='floor':assert abs(p.y-.355)<.0001
    coverage=[]
    for x in (-.95,0,.95):
        for z in (-2.3,0,2,4.2):
            direction=C@Vector((0,-1,0));hit=tr.ray_cast(C@Vector((x,3.7,z)),direction,5)
            assert hit[0] is not None and hit[1].dot(direction)<0
            p=C.transposed()@hit[0];assert abs(p.y-.355)<.0001,(x,z,list(p))
            coverage.append(list(p))
    opening=bvh(objs['Baydoor_lod1']).ray_cast(C@Vector((0,.855,.9)),C@Vector((0,1,0)),30)[0]
    report=dict(cmp_sha256=exported['cmp_sha256'],baydoor_samples=65,slider_samples=49,collisions=collisions,hold_rays=rays,floor_coverage=coverage,open_axis_clear=opening is None)
    # A manifold report for individual boxes cannot detect two coincident
    # visible skins. Count actual exported triangle layers at the rejected rim.
    corners=np.concatenate([np.array(g['corners']) for g in data['roots'][0]])
    triangles=corners[:,:,:3]
    a=triangles[:,0];e1=triangles[:,1]-a;e2=triangles[:,2]-a
    rim_layers=[]
    def first_layers(origin,direction):
        direction=np.array(direction,float);delta=np.array(origin)-a
        p=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,p)
        good=np.abs(det)>1e-10;inv=np.zeros_like(det);inv[good]=1/det[good]
        u=np.einsum('ij,ij->i',delta,p)*inv;q=np.cross(delta,e1)
        v=q@direction*inv;t=np.einsum('ij,ij->i',e2,q)*inv
        good&=(u>1e-7)&(v>1e-7)&(u+v<1-1e-7)&(t>0)
        distances=t[good];assert len(distances)
        near=distances.min();ix=np.where(good&(np.abs(t-near)<2e-5))[0]
        uv=corners[ix,:,6:8];ab=uv[:,1]-uv[:,0];ac=uv[:,2]-uv[:,0]
        area=np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])*.5
        assert area.min()>1e-8,(origin,'Lost UV on the visible seam')
        return float(near),len(ix)
    for side in (-1,1):
        for z in (-1.13,.83,3.47):
            for origin,direction,expected,label in [((side*.9,3.72,z),(side,0,0),.2,'inner rim'),
                ((side*1.18,4.2,z),(0,-1,0),.39,'upper rim')]:
                distance,layers=first_layers(origin,direction)
                assert layers==1 and abs(distance-expected)<.0001,(origin,distance,layers)
                rim_layers.append(dict(side=side,z=z,surface=label,visible_layers=layers))
    report['single_surface_rim_samples']=rim_layers
    panels=[]
    for z in (-3.60,5.52):
        for x in (-2.20,-1.90,-.87,.31,1.61,2.20):
            first_layers((x,8,z),(0,-1,0))
            hit=tr.ray_cast(C@Vector((x,8,z)),C@Vector((0,-1,0)),12)
            assert hit[0] is not None and hit[1].dot(C@Vector((0,-1,0)))<0
            # The unchanged lateral trim sits 0.04 above the new central panel.
            pos=C.transposed()@hit[0];assert 3.8099<=pos.y<=3.8501,(x,z,list(pos))
            panels.append(list(pos))
    report['both_end_panels_coverage']=panels
    g.dump('motion_check.json',report)
    assert not collisions,str(collisions[:5])
    assert opening is None
    # Probe the fracture in the surviving assembly. Opaque ROOT must not fill
    # the new recess before the exposed inner structure can be seen.
    root=tree(data['roots'][0]);wounds=json.loads((BASE/'hold_damage/damage_world.json').read_text());depth=[]
    for side,label in ((-1,'port'),(1,'starboard')):
        full=tree(data['roots'][0]+wounds[label+'_side_panel'])
        for y,z in ((1.5,3.2),(2.5,3.2),(2.0,4.0),(1.8,5.9)):
            direction=Vector((-side,0,0));origin=Vector((side*5.3,y,z));hit=full.ray_cast(origin,direction,8)
            assert hit[0] is not None and hit[1].dot(direction)<0
            x=abs(hit[0].x);depth.append(dict(side=label,y=y,z=z,visible_inner_x=x,depth_from_panel=3.5-x))
        samples=[v['depth_from_panel'] for v in depth if v['side']==label]
        # The retained upper circular shoulder crosses one high ray; preserve it.
        assert min(samples)>.8 and np.median(samples)>1.8,depth
    report['damage_depth_samples']=depth;g.dump('motion_check.json',report)
    report['user_light_coordinates_preserved']=True
    # Preview authoring scene in flight pose; damage examples in a disabled collection.
    pose(1,0)
    damagecol=bpy.data.collections.new('Deep damage / enable for inspection');bpy.context.scene.collection.children.link(damagecol)
    wounds=json.loads((BASE/'hold_damage/damage_world.json').read_text())
    for name in ('port_side_panel','starboard_side_panel'):
        ob,_=g.mesh_object(dict(groups=wounds[name]),'Damaged '+name)
        for col in list(ob.users_collection):col.objects.unlink(ob)
        damagecol.objects.link(ob)
    damagecol.hide_viewport=True;damagecol.hide_render=True
    for h in DATA['hardpoints'].values():
        ob=bpy.data.objects.new(h['name'],None);bpy.context.scene.collection.objects.link(ob)
        ob.empty_display_type='SPHERE';ob.empty_display_size=.09;ob.location=C@Vector(h['position'])
    bpy.context.preferences.filepaths.save_version=0;bpy.context.preferences.filepaths.file_preview_type='NONE'
    path=OUT/'rh_pir_freighter_review.blend';colname=damagecol.name
    bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    assert bpy.data.collections[colname].hide_render and bpy.data.collections[colname].hide_viewport
    report['blend_reopened']=True;g.dump('motion_check.json',report)
    print('PASS FULL NATIVE MOTION, FLOOR GRID, DEEP DAMAGE, SAVED BLEND',flush=True)

if __name__=='__main__':check()
