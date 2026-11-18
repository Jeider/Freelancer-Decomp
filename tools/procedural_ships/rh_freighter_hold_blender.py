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
BASE=g.OUT;OUT=BASE/'hold_damage';g.OUT=OUT
DATA=json.loads((OUT/'input.json').read_text())
C=g.C

def tree(groups):
    ts=np.concatenate([np.array(a['corners'])[...,:3] for a in groups]);vs=ts.reshape(-1,3)
    return BVHTree.FromPolygons(vs.tolist(),np.arange(len(vs)).reshape(-1,3).tolist(),all_triangles=True)

def pieces(poly,axis,value):
    """Split existing UV charts without changing their texture phase."""
    out=[]
    for positive in (False,True):
        ps=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            da=a[axis]-value;db=b[axis]-value
            if (da>=-1e-9 if positive else da<=1e-9):ps.append(a)
            if da*db < -1e-16:ps.append(a+(b-a)*da/(da-db))
        if len(ps)>=3:out.append(np.array(ps))
    return out

def narrow(t,minimum=False):
    t=t.copy();p=t[...,:3]
    z=p[...,2];y=p[...,1]
    zphase=np.clip((z+4.4)/.68,0,1)*np.clip((7.8-z)/.65,0,1)
    yphase=np.clip(y/.215,0,1)
    scale=1+(1.25/(3.2 if minimum else 2.72)-1)*yphase*zphase
    p[...,0]*=scale
    n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1),1e-15)[:,None]
    t[:,:,3:6]=n[:,None,:]
    return t

def deform(groups,selectors,split=True,minimum=False):
    result=[];count=0
    for a,mask in zip(groups,selectors):
        ts=[]
        for tri,selected in zip(np.array(a['corners']),mask):
            if not selected:ts.append(tri);continue
            count+=1;polys=[tri]
            if tri[:,1].max()<=0 or tri[:,2].min()>=7.8 or tri[:,2].max()<=-4.4:
                ts.append(tri);continue
            if split:
                for axis,v in ((1,0),(1,.215),(2,-4.4),(2,-3.72),(2,7.15),(2,7.8)):
                    tmp=[]
                    for poly in polys:
                        if poly[:,axis].min()<v-1e-7 and poly[:,axis].max()>v+1e-7:tmp+=pieces(poly,axis,v)
                        else:tmp.append(poly)
                    polys=tmp
            for poly in polys:
                for i in range(1,len(poly)-1):
                    t=narrow(np.array([[poly[0],poly[i],poly[i+1]]]),minimum)[0]
                    if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-9:ts.append(t)
        result.append(dict(a,corners=np.array(ts)))
    return result,count

