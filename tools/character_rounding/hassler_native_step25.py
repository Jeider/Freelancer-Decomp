"""Restore sleeve articulation and readable matte native cloth on Hassler."""
import sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step08 as s8
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_native_step23 as s23
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_25';SOURCE=TOP/'step_24/hassler_native_upper.blend'

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24;views.OUT=OUT
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));coat=next(o for o in edit.objects if o.name.startswith('10 '));me=coat.data
    rig_hash=s23.rig_hash(rig);data=native.load('body');names=[b['name'] for b in data['bones']];surface=upper.Surface(data)
    p=np.array([v.co[:] for v in me.vertices]);old=s8.weights(coat,names);target=old.copy();strength=np.zeros(len(p));green={i for f in me.polygons if f.material_index==0 for i in f.vertices}
    roots=json.loads(coat['shoulder_stitch_vertices']);rootids=[i for row in roots for i in row]
    rootdist=np.min(np.linalg.norm(p[:,None,:]-p[rootids][None,:,:],axis=2),axis=1)
    armids=[names.index(n) for n in ('LUpArm','RUpArm','LLowArm','RLowArm')]
    adjacent=[set() for _ in p]
    for f in me.polygons:
        vs=list(f.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):adjacent[a].add(b);adjacent[b].add(a)
    # Work along the sewn sleeve topology. A nearest-body transfer is invalid
    # here: the inner sleeve lies close to the waist and used to inherit torso
    # weights, even several rows below its real shoulder attachment.
    ends=json.loads(coat['forearm_stitch_vertices']);components=[];rows_by_side=[];new=old.copy()
    blocked=set(rootids)
    for root,end in zip(roots,ends):
        component=set(end);todo=list(end)
        while todo:
            i=todo.pop()
            for j in adjacent[i]-blocked-component:component.add(j);todo.append(j)
        components.append(component)
        rows=[list(root)];visited=set(root)
        for _ in range(5):
            row=[]
            for i in rows[-1]:
                candidates=adjacent[i]&component-visited
                assert len(candidates)==1,(i,sorted(candidates))
                row.append(next(iter(candidates)))
            rows.append(row);visited.update(row)
        assert set(rows[-1])==set(end)
        rows_by_side.append(rows)
        for column in range(len(root)):
            wa=old[rows[0][column]];wb=old[rows[-1][column]]
            for ids,t in zip(rows,(0.,.16,.34,.55,.78,1.)):
                i=ids[column];blend=t**.7;new[i]=(1-blend)*wa+blend*wb
                new[i,np.argsort(new[i])[:-4]]=0;new[i]/=new[i].sum()
                strength[i]=1 if t>0 and t<1 else 0
    s8.set_weights(coat,new)
    # Relax the actual sewn underarm patch in several native poses. The old
    # straight loft has a flat, concave lower attachment which doubles over
    # when the arm opens. This local rest-mesh correction removes that fold
    # while retaining the shared stitches and the shoulder/cuff boundaries.
    geom_factor=np.array([(1-s23.smooth(.012,.065,rootdist[i]))*(1-s23.smooth(.46,.52,q[2]))*s23.smooth(.32,.38,q[2]) if i in green else 0 for i,q in enumerate(p)])
    gid=np.flatnonzero(geom_factor>0)
    bones,joints,bind=runtime.read_rig(TOP/'game/rig_for_preview.json')
    hip=json.loads((OUT/'ru_sleeve_clips.json').read_text())['clips']['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01']
    cross=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips']['Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06']
    C=np.array(native.C4);Ci=np.linalg.inv(C);transforms=[np.broadcast_to(np.eye(4),(len(p),4,4))]
    for clip,time in ((hip,.65),(hip,1.27),(cross,2.)):
        world=runtime.evaluate(bones,joints,bind,clip,time)
        mats=np.array([C@world[n]@np.linalg.inv(bind[n])@Ci for n in names])
        transforms.append(np.einsum('vb,bij->vij',new,mats))
    q=p.copy();inverses=[np.linalg.inv(m[gid,:3,:3]) for m in transforms]
    neighbors=[np.array(sorted(adjacent[i]),dtype=int) for i in gid]
    for _ in range(35):
        delta=np.zeros((len(gid),3))
        for mats,inv in zip(transforms,inverses):
            posed=np.einsum('vij,vj->vi',mats[:,:3,:3],q)+mats[:,:3,3]
            lap=np.array([posed[ns].mean(0)-posed[i] for i,ns in zip(gid,neighbors)])
            delta+=np.einsum('vij,vj->vi',inv,lap)/len(transforms)
        q[gid]+=.28*geom_factor[gid,None]*delta
    for i in gid:me.vertices[i].co=q[i]
    me.update();normals=[n.vector[:] for n in me.corner_normals]
    for loop in me.loops:
        i=loop.vertex_index
        if geom_factor[i]>0 or strength[i]>0:normals[loop.index]=me.vertices[i].normal[:]
    me.normals_split_custom_set(normals)
    geom_delta=np.linalg.norm(q-p,axis=1)
    # Existing piping follows any modified garment vertex at the sewn boundary.
    from mathutils.kdtree import KDTree
    kd=KDTree(len(p))
    for i,point in enumerate(p):kd.insert(Vector(point),i)
    kd.balance();trim_changes=0
    for ob in edit.objects:
        if not ob.name.startswith('11 '):continue
        ww=s8.weights(ob,names)
        for v in ob.data.vertices:
            loc,i,d=kd.find(v.co)
            if d<.004 and (strength[i]>0 or geom_factor[i]>0):
                ww[v.index]=new[i];v.co+=Vector(q[i]-p[i]);trim_changes+=1
        s8.set_weights(ob,ww)
    # Reuse the actual native fabric; keep all shared native textures external
    # to this authoring change and the stable Hassler material identities.
    for index in (0,6):
        mat=me.materials[index];nodes=mat.node_tree.nodes
        mix=next(n for n in nodes if n.type=='MIX_RGB');mix.inputs[0].default_value=.85
        bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.18
        mat['step25_cloth']='Native RH elite woven fabric, 85% image / 15% uniform green tint; matte.'
    # The old small top-atlas crop lost both the sleeve folds and fabric scale.
    # Map complete sleeve circumferences into the native sleeve fabric field.
    layer=me.uv_layers[0];uv_changed=0
    sleeve_vertices=set().union(*components)|blocked
    centers={1:None,-1:None}
    for root,end in zip(roots,ends):
        a=p[root].mean(0);b=p[end].mean(0);centers[1 if a[0]>0 else -1]=(a,b)
    for f in me.polygons:
        if f.material_index!=0:continue
        if not set(f.vertices)<=sleeve_vertices:continue
        side=1 if p[f.vertices[0],0]>0 else -1;a,b=centers[side];angles=[]
        for i in f.vertices:
            t=(a[2]-p[i,2])/(a[2]-b[2]);centre=a*(1-t)+b*t
            angle=math.atan2(p[i,1]-centre[1],side*(p[i,0]-centre[0]));angles.append((angle+math.pi)/(2*math.pi))
        if max(angles)-min(angles)>.5:angles=[v+1 if v<.5 else v for v in angles]
        for li,i,angle in zip(f.loop_indices,f.vertices,angles):
            height=float(np.clip((p[i,2]-.13)/.43,0,1))
            layer.data[li].uv=(.975-.355*height,.04+.28*angle);uv_changed+=1
    assert s23.rig_hash(rig)==rig_hash
    report={'parent':str(SOURCE),'parent_sha256':s13.sha(SOURCE),'native_skin_source':data['source'],'native_skin_source_sha256':data['sha256'],'skin_vertices_changed':int(np.count_nonzero(np.max(abs(new-old),axis=1)>1e-7)),'underarm_geometry_vertices':len(gid),'underarm_max_move_m':float(geom_delta.max()),'piping_skin_vertices':trim_changes,'sleeve_uv_loops_changed':uv_changed,'cloth_texture':data['groups'][1]['texture'],'texture_mix':.85,'roughness':.9,'bones_unchanged':True,'rig_sha256':rig_hash,'epaulette_depth_scale_inherited':.72,'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    native.activate(coat);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));runtime.cull_materials(edit.objects)
    views.render(scene,'after_front',(0,1,0),(0,0,1.4),1.1)
    clips=json.loads((OUT/'ru_sleeve_clips.json').read_text())['clips'];clip=clips['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01']
    for t in (0.,1.,3.):
        runtime.apply_blender(rig,TOP/'game/rig_for_preview.json',clip,t)
        views.render(scene,f'after_hip_{int(t)}',(.85,1,.03),(0,0,1.32),1.04)
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
