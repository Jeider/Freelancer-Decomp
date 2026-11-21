"""Give the accepted waist belt a little radial clearance over the trousers."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step15 as s
from hassler_step13_check import snapshot
from hassler_step04_check import rig_snapshot
from hassler_step08_check import evaluated
configure('character_rounding')
TOP=s.TOP;OUT=TOP/'step_16';PARENT=s.OUT/'hassler_native_upper.blend'
CENTER=np.array([0.,.04]);CHANGED=(s.BELT,s.BUCKLE,s.LOOPS)


def clearance():
    band=evaluated(bpy.data.objects[s.BELT]);cloth=[evaluated(bpy.data.objects[n]) for n in (s.LOWER,s.WAIST)]
    lo,hi=band['p'][:,2].min(),band['p'][:,2].max();gaps=[]
    for z in np.linspace(lo+.0002,hi-.0002,17):
        for a in np.linspace(0,2*math.pi,720,endpoint=False):
            origin=Vector((*CENTER,z));direction=Vector((math.sin(a),math.cos(a),0))
            hit=band['tree'].ray_cast(origin,direction,1.)
            assert hit[0] is not None,('Missing belt ray',z,a)
            radii=[q[3] for tree in cloth if (q:=tree['tree'].ray_cast(origin,direction,1.))[0] is not None]
            assert radii,('Missing waist ray',z,a)
            gaps.append(hit[3]-max(radii))
    return {'min_radial_clearance_m':float(min(gaps)),'max_radial_clearance_m':float(max(gaps)),'samples':len(gaps)}


def main():
    OUT.mkdir(exist_ok=True);digest=s.s13.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study']
    names=[o.name for o in edit.objects if o.type=='MESH']+['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged']
    before={n:snapshot(bpy.data.objects[n]) for n in names};bones=rig_snapshot();old=clearance()
    # Keep the strap thickness and height: move its complete section outward.
    # Round up to millimetres and leave 2 mm beyond the actual cloth envelope.
    offset=math.ceil((.002-old['min_radial_clearance_m'])*1000)/1000
    assert 0<offset<=.015,('Unexpected widening',offset,old)
    belt=bpy.data.objects[s.BELT]
    for v in belt.data.vertices:
        direction=np.array(v.co[:2])-CENTER;direction/=np.linalg.norm(direction)
        v.co.x+=float(direction[0]*offset);v.co.y+=float(direction[1]*offset)
    buckle=bpy.data.objects[s.BUCKLE]
    for v in buckle.data.vertices:v.co.y+=offset
    loops=bpy.data.objects[s.LOOPS];adj={i:set() for i in range(len(loops.data.vertices))}
    for e in loops.data.edges:
        a,b=e.vertices;adj[a].add(b);adj[b].add(a)
    pending=set(adj);components=[]
    while pending:
        todo=[next(iter(pending))];component=set()
        while todo:
            a=todo.pop()
            if a in component:continue
            component.add(a);todo.extend(adj[a]-component)
        pending-=component;components.append(sorted(component))
    assert len(components)==5
    for component in components:
        center=np.mean([loops.data.vertices[i].co[:2] for i in component],axis=0)
        direction=center-CENTER;direction/=np.linalg.norm(direction)
        for i in component:
            v=loops.data.vertices[i];v.co.x+=float(direction[0]*offset);v.co.y+=float(direction[1]*offset)
    for n in CHANGED:s.s9.recalc(bpy.data.objects[n])
    belt['construction']=f'STEP16: accepted STEP15 strap moved outward by {offset*1000:.1f} mm around the waist. Original height, Z, thickness, UV and skin weights preserved.'
    report={'step':'16 small radial belt widening to clear trousers','parent':str(PARENT),'parent_sha256':digest,'radial_offset_m':offset,'before':old,'changed_objects':list(CHANGED),'height_and_z_preserved':True,'buckle_and_keepers_moved_rigidly':True,'game_installed':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2));s.native.activate(belt)
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    for n,oldmesh in before.items():
        now=snapshot(bpy.data.objects[n])
        for k in ('faces','weights','materials','material_indices'):assert oldmesh[k]==now[k],(n,k)
        for k,v in oldmesh['uv_layers'].items():assert np.array_equal(v,now['uv_layers'][k]),(n,k)
        assert np.array_equal(oldmesh['world'],now['world'])
        if n not in CHANGED:
            assert np.array_equal(oldmesh['points'],now['points']) and np.array_equal(oldmesh['normals'],now['normals']),n
        else:
            assert np.array_equal(oldmesh['points'][:,2],now['points'][:,2]),('Belt height changed',n)
            bm=bmesh.new();bm.from_mesh(bpy.data.objects[n].data)
            assert all(e.is_manifold for e in bm.edges) and bm.calc_volume(signed=True)>0;bm.free()
    after=rig_snapshot();assert set(after)==set(bones)
    for n,(m,w,p) in after.items():assert np.array_equal(m,bones[n][0]) and w==bones[n][1] and p==bones[n][2]
    clear=clearance();assert clear['min_radial_clearance_m']>.0015,clear
    poses=[]
    for frame in (1,30,60,90,120):
        scene.frame_set(frame);band=evaluated(bpy.data.objects[s.BELT]);contacts={}
        for n in (s.LOWER,s.WAIST,s.s13.GARMENT):
            hits=band['tree'].overlap(evaluated(bpy.data.objects[n])['tree']);contacts[n]=len(hits)
            assert not hits,('Belt/cloth crossing',frame,n,hits[:5])
        poses.append({'frame':frame,'triangle_crossings':contacts})
    scene.frame_set(1)
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport
    result={'reopened':True,'checks_passed':True,'blend_sha256':s.s13.sha(path),'parent_sha256':digest,'unchanged_objects_exact':len(names)-3,'belt_topology_uv_skin_materials_height_preserved':True,'rig_exact':True,'after':clear,'poses':poses,'game_animations_validated':False,'game_installed':False}
    print('BELT16',json.dumps({'offset_mm':offset*1000,'before':old,'after':clear}),flush=True)
    if '--no-render' not in sys.argv:
        s.OUT=OUT
        for label,direction,target,scale in [('waist_front',(0,1,.08),(0,.02,1.15),.59),('waist_side',(1,0,.1),(0,.02,1.15),.59),('waist_back',(0,-1,.08),(0,.02,1.15),.59),('full_front',(0,1,.03),(0,0,.99),2.08)]:s.render(scene,label,direction,target,scale)
        result['previews_bound_to_blend_sha256']=result['blend_sha256']
    assert s.s13.sha(path)==result['blend_sha256'] and s.s13.sha(PARENT)==digest
    (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
