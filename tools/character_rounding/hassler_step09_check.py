"""Reopen the drawn-shoulder prototype; check preservation, UV, rig and poses."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step09 as s9
import hassler_step08_check as c8
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding')
for key in ('GARMENT','LINING','SHIRT','EPAULETTES'):setattr(c8,key,getattr(s9,key))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s9.PARENT));configure('character_rounding')
    edit=bpy.data.collections['EDIT — native costume upper study'];keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged','00 Native lower body and belt',s9.SHIRT]+[o.name for o in edit.objects if o.name.startswith('13.')]
    previous={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot();old=mesh(next(o for o in edit.objects if o.name.startswith('10 ')))
    path=s9.OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');report=json.loads((s9.OUT/'report.json').read_text(encoding='utf8'));assert sha(s9.PARENT)==report['parent_sha256']
    for n in keep:
        now=mesh(bpy.data.objects[n])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[n][k]),(n,k)
        for k in ('faces','weights'):assert now[k]==previous[n][k],(n,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    coat=bpy.data.objects[s9.GARMENT];data=mesh(coat);changed=set(report['collar']['changed_vertices']);unchanged=sorted(set(range(len(data['points'])))-changed)
    assert data['faces']==old['faces'] and data['weights']==old['weights'] and np.array_equal(data['uv'],old['uv']);assert np.array_equal(data['points'][unchanged],old['points'][unchanged])
    flap=report['inherited_opening'];fv={v for fi in flap['faces'] for v in data['faces'][fi]};assert not fv&changed
    topo=topology(coat.data);assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0
    red=bpy.data.objects[s9.LINING];assert max(v.co.z-s9.blue_z(v.co.x) for v in red.data.vertices)<1e-6
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
    def audit(label):
        result=c8.pose_audit(scene,report,label);audits.append(result)
        # Ignore neighbours of the same source vertex, including its Solidify
        # counterpart. Test the actual grey collar surface for unrelated folds.
        d=c8.evaluated(coat);n=len(coat.data.vertices);cross=[]
        for i,j in d['tree'].overlap(d['tree']):
            if i>=j or d['material_indices'][i]!=4 or d['material_indices'][j]!=4:continue
            if {v%n for v in d['faces'][i]} & {v%n for v in d['faces'][j]}:continue
            cross.append([i,j])
        result['nonadjacent_grey_collar_self_crossings']=len(cross)
        print('POSE',label,'ep/coat',result['epaulette_coat_triangle_crossings'],'pad/gold',result['pad_visible_gold_triangle_crossings'],'head/coat',result['head_coat_triangle_crossings'],'cord/coat',[c['coat_triangle_crossings'] for c in result['cord_contacts'].values()],'cord/ep',[c['epaulette_crossing_rings'] for c in result['cord_contacts'].values()],flush=True)
        return result
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:scene.frame_set(frame);audit(label)
    scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];bone=rig.pose.bones['Body_Head'];mode=bone.rotation_mode;basis=bone.matrix_basis.copy();action=rig.animation_data.action;rig.animation_data.action=None;bone.rotation_mode='QUATERNION'
    for label,axis,angle in [('head_turn_left',(0,0,1),.65),('head_turn_right',(0,0,1),-.65),('head_nod',(1,0,0),-.35),('head_look_up',(1,0,0),.28),('head_tilt',(0,1,0),.28)]:
        local=rig.data.bones['Body_Head'].matrix_local.to_3x3().inverted()@Vector(axis);bone.rotation_quaternion=Quaternion(local,angle);bpy.context.view_layer.update();r=audit(label);r['axis']=axis;r['angle_radians']=angle
        if '--render' in sys.argv and label in ('head_nod','head_turn_right'):
            before=np.array(bone.matrix);s9.render(scene,label,(.35,1,.14),(0,.01,1.55),.60);assert np.max(abs(np.array(bone.matrix)-before))<2e-6
    bone.rotation_mode=mode;bone.matrix_basis=basis;rig.animation_data.action=action;scene.frame_set(1);bpy.context.view_layer.update()
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    clean=all(a['neck_seam_max_error_m']<2e-6 and a['epaulette_coat_triangle_crossings']==0 and a['head_coat_triangle_crossings']==0 and a['pad_visible_gold_triangle_crossings']==0 and a['nonadjacent_grey_collar_self_crossings']==0 and not any(a['cord_to_cord_crossings'].values()) and all(c['coat_triangle_crossings']==0 and all(i<4 for i in c['epaulette_crossing_rings']) for c in a['cord_contacts'].values()) for a in audits)
    result={'reopened':True,'blend_sha256':sha(path),'parent_step08_unchanged':True,'native_head_neck_hands_lower_body_rig_shirt_cords_unchanged':True,'accepted_hanging_flap_unchanged':True,'coat_uv_faces_weights_unchanged':True,'main_garment_topology':topo,'red_geometry_below_drawn_boundary':True,'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'pose_audits':audits,'clearance_checks_passed':clean,'game_installed':False,'game_animations_validated':False}
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43),('right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43),('collar_close',(.35,1,.18),(0,.02,1.53),.64),('shoulders_above',(0,1,.8),(0,.01,1.50),.72),('back',(0,-1,.03),(0,0,1.47),1.02)]:s9.render(scene,label,direction,target,scale)
        scene.frame_set(60);s9.render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(120);s9.render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1);result['previews_bound_to_blend_sha256']=sha(path)
    (s9.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('RESULT',json.dumps({k:result[k] for k in ('blend_sha256','clearance_checks_passed','body_triangles_with_modifiers')}),flush=True)
    if '--strict' in sys.argv:assert clean,'Clearance checks failed; inspect validation.json'

if __name__=='__main__':main()
