"""Reopen step11 and check native preservation, closed hems and posed layers."""
import sys,json,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Quaternion
from mathutils.geometry import intersect_ray_tri
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step11 as s11
import hassler_step08_check as c8
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding')
for k in ('GARMENT','EPAULETTES','SHIRT','LINING'):setattr(c8,k,getattr(s11,k))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def segment_distance(p,a,b):
    d=b-a;t=np.clip(np.dot(p-a,d)/max(np.dot(d,d),1e-20),0,1);return np.linalg.norm(p-a-t*d)

def intersections(a,b):
    hits=[]
    for aa,bb in ((a,b),(b,a)):
        for p,q in zip(aa,np.roll(aa,-1,axis=0)):
            d=q-p;length=np.linalg.norm(d)
            if length<1e-12:continue
            hit=intersect_ray_tri(*[Vector(v) for v in bb],Vector(d/length),Vector(p),True)
            if hit is not None and (hit-Vector(p)).length<=length+1e-6:hits.append(np.array(hit))
    return hits

def seam_contacts(a,b,segments,material_filter=None):
    seam=0;free=[];maximum=0.
    for i,j in a['tree'].overlap(b['tree']):
        if material_filter is not None and b['material_indices'][j] not in material_filter:continue
        aa=a['p'][a['faces'][i]];bb=b['p'][b['faces'][j]];hits=intersections(aa,bb)
        if not hits:hits=[p for p in aa if min(segment_distance(p,x,y) for x,y in segments)<.0015]
        if not hits:free.append([i,j,'no resolved seam intersection']);continue
        distance=max(min(segment_distance(p,x,y) for x,y in segments) for p in hits);maximum=max(maximum,float(distance))
        if distance>.003:free.append([i,j,float(distance)])
        else:seam+=1
    return {'seam_contacts':seam,'free_contacts':free,'max_distance_from_seam_m':maximum}

def pose_audit(scene,report,label):
    result=c8.pose_audit(scene,report,label);gold=c8.evaluated(bpy.data.objects[s11.EPAULETTES]);pad=c8.evaluated(bpy.data.objects[s11.PAD]);coat=c8.evaluated(bpy.data.objects[s11.GARMENT])
    cf=set(report['collar_lining']['faces']);pairs=gold['tree'].overlap(coat['tree']);cols=(4,15,22,33)
    result['gold_collar_crossings']=sum(coat['material_indices'][j] in cols for i,j in pairs)
    result['gold_collar_centers']=[np.mean(gold['p'][gold['faces'][i]],axis=0).tolist() for i,j in pairs if coat['material_indices'][j] in cols]
    result['pad_collar_crossings']=sum(coat['material_indices'][j] in cols for i,j in pad['tree'].overlap(coat['tree']))
    result['gold_other_cloth_seating_contacts']=sum(coat['material_indices'][j] not in cols for i,j in pairs)
    result['gold_self_crossings']=[[i,j] for i,j in gold['tree'].overlap(gold['tree']) if i<j and not set(gold['faces'][i])&set(gold['faces'][j])]
    result['pad_self_crossings']=[[i,j] for i,j in pad['tree'].overlap(pad['tree']) if i<j and not set(pad['faces'][i])&set(pad['faces'][j])]
    join=c8.evaluated(bpy.data.objects[s11.GUSSET]);chains=report['gold_join']['attachments'];segments={}
    for key in ('top_vertices','lower_vertices'):
        segments[key]=[(join['p'][a],join['p'][b]) for chain in chains for a,b in zip(chain[key],chain[key][1:])]
    result['gold_join_collar']=seam_contacts(join,coat,segments['top_vertices'],cols)
    result['gold_join_epaulette']=seam_contacts(join,gold,segments['lower_vertices'])
    result['gold_join_pad_crossings']=len(join['tree'].overlap(pad['tree']))
    result['gold_join_head_crossings']=len(join['tree'].overlap(c8.evaluated(bpy.data.objects['Hassler head — native unchanged'])['tree']))
    count=len(bpy.data.objects[s11.GUSSET].data.vertices)
    result['gold_join_self_crossings']=[[i,j] for i,j in join['tree'].overlap(join['tree']) if i<j and not {v%count for v in join['faces'][i]}&{v%count for v in join['faces'][j]}]
    result.pop('epaulette_crossing_centers',None)
    print('POSE',label,'gold/pad',result['pad_gold_triangle_crossings'],'gold/collar',result['gold_collar_crossings'],'pad/collar',result['pad_collar_crossings'],'gold self',len(result['gold_self_crossings']),'pad self',len(result['pad_self_crossings']),flush=True)
    print('JOIN',label,'free/collar',len(result['gold_join_collar']['free_contacts']),'free/gold',len(result['gold_join_epaulette']['free_contacts']),'pad',result['gold_join_pad_crossings'],'self',len(result['gold_join_self_crossings']),flush=True)
    return result