def roof_clearance(groups):
    """A real channel for the shutter sweep, with closed brown cut walls."""
    ob,_=g.mesh_object(dict(groups=groups),'Narrowed fixed cargo core')
    print('CORE CONFORM',g.conform(ob),flush=True)
    bm=bmesh.new();bm.from_mesh(ob.data);edges=[e for e in bm.edges if e.is_boundary]
    assert len(edges)<32,len(edges)
    if edges:
        faces=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];area=sum(p.calc_area() for p in faces)
        print('SUBPIXEL SEAMS',len(edges),area,flush=True);assert area<.005,area
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    # 64-sided concentric channel encloses the exact native rotating roof.
    verts=[];n=24
    for x in (-2.36,2.36):
        for radius in (4.27,4.82):
            for i in range(n):
                a=2*math.pi*i/n;verts.append((x,2.4349513+radius*math.cos(a),.9392922+radius*math.sin(a)))
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                      (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
    cutter=g.object_from_points('Complete roof sweep channel',verts,faces,529652695)
    bpy.context.view_layer.objects.active=ob
    # Preserve native UV islands; only the newly cut mechanical edge gets brown.
    g.boolean(ob,cutter)
    uv=ob.data.uv_layers.active
    for p in ob.data.polygons:
        if int(ob.data.materials[p.material_index].name)!=529652695:continue
        for li in p.loop_indices:
            co=C.transposed()@ob.data.vertices[ob.data.loops[li].vertex_index].co
            uv.data[li].uv=(.20+co.z*.12,1-(.3+co.y*.12))
    mod=ob.modifiers.new('Remove coplanar transfer cuts','DECIMATE');mod.decimate_type='DISSOLVE';mod.angle_limit=.0001
    mod.delimit={'UV','MATERIAL','NORMAL'};bpy.ops.object.modifier_apply(modifier=mod.name)
    # Only the newly inset core is eligible. Keep external cornices/deck/belly
    # expensive to collapse so their approved atlas boundaries remain stable.
    group=ob.vertex_groups.new(name='Internal hold only')
    for v in ob.data.vertices:
        p=C.transposed()@v.co
        eligible=abs(p.x)<2.36 and p.y>.01 and -4.35<p.z<7.75
        group.add([v.index],1 if eligible else 0,'REPLACE')
    mod=ob.modifiers.new('Simplify internal shutter clearance','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=.66
    mod.vertex_group=group.name;mod.vertex_group_factor=1000
    bpy.ops.object.modifier_apply(modifier=mod.name)
    gs=g.groups_from_mesh(ob.data,[int(m.name) for m in ob.data.materials])
    stat=g.topology(ob);print('CORE CHANNEL',stat,sum(len(a['corners']) for a in gs),flush=True)
    assert not stat['boundary_edges'] and not stat['nonmanifold_edges'],stat
    bpy.data.objects.remove(ob,do_unlink=True)
    return gs

def author():
    g.clear();g.materials()
    raw=json.loads((BASE.parent/'prototypes/uv_15/mechanical_geometry.json').read_text())['objects']
    src=[o for o in raw if o['name'].startswith(('Continuous hull','Raised cargo deck'))]
    owned=json.loads((OUT/'owned_core.json').read_text())
    def key(t):return tuple(sorted(tuple(p.round(4)) for p in np.array(t)[:,:3]))
    keys={(a['material'],key(t)) for a in owned for t in a['corners']}
    ownedtris=[(a['material'],np.array(t)[:,:3]) for a in owned for t in a['corners']]
    kd=KDTree(len(ownedtris))
    for i,(_,ts) in enumerate(ownedtris):kd.insert(Vector(ts.mean(0)),i)
    kd.balance()
    bv=tree([a for o in src for a in o['groups']]);roots=[];counts=[]
    gs=DATA['levels'][0]['Root'];masks=[]
    for a in gs:
        mask=[]
        for t in np.array(a['corners']):
            p=t[:,:3].mean(0);hit=bv.find_nearest(Vector(p))
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n)
            match=(a['material'],key(t)) in keys
            if not match:
                for _,ix,_ in kd.find_range(Vector(p),.0001):
                    mid,other=ownedtris[ix]
                    if mid==a['material'] and np.linalg.norm(t[:,:3,None]-other.T[None,:,:],axis=1).min(1).max()<.0001:
                        match=True;break
            mask.append(match)
        masks.append(mask)
    print('CORE OWNERSHIP',sum(sum(m) for m in masks),sum(len(a['corners']) for a in owned),flush=True)
    assert sum(sum(m) for m in masks)>=sum(len(a['corners']) for a in owned)-5
    selected=[dict(a,corners=np.array(a['corners'])[mask]) for a,mask in zip(gs,masks) if any(mask)]
    untouched=[dict(a,corners=np.array(a['corners'])[np.logical_not(mask)]) for a,mask in zip(gs,masks) if not all(mask)]
    changed,count=deform(selected,[np.ones(len(a['corners']),bool) for a in selected])
    if '--diagnose' in sys.argv:
        dist=[];ang=[]
        for a in gs:
            for tri in np.array(a['corners']):
                h=bv.find_nearest(Vector(tri[:,:3].mean(0)))
                nn=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]);nn/=np.linalg.norm(nn)
                dist.append(h[3]);ang.append(abs(np.dot(nn,h[1])))
        print('NEAREST',[(ep,int(np.sum(np.array(dist)<ep)),int(np.sum((np.array(dist)<ep)&(np.array(ang)>.995)))) for ep in (.00015,.001,.01,.05)],flush=True)
        alltree=tree(gs)
        rev=[]
        for o in src:
            for a in o['groups']:
                for t in np.array(a['corners']):
                    h=alltree.find_nearest(Vector(t[:,:3].mean(0)));rev.append(h[3])
        print('REVERSE',np.quantile(rev,[0,.5,.9,.99,1]),flush=True)
        for label,items in [('raw',[a for o in src for a in o['groups']]),('selected',selected),('changed',changed)]:
            for a in items:
                key=str(a['material'])
                if key not in bpy.data.materials:bpy.data.materials.new(key)
            ob,_=g.mesh_object(dict(groups=items),label)
            print('DIAG',label,g.conform(ob),g.topology(ob),flush=True)
        return
    root=untouched+roof_clearance(changed);roots.append(root);counts.append(count)
    # Known component ranges from the authored 1776-triangle structural proxy.
    gs=DATA['levels'][1]['Root'];masks=[]
    for a in gs:
        n=len(a['corners']);mask=np.zeros(n,bool)
        if n==678:mask[32:294]=True;mask[-12:]=True
        masks.append(mask)
    assert sum(sum(m) for m in masks)==274
    roots.append(deform(gs,masks,False)[0])
    # The far proxy still has 494 triangles; only its 36-triangle cargo box moves.
    gs=DATA['levels'][2]['Root'];masks=[]
    for a in gs:
        mask=np.zeros(len(a['corners']),bool);mask[:36]=True;masks.append(mask)
    roots.append(deform(gs,masks,False,True)[0])
    bv=tree(roots[0]);lights={}
    # Surface rays anchor emitters on the fixed structure, away from moving lids.
    rays={
      'hprunninglight01':((-8,4.89,-3.30),(1,0,0)),
      'hprunninglight02':((8,4.89,-3.30),(-1,0,0)),
      'hprunninglight03':((1.30,12,9.2),(0,-1,0)),
      'hprunninglight04':((-1.30,12,9.2),(0,-1,0)),
      'hprunninglight05':((-2.60,-10,-4.0),(0,1,0)),
      'hprunninglight06':((2.60,-10,-4.0),(0,1,0)),
      'hprunninglight07':((0,12,-8.15),(0,-1,0)),
      'hpdocklight01':((-1.8,1.45,16),(0,0,-1)),
      'hpdocklight02':((1.8,1.45,16),(0,0,-1)),
    }
    for k,h in DATA['hardpoints'].items():
        if 'light' not in k:continue
        if k in rays:
            origin,direction=rays[k];hit=bv.ray_cast(Vector(origin),Vector(direction),30)
        else:hit=bv.find_nearest(Vector(h['position']))
        assert hit[0] is not None,k
        p=np.array(hit[0])+np.array(hit[1])*.035
        lights[k]=dict(name=h['name'],before=h['position'],after=p,surface=list(hit[0]),normal=list(hit[1]),offset=.035)
    g.dump('geometry.json',dict(roots=roots,lights=lights,core_near_triangles_selected=count,
        old_floor_half_width=2.405,new_floor_half_width=2.405*1.25/2.72,
        outer_wall_half_width=1.25,folded_big_button_inner_x=1.51,floor_height_unchanged=.355))
    damage.author(deep=True)
    print('NARROW HOLD AUTHORED',count,flush=True)

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
    opening=bvh(objs['Baydoor_lod1']).ray_cast(C@Vector((0,.855,.9)),C@Vector((0,1,0)),30)[0]
    report=dict(cmp_sha256=exported['cmp_sha256'],baydoor_samples=65,slider_samples=49,collisions=collisions,hold_rays=rays,open_axis_clear=opening is None)
    g.dump('motion_check.json',report)
    assert not collisions,collisions[:5]
    assert opening is None
    # Probe the fracture in the surviving assembly. Opaque ROOT must not fill
    # the new recess before the exposed inner structure can be seen.
    root=tree(data['roots'][0]);wounds=json.loads((OUT/'damage_world.json').read_text());depth=[]
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
    full=tree(data['roots'][0]+[a for name,items in DATA['levels'][0].items() if name!='Root' for a in items])
    lampchecks=[]
    for k,h in data['lights'].items():
        p=Vector(h['after']);normal=Vector(h['normal']);near=full.find_nearest(p)
        outward=full.ray_cast(p,normal,1.0)
        lampchecks.append(dict(name=k,nearest_distance=near[3],outward_clear=outward[0] is None))
    report['light_clearance']=lampchecks;g.dump('motion_check.json',report)
    assert all(c['nearest_distance']>.015 and c['outward_clear'] for c in lampchecks),lampchecks
    # Preview authoring scene in flight pose; damage examples in a disabled collection.
    pose(1,0)
    damagecol=bpy.data.collections.new('Deep damage / enable for inspection');bpy.context.scene.collection.children.link(damagecol)
    wounds=json.loads((OUT/'damage_world.json').read_text())
    for name in ('port_side_panel','starboard_side_panel'):
        ob,_=g.mesh_object(dict(groups=wounds[name]),'Damaged '+name)
        for col in list(ob.users_collection):col.objects.unlink(ob)
        damagecol.objects.link(ob)
    damagecol.hide_viewport=True;damagecol.hide_render=True
    for h in data['lights'].values():
        ob=bpy.data.objects.new(h['name'],None);bpy.context.scene.collection.objects.link(ob)
        ob.empty_display_type='SPHERE';ob.empty_display_size=.09;ob.location=C@Vector(h['after'])
    bpy.context.preferences.filepaths.save_version=0;bpy.context.preferences.filepaths.file_preview_type='NONE'
    path=OUT/'rh_pir_freighter_review.blend';colname=damagecol.name
    bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    assert bpy.data.collections[colname].hide_render and bpy.data.collections[colname].hide_viewport
    print('PASS FULL NATIVE MOTION AND NARROW HOLD',flush=True)

if __name__=='__main__':
    check() if '--check' in sys.argv else author()
