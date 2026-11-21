"""Reopen the tailored shoulder prototype and verify geometry and posed layers."""
import sys,json,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step12 as s12
import hassler_step11_check as c11
import hassler_step08_check as c8
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding');c11.s11=s12
BASELINE={}
for k in ('GARMENT','EPAULETTES','SHIRT','LINING'):setattr(c8,k,getattr(s12,k))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def sleeve_pairs(coat,moved,n):
    return {(i,j) for i,j in coat['tree'].overlap(coat['tree']) if i<j and coat['material_indices'][i]==coat['material_indices'][j]==0 and (set(coat['faces'][i])|set(coat['faces'][j]))&moved and not {v%n for v in coat['faces'][i]}&{v%n for v in coat['faces'][j]}}

def audit(scene,report,label):
    result=c11.pose_audit(scene,report,label);coat=c8.evaluated(bpy.data.objects[s12.GARMENT]);n=len(bpy.data.objects[s12.GARMENT].data.vertices)
    result['collar_self_crossings']=[[i,j] for i,j in coat['tree'].overlap(coat['tree']) if i<j and coat['material_indices'][i] in (4,15) and coat['material_indices'][j] in (4,15) and not {v%n for v in coat['faces'][i]}&{v%n for v in coat['faces'][j]}]
    moved=set(report['tailoring']['sleeve_vertices'])
    current=sleeve_pairs(coat,moved,n);baseline=BASELINE.get(label,BASELINE['rest'])
    result['sleeve_self_crossings']=[list(p) for p in sorted(current)];result['inherited_sleeve_contact_count']=len(current&baseline);result['new_sleeve_self_crossings']=[list(p) for p in sorted(current-baseline)]
    trim=c8.evaluated(bpy.data.objects[s12.TRIM]);gold=c8.evaluated(bpy.data.objects[s12.EPAULETTES])
    result['red_edge_gold_crossings']=len(trim['tree'].overlap(gold['tree']))
    print('COLLAR',label,'self',len(result['collar_self_crossings']),'red/gold',result['red_edge_gold_crossings'],'new sleeve',len(result['new_sleeve_self_crossings']),'inherited',result['inherited_sleeve_contact_count'],flush=True)
    return result

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s12.PARENT));configure('character_rounding');edit=bpy.data.collections['EDIT — native costume upper study']
    keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged','00 Native lower body and belt',s12.SHIRT,s12.LINING,s12.EPAULETTES]+[o.name for o in edit.objects if o.name.startswith('13.')]
    old={n:mesh(bpy.data.objects[n]) for n in keep};oldcoat=mesh(next(o for o in edit.objects if o.name.startswith('10 ')));bones=rig_snapshot()
    report=json.loads((s12.OUT/'report.json').read_text(encoding='utf8'));moved=set(report['tailoring']['sleeve_vertices']);parentcoat=next(o for o in edit.objects if o.name.startswith('10 '))
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:bpy.context.scene.frame_set(frame);BASELINE[label]=sleeve_pairs(c8.evaluated(parentcoat),moved,len(parentcoat.data.vertices))
    path=s12.OUT/'hassler_native_upper.blend';digest=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    report=json.loads((s12.OUT/'report.json').read_text(encoding='utf8'));assert sha(s12.PARENT)==report['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for key in ('points','uv'):assert np.array_equal(now[key],old[name][key]),(name,key)
        for key in ('faces','weights'):assert now[key]==old[name][key],(name,key)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    coat=bpy.data.objects[s12.GARMENT];data=mesh(coat);changed=set(report['tailoring']['changed_vertices']);unchanged=sorted(set(range(len(data['points'])))-changed)
    assert np.array_equal(data['points'][unchanged],oldcoat['points'][unchanged]);assert np.array_equal(data['uv'],oldcoat['uv'])
    for k in ('faces','weights'):assert data[k]==oldcoat[k]
    flap={v for f in report['inherited_opening']['faces'] for v in data['faces'][f]};assert not changed&flap;assert not changed&set(report['tailoring']['hinge_vertices'])
    assert all(coat.data.polygons[i].material_index==4 for i in report['tailoring']['collar_faces'])
    assert all(coat.data.materials[i]==coat.data.materials[4] for i in (15,22,33))
    parts={};uvzero={};influences=0;tops={}
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            w=[g.weight for g in v.groups if g.weight>0];assert abs(sum(w)-1)<3e-6;influences=max(influences,len(w))
        ob.data.calc_loop_triangles();uv=ob.data.uv_layers.active;zero=0
        for tri in ob.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in tri.loops];zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[ob.name]=int(zero);d=c8.evaluated(ob);assert np.isfinite(d['p']).all();parts[ob.name]={k:d[k] for k in ('vertices','triangles')}
        for mat in ob.data.materials:
            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type=='UVMAP':assert node.uv_map in ob.data.uv_layers
        if ob.name in (s12.PAD,s12.EPAULETTES):
            t=topology(ob.data);bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
            assert len(t['connected_components'])==2 and not t['boundary_loops'] and t['nonmanifold_edges']==0 and volume>0
            p=np.array([v.co[:] for v in ob.data.vertices]);a=p[p[:,0]>0];b=p[p[:,0]<0].copy();b[:,0]*=-1
            from mathutils.kdtree import KDTree
            tree=KDTree(len(b))
            for i,v in enumerate(b):tree.insert(v,i)
            tree.balance();err=max(tree.find(v)[2] for v in a);assert err<3e-6,(ob.name,err)
            tops[ob.name]={'closed_components':2,'signed_volume_m3':volume,'mirror_error_m':err}
    print('UV',uvzero,flush=True);assert influences<=4 and sum(d['vertices'] for d in parts.values())<65535
    audits=[]
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:scene.frame_set(frame);audits.append(audit(scene,report,label))
    scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];bone=rig.pose.bones['Body_Head'];mode=bone.rotation_mode;basis=bone.matrix_basis.copy();action=rig.animation_data.action;rig.animation_data.action=None;bone.rotation_mode='QUATERNION'
    for label,axis,angle in [('head_turn_left',(0,0,1),.65),('head_turn_right',(0,0,1),-.65),('head_nod',(1,0,0),-.35),('head_look_up',(1,0,0),.28),('head_tilt',(0,1,0),.28)]:
        local=rig.data.bones['Body_Head'].matrix_local.to_3x3().inverted()@Vector(axis);bone.rotation_quaternion=Quaternion(local,angle);bpy.context.view_layer.update();audits.append(audit(scene,report,label))
    bone.rotation_mode=mode;bone.matrix_basis=basis;rig.animation_data.action=action;scene.frame_set(1);bpy.context.view_layer.update()
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport
    clean=not any(uvzero.values()) and all(a['neck_seam_max_error_m']<2e-6 and a['pad_gold_triangle_crossings']==0 and a['gold_collar_crossings']==0 and a['pad_collar_crossings']==0 and a['head_coat_triangle_crossings']==0 and not a['gold_self_crossings'] and not a['pad_self_crossings'] and not a['gold_join_collar']['free_contacts'] and not a['gold_join_epaulette']['free_contacts'] and a['gold_join_pad_crossings']==0 and a['gold_join_head_crossings']==0 and not a['gold_join_self_crossings'] and not a['collar_self_crossings'] and a['red_edge_gold_crossings']==0 and not any(a['cord_to_cord_crossings'].values()) and all(c['coat_triangle_crossings']==0 and all(i<7 for i in c['epaulette_crossing_rings']) for c in a['cord_contacts'].values()) for a in audits)
    result={'reopened':True,'blend_sha256':digest,'parent_step11_unchanged':True,'native_head_hands_neck_rig_lower_body_shirt_red_lining_epaulettes_cords_unchanged':True,'accepted_flap_unchanged':True,'collar_all_sides_grey':True,'coat_original_uv_faces_weights_unchanged':True,'closed_shoulders':tops,'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'pose_audits':audits,'layer_checks_passed':clean,'game_installed':False,'game_animations_validated':False}
    result['layer_checks_passed']=clean=clean and not any(a['new_sleeve_self_crossings'] for a in audits)
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43),('shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43),('shoulders_above',(0,1,.8),(0,.01,1.50),.72),('back',(0,-1,.03),(0,0,1.47),1.02),('side',(1,0,.03),(0,0,1.47),1.02)]:s12.render(scene,label,direction,target,scale)
        scene.frame_set(60);s12.render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(120);s12.render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1);result['previews_bound_to_blend_sha256']=digest
    assert sha(path)==digest
    (s12.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('RESULT',json.dumps({k:result[k] for k in ('blend_sha256','layer_checks_passed','body_triangles_with_modifiers')}),flush=True)
    if '--strict' in sys.argv:assert clean,'Layer checks failed; inspect validation.json'

if __name__=='__main__':main()