def main():
    bpy.ops.wm.open_mainfile(filepath=str(s11.PARENT));configure('character_rounding');edit=bpy.data.collections['EDIT — native costume upper study']
    keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged','00 Native lower body and belt',s11.SHIRT,s11.LINING]+[o.name for o in edit.objects if o.name.startswith(('13.','11 '))]
    previous={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot();old=mesh(next(o for o in edit.objects if o.name.startswith('10 ')))
    path=s11.OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');report=json.loads((s11.OUT/'report.json').read_text(encoding='utf8'));assert sha(s11.PARENT)==report['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[name][k]),(name,k)
        for k in ('faces','weights'):assert now[k]==previous[name][k],(name,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    coat=bpy.data.objects[s11.GARMENT];data=mesh(coat)
    for k in ('points','uv'):assert np.array_equal(data[k],old[k]),k
    for k in ('faces','weights'):assert data[k]==old[k],k
    joining=bpy.data.objects[s11.GUSSET];jm=mesh(joining);seam_errors=[]
    for chain in report['gold_join']['attachments']:
        for i in chain['top_vertices']:
            j=int(np.argmin(np.linalg.norm(data['points']-jm['points'][i],axis=1)))
            error=float(np.linalg.norm(data['points'][j]-jm['points'][i]));seam_errors.append(error)
            assert error<1e-7 and jm['weights'][i]==data['weights'][j]
    topo=topology(coat.data);assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0
    shells={}
    for n in (s11.EPAULETTES,s11.PAD):
        ob=bpy.data.objects[n];t=topology(ob.data);assert len(t['connected_components'])==2 and not t['boundary_loops'] and t['nonmanifold_edges']==0
        bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free();assert volume>0
        shells[n]={'components':2,'boundary_edges':0,'nonmanifold_edges':0,'signed_volume_m3':volume}
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
    print('UV',uvzero,flush=True);assert influences<=4 and sum(p['vertices'] for p in parts.values())<65535
    if '--render' in sys.argv:s11.render(scene,'right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43)
    audits=[]
    for frame,label in [(1,'rest'),(30,'elbows'),(60,'shoulders'),(120,'body_and_head_turn')]:scene.frame_set(frame);audits.append(pose_audit(scene,report,label))
    scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland'];bone=rig.pose.bones['Body_Head'];mode=bone.rotation_mode;basis=bone.matrix_basis.copy();action=rig.animation_data.action;rig.animation_data.action=None;bone.rotation_mode='QUATERNION'
    for label,axis,angle in [('head_turn_left',(0,0,1),.65),('head_turn_right',(0,0,1),-.65),('head_nod',(1,0,0),-.35),('head_look_up',(1,0,0),.28),('head_tilt',(0,1,0),.28)]:
        local=rig.data.bones['Body_Head'].matrix_local.to_3x3().inverted()@Vector(axis);bone.rotation_quaternion=Quaternion(local,angle);bpy.context.view_layer.update();r=pose_audit(scene,report,label);r['axis']=axis;r['angle_radians']=angle;audits.append(r)
        if '--render' in sys.argv and label in ('head_nod','head_turn_right'):
            before=np.array(bone.matrix);s11.render(scene,label,(.35,1,.14),(0,.01,1.55),.60);assert np.max(abs(np.array(bone.matrix)-before))<2e-6
    bone.rotation_mode=mode;bone.matrix_basis=basis;rig.animation_data.action=action;scene.frame_set(1);bpy.context.view_layer.update()
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    clean=not any(uvzero.values()) and all(a['neck_seam_max_error_m']<2e-6 and a['pad_gold_triangle_crossings']==0 and a['gold_collar_crossings']==0 and a['pad_collar_crossings']==0 and a['head_coat_triangle_crossings']==0 and not a['gold_self_crossings'] and not a['pad_self_crossings'] and not a['gold_join_collar']['free_contacts'] and not a['gold_join_epaulette']['free_contacts'] and a['gold_join_pad_crossings']==0 and a['gold_join_head_crossings']==0 and not a['gold_join_self_crossings'] and not any(a['cord_to_cord_crossings'].values()) and all(c['coat_triangle_crossings']==0 and all(i<7 for i in c['epaulette_crossing_rings']) for c in a['cord_contacts'].values()) for a in audits)
    result={'reopened':True,'blend_sha256':sha(path),'parent_step10_unchanged':True,'native_head_neck_hands_lower_body_rig_shirt_red_lining_cords_binding_unchanged':True,'coat_geometry_original_uv_faces_weights_unchanged':True,'accepted_hanging_flap_unchanged':True,'closed_shoulders':shells,'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,'parts':parts,'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'pose_audits':audits,'layer_checks_passed':clean,'game_installed':False,'game_animations_validated':False}
    if '--render' in sys.argv:
        for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),('shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43),('collar_close',(.35,1,.18),(0,.02,1.53),.64),('shoulders_above',(0,1,.8),(0,.01,1.50),.72),('back',(0,-1,.03),(0,0,1.47),1.02),('side',(1,0,.03),(0,0,1.47),1.02)]:s11.render(scene,label,direction,target,scale)
        scene.frame_set(60);s11.render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(120);s11.render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1);result['previews_bound_to_blend_sha256']=sha(path)
    (s11.OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('RESULT',json.dumps({k:result[k] for k in ('blend_sha256','layer_checks_passed','body_triangles_with_modifiers')}),flush=True)
    if '--strict' in sys.argv:assert clean,'Layer checks failed; inspect validation.json'

if __name__=='__main__':main()
