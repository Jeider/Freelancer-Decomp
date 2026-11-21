"""Reopen the fitted waist belt, verify retained upper and trouser attachment."""
import sys,json
from pathlib import Path
import bpy,bmesh,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step14 as s
from hassler_step13_check import snapshot
from hassler_step04_check import rig_snapshot
from hassler_step08_check import evaluated
from hassler_step03_check import topology
configure('character_rounding')

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s.PARENT));configure('character_rounding');bpy.context.scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];names=[o.name for o in edit.objects if o.type=='MESH' and o.name!=s.OLD]+['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged'];before={n:snapshot(bpy.data.objects[n]) for n in names};base=snapshot(bpy.data.objects[s.OLD]);bones=rig_snapshot()
    path=s.OUT/'hassler_native_upper.blend';digest=s.s13.sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);report=json.loads((s.OUT/'report.json').read_text(encoding='utf8'));assert s.s13.sha(s.PARENT)==report['parent_sha256']
    for name,old in before.items():
        now=snapshot(bpy.data.objects[name])
        for k in ('points','normals','world'):assert np.array_equal(old[k],now[k]),(name,k)
        for k in ('faces','weights','materials','material_indices'):assert old[k]==now[k],(name,k)
        for k,v in old['uv_layers'].items():assert np.array_equal(v,now['uv_layers'][k]),(name,k)
    b=bpy.data.objects[s.BASE];now=snapshot(b);assert np.array_equal(base['points'],now['points']) and base['weights']==now['weights']
    kept=report['retained_base_faces'];assert now['faces']==[base['faces'][i] for i in kept]
    offsets=np.r_[0,np.cumsum([len(f) for f in base['faces']])];loops=[j for i in kept for j in range(offsets[i],offsets[i+1])]
    for k,v in base['uv_layers'].items():assert np.array_equal(v[loops],now['uv_layers'][k])
    normal_error=float(np.max(np.linalg.norm(base['normals'][loops]-now['normals'],axis=1)));print('RETAINED_NORMAL_ERROR',normal_error,flush=True);assert normal_error<.0003
    after=rig_snapshot();assert set(after)==set(bones)
    for n,(m,w,p) in after.items():assert np.array_equal(m,bones[n][0]) and w==bones[n][1] and p==bones[n][2]
    parts={};new={};maxweights=0
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type!='MESH':continue
        data=evaluated(ob);parts[ob.name]={k:data[k] for k in ('vertices','triangles')}
        if ob.name not in (s.BELT,s.BUCKLE,s.LOOPS,s.WAIST):continue
        me=ob.data;me.calc_loop_triangles();uv=me.uv_layers[0];zero=0
        for t in me.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in t.loops];zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        for v in me.vertices:
            w=[g.weight for g in v.groups if g.weight>0];assert abs(sum(w)-1)<3e-6;maxweights=max(maxweights,len(w))
        assert zero==0,(ob.name,zero);assert np.isfinite(data['p']).all()
        t=topology(me);new[ob.name]={'uv_degenerate_triangles':int(zero),'components':len(t['connected_components']),'boundary_components':len(t['boundary_loops'])}
        if ob.name!=s.WAIST:
            assert not t['boundary_loops'] and t['nonmanifold_edges']==0
            bm=bmesh.new();bm.from_mesh(me);volume=bm.calc_volume(signed=True);bm.free();assert volume>0;new[ob.name]['signed_volume_m3']=volume
        else:
            # Every added strip must face outward with back-face culling.
            for f in me.polygons:
                radial=np.array([f.center.x,f.center.y-.04,0]);assert np.dot(f.normal,radial)>0,('Waist inward',f.index)
    assert maxweights<=4 and sum(d['vertices'] for d in parts.values())<65535
    poses=[]
    for frame in (1,30,60,120):
        scene.frame_set(frame);base=evaluated(bpy.data.objects[s.BASE]);waist=evaluated(bpy.data.objects[s.WAIST]);belt=evaluated(bpy.data.objects[s.BELT]);coat=evaluated(bpy.data.objects[s.s13.GARMENT])
        gap=max(float(np.linalg.norm(waist['p'][a]-base['p'][b])) for a,b in report['waist_closure']['bottom_attachments']);assert gap<2e-6
        contacts=belt['tree'].overlap(coat['tree']);original=bpy.data.objects[s.s13.GARMENT].data
        bad=[(i,j) for i,j in contacts if max(original.vertices[k%len(original.vertices)].co.z for k in coat['faces'][j])>.24];assert not bad,('belt above hem',frame,bad[:5])
        selfhits=[(i,j) for i,j in belt['tree'].overlap(belt['tree']) if i<j and not set(belt['faces'][i])&set(belt['faces'][j])];assert not selfhits,('belt self',frame,selfhits[:5])
        poses.append({'frame':frame,'native_trouser_seam_error_m':gap,'belt_coat_hem_seating_contacts':len(contacts),'belt_self_intersections':0})
    scene.frame_set(1)
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_viewport and col.hide_render
    for t in report['textures']:assert s.s13.sha(Path(t['path']))==t['sha256']
    result={'reopened':True,'blend_sha256':digest,'parent_sha256':report['parent_sha256'],'upper_head_hands_neck_materials_uv_rig_exact':True,'retained_native_trousers_exact':True,'old_pouch_belt_faces_removed':len(report['removed_old_belt_faces']),'max_skin_influences':maxweights,'new_parts':new,'poses':poses,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'checks_passed':True,'game_installed':False,'game_animations_validated':False}
    result['retained_trouser_normal_encoding_max_delta']=normal_error
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('waist_front',(0,1,.08),(0,.02,1.15),.59),('waist_side',(1,0,.1),(0,.02,1.15),.59),('waist_back',(0,-1,.08),(0,.02,1.15),.59),('back',(0,-1,.03),(0,0,1.47),1.02)]:s.render(scene,label,direction,target,scale)
        scene.frame_set(120);s.render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1);result['previews_bound_to_blend_sha256']=digest
    assert s.s13.sha(path)==digest
    (s.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('CHECK14',json.dumps({k:result[k] for k in ('blend_sha256','checks_passed','body_triangles_with_modifiers')}),flush=True)

if __name__=='__main__':main()
