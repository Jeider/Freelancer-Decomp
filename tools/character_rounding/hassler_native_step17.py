"""Keep STEP15's close belt fit; correct only visible cloth breakthroughs."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step15 as s
from hassler_step13_check import snapshot
from hassler_step04_check import rig_snapshot
from hassler_step08_check import evaluated
configure('character_rounding')
TOP=s.TOP;OUT=TOP/'step_17';PARENT=s.OUT/'hassler_native_upper.blend'
CENTER=np.array([0.,.04]);CHANGED=(s.BELT,s.BUCKLE,s.LOOPS)


def outer_surface():
    ob=bpy.data.objects[s.BELT];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    points=[v.co[:] for v in me.vertices]
    # The three outward-facing section spans include both narrow bevels.
    faces=[list(t.vertices) for t in me.loop_triangles if t.polygon_index%8 in (0,1,2)]
    tree=BVHTree.FromPolygons(points,faces,all_triangles=True);ev.to_mesh_clear()
    return tree,np.array(points)


def scan():
    tree,p=outer_surface();cloth=[evaluated(bpy.data.objects[n])['tree'] for n in (s.LOWER,s.WAIST)]
    lo,hi=p[:,2].min(),p[:,2].max();gap=np.full(720,np.inf)
    for z in np.linspace(lo+.00015,hi-.00015,17):
        for i,a in enumerate(np.linspace(0,2*math.pi,720,endpoint=False)):
            origin=Vector((*CENTER,z));direction=Vector((math.sin(a),math.cos(a),0))
            hit=tree.ray_cast(origin,direction,1.);assert hit[0] is not None
            radii=[q[3] for t in cloth if (q:=t.ray_cast(origin,direction,1.))[0] is not None];assert radii
            gap[i]=min(gap[i],hit[3]-max(radii))
    return gap


def main():
    OUT.mkdir(exist_ok=True);parent_hash=s.s13.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    names=[o.name for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.type=='MESH']+['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged']
    before={n:snapshot(bpy.data.objects[n]) for n in names};bones=rig_snapshot();gaps=scan()
    required=np.maximum(0,.00065-gaps)
    # Each station covers the actual adjacent face spans. A narrow smooth
    # envelope avoids a kink, without inflating the whole strap by the maximum.
    need=np.array([max(required[(np.arange(i*10-10,i*10+11))%720]) for i in range(72)])
    delta=np.array([max(need[j]*math.exp(-.5*(min(abs(i-j),72-abs(i-j))/1.15)**2) for j in range(72)) for i in range(72)])
    delta[delta<.00001]=0
    assert delta.max()<.006,('Correction too large',float(delta.max()))
    belt=bpy.data.objects[s.BELT]
    assert len(belt.data.vertices)==72*8
    for v in belt.data.vertices:
        d=np.array(v.co[:2])-CENTER;d/=np.linalg.norm(d)
        v.co.x+=float(d[0]*delta[v.index//8]);v.co.y+=float(d[1]*delta[v.index//8])
    def amount(point):
        a=math.atan2(point[0],point[1]-.04)%(2*math.pi);t=a*72/(2*math.pi);i=int(t)
        return (1-(t-i))*delta[i]+(t-i)*delta[(i+1)%72]
    # Keep the fittings rigid and move only as much as their strap patch moved.
    for name in (s.BUCKLE,s.LOOPS):
        ob=bpy.data.objects[name];adj={i:set() for i in range(len(ob.data.vertices))}
        for e in ob.data.edges:
            a,b=e.vertices;adj[a].add(b);adj[b].add(a)
        pending=set(adj)
        if name==s.BUCKLE:components=[list(pending)];pending.clear()
        else:components=[]
        while pending:
            todo=[next(iter(pending))];component=set()
            while todo:
                a=todo.pop()
                if a in component:continue
                component.add(a);todo.extend(adj[a]-component)
            pending-=component;components.append(list(component))
        for ids in components:
            q=np.mean([ob.data.vertices[i].co[:2] for i in ids],axis=0);d=q-CENTER;d/=np.linalg.norm(d);move=amount(q)
            for i in ids:
                ob.data.vertices[i].co.x+=float(d[0]*move);ob.data.vertices[i].co.y+=float(d[1]*move)
    for name in CHANGED:s.s9.recalc(bpy.data.objects[name])
    belt['construction']='STEP17: original STEP15 fit, local millimetre outer clearance corrections only. No uniform expansion. Inner contact with hidden cloth is allowed; exposed outer face is checked.'
    aftergaps=scan();assert aftergaps.min()>.0004,('Outer clearance',float(aftergaps.min()))
    report={'step':'17 close belt fit with local corrections','parent':str(PARENT),'parent_sha256':parent_hash,'rejected_uniform_step16_offset_m':.012,'station_offsets_m':delta.tolist(),'max_offset_m':float(delta.max()),'mean_offset_m':float(delta.mean()),'outside_clearance_before_m':float(gaps.min()),'outside_clearance_after_m':float(aftergaps.min()),'hidden_inner_contact_allowed':True,'cloth_geometry_unchanged':True,'height_z_uv_skin_preserved':True,'game_installed':False}
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2));s.native.activate(belt)
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    for name,old in before.items():
        now=snapshot(bpy.data.objects[name])
        for k in ('faces','weights','materials','material_indices'):assert old[k]==now[k],(name,k)
        for k,v in old['uv_layers'].items():assert np.array_equal(v,now['uv_layers'][k]),(name,k)
        assert np.array_equal(old['world'],now['world'])
        if name not in CHANGED:assert np.array_equal(old['points'],now['points']) and np.array_equal(old['normals'],now['normals']),name
        else:
            assert np.array_equal(old['points'][:,2],now['points'][:,2])
            bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free()
    newbones=rig_snapshot();assert set(newbones)==set(bones)
    for name,(m,w,p) in newbones.items():assert np.array_equal(m,bones[name][0]) and w==bones[name][1] and p==bones[name][2]
    poses=[]
    for frame in (1,30,60,90,120):
        scene.frame_set(frame);outside,_=outer_surface();whole=evaluated(bpy.data.objects[s.BELT]);contacts={}
        for name in (s.LOWER,s.WAIST,s.s13.GARMENT):
            other=evaluated(bpy.data.objects[name])['tree'];visible=outside.overlap(other);assert not visible,('Exposed crossing',frame,name,visible[:5])
            contacts[name]={'exposed_crossings':0,'hidden_inner_contacts':len(whole['tree'].overlap(other))}
            if name==s.s13.GARMENT:assert not contacts[name]['hidden_inner_contacts']
        poses.append({'frame':frame,'contacts':contacts})
    scene.frame_set(1);now=np.array([v.co[:] for v in bpy.data.objects[s.BELT].data.vertices]);old=before[s.BELT]['points']
    report['belt_bbox_before_m']=[old.min(axis=0).tolist(),old.max(axis=0).tolist()];report['belt_bbox_after_m']=[now.min(axis=0).tolist(),now.max(axis=0).tolist()]
    report['width_increase_m']=float(np.ptp(now[:,0])-np.ptp(old[:,0]))
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_viewport and col.hide_render
    result={'reopened':True,'checks_passed':True,'blend_sha256':s.s13.sha(path),'parent_sha256':parent_hash,'other_objects_exact':len(names)-3,'rig_exact':True,'belt_height_uv_topology_weights_preserved':True,'outside_clearance_min_m':float(scan().min()),'poses':poses,'game_installed':False,'game_animations_validated':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('BELT17',json.dumps({k:report[k] for k in ('max_offset_m','mean_offset_m','width_increase_m','outside_clearance_after_m')}),flush=True)
    if '--no-render' not in sys.argv:
        s.OUT=OUT
        for label,direction,target,scale in [('waist_front',(0,1,.08),(0,.02,1.15),.59),('waist_side',(1,0,.1),(0,.02,1.15),.59),('waist_back',(0,-1,.08),(0,.02,1.15),.59),('full_front',(0,1,.03),(0,0,.99),2.08)]:s.render(scene,label,direction,target,scale)
        result['previews_bound_to_blend_sha256']=result['blend_sha256']
    assert s.s13.sha(path)==result['blend_sha256'] and s.s13.sha(PARENT)==parent_hash
    (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
