"""Reopen step10: shell closure, padding enclosure, collar layers and native rig."""
import sys,json,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step10 as s10
import hassler_step08_check as c8
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding')
for k in ('GARMENT','EPAULETTES','SHIRT','LINING'):setattr(c8,k,getattr(s10,k))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def pose_audit(scene,report,label):
    result=c8.pose_audit(scene,report,label)
    gold=c8.evaluated(bpy.data.objects[s10.EPAULETTES]);pad=c8.evaluated(bpy.data.objects[s10.PAD]);coat=c8.evaluated(bpy.data.objects[s10.GARMENT]);red=c8.evaluated(bpy.data.objects[s10.LINING])
    pairs=gold['tree'].overlap(coat['tree']);signed=[]
    for p in pad['p']:
        hit,no,i,dist=gold['tree'].find_nearest(Vector(p));signed.append(float((Vector(p)-hit).dot(no)))
    result['padding_signed_distance_range_m']=[min(signed),max(signed)];result['padding_outside_vertices']=sum(d>1e-6 for d in signed)
    result['gold_collar_crossings']=sum(coat['material_indices'][j] in (4,15) for i,j in pairs)
    result['gold_cloth_seating_contacts']=sum(coat['material_indices'][j] not in (4,15) for i,j in pairs)
    result['gold_red_lining_seating_contacts']=len(gold['tree'].overlap(red['tree']))
    n=len(bpy.data.objects[s10.GARMENT].data.vertices);self_cross=[]
    for i,j in coat['tree'].overlap(coat['tree']):
        if i>=j or coat['material_indices'][i]!=4 or coat['material_indices'][j]!=4:continue
        if {v%n for v in coat['faces'][i]} & {v%n for v in coat['faces'][j]}:continue
        self_cross.append([i,j])
    result['nonadjacent_collar_self_crossings']=self_cross
    result['gold_self_crossings']=[[i,j] for i,j in gold['tree'].overlap(gold['tree']) if i<j and not set(gold['faces'][i])&set(gold['faces'][j])]
    result.pop('epaulette_crossing_centers',None)
    print('POSE',label,'padding outside',result['padding_outside_vertices'],'gold/pad',result['pad_gold_triangle_crossings'],'gold/collar',result['gold_collar_crossings'],'head',result['head_coat_triangle_crossings'],'collar self',len(self_cross),'gold self',len(result['gold_self_crossings']),flush=True)
    return result

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s10.PARENT));configure('character_rounding');edit=bpy.data.collections['EDIT — native costume upper study']
    keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged','00 Native lower body and belt',s10.SHIRT,s10.LINING]+[o.name for o in edit.objects if o.name.startswith('13.')]
    previous={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot();old=mesh(next(o for o in edit.objects if o.name.startswith('10 ')))
    path=s10.OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');report=json.loads((s10.OUT/'report.json').read_text(encoding='utf8'));assert sha(s10.PARENT)==report['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[name][k]),(name,k)
        for k in ('faces','weights'):assert now[k]==previous[name][k],(name,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    coat=bpy.data.objects[s10.GARMENT];data=mesh(coat);changed=set(report['collar']['changed_vertices']);unchanged=sorted(set(range(len(data['points'])))-changed)
    assert data['faces']==old['faces'] and data['weights']==old['weights'] and np.array_equal(data['uv'],old['uv']);assert np.array_equal(data['points'][unchanged],old['points'][unchanged])
    assert not changed&set(report['collar']['hinge_vertices_unchanged'])
    flap=report['inherited_opening'];fv={v for fi in flap['faces'] for v in data['faces'][fi]};assert not fv&changed
    topo=topology(coat.data);assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0
    shells={}
    for n in (s10.EPAULETTES,s10.PAD):
        ob=bpy.data.objects[n];t=topology(ob.data);assert len(t['connected_components'])==2 and not t['boundary_loops'] and t['nonmanifold_edges']==0
        bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free();assert volume>0
        shells[n]={'topology':t,'signed_volume_m3':volume}
    gold=mesh(bpy.data.objects[s10.EPAULETTES]);pad=mesh(bpy.data.objects[s10.PAD]);assert gold['faces']==pad['faces'] and gold['weights']==pad['weights']
    parts={};uvzero={};influences=0;scene=bpy.context.scene;scene.frame_set(1)
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            w=[g.weight for g in v.groups if g.weight>0];assert abs(sum(w)-1)<3e-6,(ob.name,v.index,sum(w));influences=max(influences,len(w))
        ob.data.calc_loop_triangles();uv=ob.data.uv_layers.active;zero=0
        for t in ob.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in t.loops];zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[ob.name]=int(zero);d=c8.evaluated(ob);assert np.isfinite(d['p']).all();parts[ob.name]={k:d[k] for k in ('vertices','triangles')}
        for mat in ob.data.materials:
            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type=='UVMAP':assert node.uv_map in ob.data.uv_layers,(ob.name,mat.name,node.uv_map)
    print('UV',uvzero,flush=True);assert not any(uvzero.values());assert influences<=4 and sum(p['vertices'] for p in parts.values())<65535
    audits=[]
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:scene.frame_set(frame);audits.append(pose_audit(scene,report,label))
    scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];bone=rig.pose.bones['Body_Head'];mode=bone.rotation_mode;basis=bone.matrix_basis.copy();action=rig.animation_data.action;rig.animation_data.action=None;bone.rotation_mode='QUATERNION'
    for label,axis,angle in [('head_turn_left',(0,0,1),.65),('head_turn_right',(0,0,1),-.65),('head_nod',(1,0,0),-.35),('head_look_up',(1,0,0),.28),('head_tilt',(0,1,0),.28)]:
        local=rig.data.bones['Body_Head'].matrix_local.to_3x3().inverted()@Vector(axis);bone.rotation_quaternion=Quaternion(local,angle);bpy.context.view_layer.update();r=pose_audit(scene,report,label);r['axis']=axis;r['angle_radians']=angle;audits.append(r)
        if '--render' in sys.argv and label in ('head_nod','head_turn_right'):
            before=np.array(bone.matrix);s10.render(scene,label,(.35,1,.14),(0,.01,1.55),.60);assert np.max(abs(np.array(bone.matrix)-before))<2e-6
    bone.rotation_mode=mode;bone.matrix_basis=basis;rig.animation_data.action=action;scene.frame_set(1);bpy.context.view_layer.update()
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    clean=all(a['neck_seam_max_error_m']<2e-6 and a['padding_outside_vertices']==0 and a['pad_gold_triangle_crossings']==0 and a['gold_collar_crossings']==0 and a['head_coat_triangle_crossings']==0 and not a['nonadjacent_collar_self_crossings'] and not a['gold_self_crossings'] and not any(a['cord_to_cord_crossings'].values()) and all(c['coat_triangle_crossings']==0 and all(i<7 for i in c['epaulette_crossing_rings']) for c in a['cord_contacts'].values()) for a in audits)
    result={'reopened':True,'blend_sha256':sha(path),'parent_step09_unchanged':True,'native_head_neck_hands_lower_body_rig_shirt_red_lining_cords_unchanged':True,'accepted_hanging_flap_unchanged':True,'coat_uv_faces_weights_unchanged':True,'main_garment_topology':topo,'closed_shoulders':shells,'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'pose_audits':audits,'layer_checks_passed':clean,'seating_contacts_retained':'Closed underside and inner ends meet the existing coat/red lining. They are reported separately from collar and padding layer intersections. Cords emerge through the attachment area within rings 0..6.','game_installed':False,'game_animations_validated':False}
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43),('right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43),('collar_close',(.35,1,.18),(0,.02,1.53),.64),('shoulders_above',(0,1,.8),(0,.01,1.50),.72),('back',(0,-1,.03),(0,0,1.47),1.02),('side',(1,0,.03),(0,0,1.47),1.02)]:s10.render(scene,label,direction,target,scale)
        scene.frame_set(60);s10.render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(120);s10.render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1);result['previews_bound_to_blend_sha256']=sha(path)
    (s10.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('RESULT',json.dumps({k:result[k] for k in ('blend_sha256','layer_checks_passed','body_triangles_with_modifiers')}),flush=True)
    if '--strict' in sys.argv:assert clean,'Layer checks failed; inspect validation.json'

if __name__=='__main__':main()
