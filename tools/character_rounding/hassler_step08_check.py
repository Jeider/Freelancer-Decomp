"""Reopened upper finish: native neck seam, shoulder and cord pose clearance."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step08 import TOP,OUT,PARENT,GARMENT,LINING,SHIRT,EPAULETTES,render
from hassler_native_step07 import GARMENT as OLD_GARMENT
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluated(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
    p=np.array([v.co[:] for v in me.vertices]);f=[list(t.vertices) for t in me.loop_triangles]
    result={'p':p,'faces':f,'material_indices':[t.material_index for t in me.loop_triangles],
            'tree':BVHTree.FromPolygons(p.tolist(),f,all_triangles=True),'triangles':len(f),'vertices':len(p)}
    ev.to_mesh_clear();return result

def neck_error(head,shirt,report):
    native=bpy.data.objects['Hassler head — native unchanged'];points=np.array([v.co[:] for v in native.data.vertices]);ring=report['neck']['native_boundary']
    ids=[int(np.argmin(np.linalg.norm(points-q,axis=1))) for q in ring];poly=head['p'][ids];errors=[]
    for i,q in report['neck']['hem_vertices']:
        p=shirt['p'][i];dd=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            d=b-a;t=np.clip(np.dot(p-a,d)/np.dot(d,d),0,1);dd.append(np.linalg.norm(p-(a+t*d)))
        errors.append(min(dd))
    return float(max(errors))

def pose_audit(scene,report,label):
    edit=bpy.data.collections['EDIT — native costume upper study'];obs={o.name:evaluated(o) for o in edit.objects if o.type=='MESH'}
    head=evaluated(bpy.data.objects['Hassler head — native unchanged']);coat=obs[GARMENT];ep=obs[EPAULETTES];shirt=obs[SHIRT]
    pad=next(d for n,d in obs.items() if n.startswith('16 '));pad_ep=pad['tree'].overlap(ep['tree'])
    cords=[r['name'] for r in report['cords']];contacts={}
    for n in cords:
        cc=obs[n]['tree'].overlap(coat['tree']);ce=obs[n]['tree'].overlap(ep['tree'])
        contacts[n]={'coat_triangle_crossings':len(cc),'epaulette_triangle_crossings':len(ce),
                     'coat_crossing_rings':sorted({v//8 for i,j in cc for v in obs[n]['faces'][i]}),
                     'epaulette_crossing_rings':sorted({v//8 for i,j in ce for v in obs[n]['faces'][i]})}
    between={}
    for i,a in enumerate(cords):
        for b in cords[i+1:]:between[a+' / '+b]=len(obs[a]['tree'].overlap(obs[b]['tree']))
    pair=ep['tree'].overlap(coat['tree']);box=[]
    for i,j in pair:
        box.append(np.mean(ep['p'][ep['faces'][i]],axis=0))
    hp=head['tree'].overlap(coat['tree'])
    result={'pose':label,'neck_seam_max_error_m':neck_error(head,shirt,report),'cord_contacts':contacts,'cord_to_cord_crossings':between,
            'epaulette_coat_triangle_crossings':len(pair),'epaulette_crossing_centers':np.array(box).tolist(),
            'head_coat_triangle_crossings':len(hp),
            'pad_gold_triangle_crossings':len(pad_ep),
            'pad_visible_gold_triangle_crossings':sum(ep['material_indices'][j]==0 for i,j in pad_ep),
            'head_coat_crossing_centers':[np.mean(coat['p'][coat['faces'][j]],axis=0).tolist() for i,j in hp]}
    return result

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged','00 Native lower body and belt']
    previous={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot();old=mesh(bpy.data.objects[OLD_GARMENT]);old_ep=next(o for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith('14 '))
    ep_uv=mesh(old_ep)['uv'];ep_mats=[m.name for m in old_ep.data.materials]
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    report=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==report['parent_sha256']
    for n in keep:
        now=mesh(bpy.data.objects[n])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[n][k]),(n,k)
        for k in ('faces','weights'):assert now[k]==previous[n][k],(n,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    coat=bpy.data.objects[GARMENT];data=mesh(coat);changed=set(report['cloth']['changed_coat_vertices']);unchanged=sorted(set(range(len(data['points'])))-changed)
    assert data['faces']==old['faces'] and data['weights']==old['weights'] and np.array_equal(data['uv'],old['uv'])
    assert np.array_equal(data['points'][unchanged],old['points'][unchanged])
    flap=report['inherited_opening'];fv={v for fi in flap['faces'] for v in data['faces'][fi]};assert not fv&changed
    topo=topology(coat.data);assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0
    ep=bpy.data.objects[EPAULETTES];assert np.array_equal(mesh(ep)['uv'],ep_uv) and [m.name for m in ep.data.materials]==ep_mats
    shirt=bpy.data.objects[SHIRT];used={v for f in shirt.data.polygons for v in f.vertices};assert max(shirt.data.vertices[i].co.z for i in used)<.574
    scene=bpy.context.scene;scene.frame_set(1);parts={};uvzero={};influences=0
    for o in bpy.data.collections['EDIT — native costume upper study'].objects:
        if o.type!='MESH':continue
        for v in o.data.vertices:
            w=[g.weight for g in v.groups if g.weight>0];assert abs(sum(w)-1)<3e-6,(o.name,v.index,sum(w));influences=max(influences,len(w))
        o.data.calc_loop_triangles();uv=o.data.uv_layers.active;zero=0
        for t in o.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in t.loops];zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[o.name]=int(zero);d=evaluated(o);assert np.isfinite(d['p']).all();parts[o.name]={k:d[k] for k in ('vertices','triangles')}
    assert influences<=4 and sum(p['vertices'] for p in parts.values())<65535
    print('UV',uvzero,flush=True);assert not any(uvzero.values()),uvzero
    audits=[]
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:
        scene.frame_set(frame);audit=pose_audit(scene,report,label);audits.append(audit)
        print('POSE',label,'board/coat',audit['epaulette_coat_triangle_crossings'],'head/coat',audit['head_coat_triangle_crossings'],
              'cord/coat',[c['coat_triangle_crossings'] for c in audit['cord_contacts'].values()],
              'cord/cord',list(audit['cord_to_cord_crossings'].values()),'pad/gold',audit['pad_visible_gold_triangle_crossings'],'pad/inner',audit['pad_gold_triangle_crossings'],flush=True)
    scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];bone=rig.pose.bones['Body_Head'];old_mode=bone.rotation_mode;old_basis=bone.matrix_basis.copy();bone.rotation_mode='QUATERNION'
    action=rig.animation_data.action;rig.animation_data.action=None
    for label,axis,angle in [('head_turn_left',(0,0,1),.65),('head_turn_right',(0,0,1),-.65),('head_nod',(1,0,0),-.35),('head_look_up',(1,0,0),.28),('head_tilt',(0,1,0),.28)]:
        local=rig.data.bones['Body_Head'].matrix_local.to_3x3().inverted()@Vector(axis)
        bone.rotation_quaternion=Quaternion(local,angle);bpy.context.view_layer.update();audit=pose_audit(scene,report,label);audits.append(audit)
        audit['authored_rotation_axis_armature_space']=axis;audit['authored_rotation_radians']=angle
        print('NECK',label,audit['neck_seam_max_error_m'],'crossings',audit['head_coat_triangle_crossings'],audit['head_coat_crossing_centers'][:6],flush=True)
        if '--no-render' not in sys.argv and label in ('head_nod','head_turn_right'):
            before=np.array(bone.matrix);render(scene,label,(.35,1,.14),(0,.01,1.55),.60)
            assert np.max(abs(np.array(bone.matrix)-before))<2e-6,'Render reset the authored head pose'
    bone.rotation_mode=old_mode;bone.matrix_basis=old_basis;rig.animation_data.action=action;scene.frame_set(1);bpy.context.view_layer.update()
    for audit in audits:
        assert audit['neck_seam_max_error_m']<2e-6,audit['pose']
        assert audit['epaulette_coat_triangle_crossings']==0,audit['pose']
        assert audit['head_coat_triangle_crossings']==0,audit['pose']
        assert audit['pad_visible_gold_triangle_crossings']==0,audit['pose']
        assert not any(audit['cord_to_cord_crossings'].values()),audit['pose']
        for name,contact in audit['cord_contacts'].items():
            assert contact['coat_triangle_crossings']==0,(audit['pose'],name)
            # A cord terminates inside its sewn attachment underneath the
            # board; contact is limited to these first four hidden rings.
            assert all(i<4 for i in contact['epaulette_crossing_rings']),(audit['pose'],name,contact)
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    result={'reopened':True,'blend_sha256':sha(path),'parent_step07_unchanged':True,'native_head_neck_hands_lower_body_rig_unchanged':True,
            'accepted_hanging_flap_unchanged':True,'main_garment_topology':topo,'coat_uv_faces_weights_unchanged':True,'coat_unchanged_vertices':len(unchanged),
            'epaulette_native_uv_and_materials_retained':True,'high_black_neck_band_removed':True,'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,
            'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'pose_audits':audits,
            'clearance_checks_passed':True,'buried_cord_attachment_contact_only':True,
            'game_installed':False,'game_animations_validated':False}
    if '--no-render' not in sys.argv and '--head-only' not in sys.argv:
        for label,direction,target,scale in [
            ('collar_close',(.35,1,.18),(0,.02,1.53),.64),
            ('shoulder_detail',(1,.65,.35),(.16,0,1.50),.44),
            ('cord_detail',(-.7,1,.12),(-.12,.08,1.43),.48),
            ('shoulders_above',(0,1,.8),(0,.01,1.50),.72),
            ('back',(0,-1,.03),(0,0,1.47),1.02),('side',(1,0,.02),(0,0,1.47),1.02)]:render(scene,label,direction,target,scale)
        scene.frame_set(30);render(scene,'elbow_pose',(.65,1,.12))
        scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12))
        scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    if '--no-render' not in sys.argv:result['previews_bound_to_blend_sha256']=sha(path)
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('RESULT',json.dumps({'blend_sha256':result['blend_sha256'],'triangles':result['body_triangles_with_modifiers'],'neck_seam_max':max(a['neck_seam_max_error_m'] for a in audits)}),flush=True)

if __name__=='__main__':main()
