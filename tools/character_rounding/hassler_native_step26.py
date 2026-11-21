"""Taper only pad crowns, curl the gold overhang down and clean the collar join."""
import sys,json,math,shutil,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_native_step20 as geometry
import hassler_native_step23 as s23
import hassler_native_step24 as s24
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_26';SOURCE=TOP/'step_25/hassler_native_upper.blend'

def curl(p):
    x,y,z=map(float,p);side=1 if x>=0 else -1;a=abs(x)
    # Preserve the accepted central crown. The last 4 cm turn down in a real
    # arc, instead of lowering an entire flat board or extruding a hanging flap.
    excess=max(0,a-.245);radius=.030;angle=excess/radius
    a=.245+radius*math.sin(angle) if excess else a
    z-=radius*(1-math.cos(angle))
    # Dietrich's front and rear returns also curve down over the grey support.
    weight=s23.smooth(.135,.20,abs(x));front=y>=.01278;start=.070 if front else -.052
    excess=max(0,y-start) if front else max(0,start-y);r=.032;angle=excess/r
    target=start+(1 if front else -1)*r*math.sin(angle) if excess else y
    y+=(target-y)*weight;z-=r*(1-math.cos(angle))*weight
    return np.array([side*a,y,z])

def edit_positions(ob,fn):
    me=ob.data;before=np.array([v.co[:] for v in me.vertices]);normals=np.array([n.vector[:] for n in me.corner_normals]);grad={}
    for v,p in zip(me.vertices,before):
        q=fn(v.index,p);v.co=q
        if np.linalg.norm(q-p)<1e-9:continue
        J=np.empty((3,3))
        for a in range(3):
            e=np.zeros(3);e[a]=1e-5;J[:,a]=(fn(v.index,p+e)-fn(v.index,p-e))/(2e-5)
        assert np.linalg.det(J)>.035,(ob.name,v.index,np.linalg.det(J))
        grad[v.index]=np.linalg.inv(J).T
    me.update()
    if me.has_custom_normals:
        nn=[]
        for loop,n in zip(me.loops,normals):
            n=grad.get(loop.vertex_index,np.eye(3))@n;n/=max(np.linalg.norm(n),1e-12);nn.append(n)
        me.normals_split_custom_set(nn)
    return before,np.array([v.co[:] for v in me.vertices])

def render(scene,prefix):
    views.OUT=OUT
    views.render(scene,prefix+'_front',(0,1,0),(0,0,1.4),1.1)
    views.render(scene,prefix+'_profile',(-1,.04,.35),(.19,.01,1.55),.42)
    views.render(scene,prefix+'_other_profile',(1,.04,.35),(-.19,.01,1.55),.42)

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    if not (OUT/'user_shoulder.png').exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-sj8GFf.png',OUT/'user_shoulder.png')
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));rig_hash=s23.rig_hash(rig)
    if '--no-render' not in sys.argv and not (OUT/'before_other_profile.png').exists():
        runtime.cull_materials(edit.objects);render(scene,'before')
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '))
    objects=[o for o in edit.objects if o.type=='MESH'];fixed={o.name:geometry.geometry_hash(o) for o in objects};invariants={o.name:s24.mesh_invariants(o) for o in objects}
    ep=next(o for o in objects if o.name.startswith('14 '));pad=next(o for o in objects if o.name.startswith('16 '));join=next(o for o in objects if o.name.startswith('17 '))
    e0,e1=edit_positions(ep,lambda i,p:curl(p))
    # Original support topology: 19x25 top, 19x25 bottom, seven perimeter
    # transition rows per side. Freeze the lower surface and the last two rows.
    grid=19*25;rim=2*19+2*(25-2);half=2*grid+7*rim
    assert len(pad.data.vertices)==2*half
    def factor(i):
        k=i%half
        if k<grid:return 1.
        if k<2*grid:return 0.
        t=(.12,.25,.40,.56,.70,.82,.92)[(k-2*grid)//rim]
        return 1-s23.smooth(0,.8,t)
    def narrow(i,p):
        q=p.copy();f=factor(i);side=1 if p[0]>0 else -1
        q[0]=side*(.205+(abs(p[0])-.205)*(1-.28*f))
        q[1]=.01278+(p[1]-.01278)*(1-.28*f)
        return q
    p0,p1=edit_positions(pad,narrow);bottom=[i for i in range(len(p0)) if factor(i)==0]
    assert np.array_equal(p0[bottom],p1[bottom])
    # Rebuild the joining cloth as ruled strips between its sewn collar anchor
    # and the newly curled board. Earlier successive deformations left bent
    # intermediate columns that projected as hooks beside the grey collar.
    j0=np.array([v.co[:] for v in join.data.vertices]);assert len(j0)%4==0
    reversed_before=0
    for start in range(0,len(j0),4):
        a=j0[start];b=curl(j0[start+3]);direction=j0[start+3]-a
        reversed_before+=sum(np.dot(j0[start+k+1]-j0[start+k],direction)<-1e-9 for k in range(3))
        for k,t in enumerate((0.,.25,.6,1.)):
            q=a*(1-t)+b*t
            # The rear return previously followed the free collar tip and
            # projected sideways as a triangular hook. Tuck that short return
            # under the grey lip, retaining the gold backing rather than
            # deleting it and reopening a side slit.
            tuck=(1-s23.smooth(-.07,-.035,q[1]))*s23.smooth(.105,.14,abs(q[0]))
            q[0]-=math.copysign(.025*tuck,q[0])
            # The long left lapel has a different front termination from the
            # closed right collar cap. Hide its gold return underneath the
            # lapel instead of allowing its reverse face into the neckline.
            if q[0]<0:
                front=s23.smooth(.075,.105,q[1])
                q[0]-=max(0,.108-abs(q[0]))*front
                q[2]-=.012*front
            join.data.vertices[start+k].co=q
    if join.data.has_custom_normals:
        native.activate(join);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    join.data.update();j1=np.array([v.co[:] for v in join.data.vertices])
    reversed_after=sum(np.dot(j1[start+k+1]-j1[start+k],j1[start+3]-j1[start])<-1e-9 for start in range(0,len(j1),4) for k in range(3))
    # The historical front returns were built before the grey facing became a
    # complete shell. They now sit behind that shell and can poke into the neck
    # in animation. Remove only those redundant ends; keep the lateral gold
    # panel connecting the shoulder to the collar. Solidify closes its cut rim.
    bm=bmesh.new();bm.from_mesh(join.data);bm.faces.ensure_lookup_table()
    redundant=[f for f in bm.faces if min(v.index for v in f.verts)<12 or min(v.index for v in f.verts)>=136]
    removed_faces=len(redundant);bmesh.ops.delete(bm,geom=redundant,context='FACES_ONLY')
    # Retain unused control vertices for stable authoring indices and weights.
    bm.to_mesh(join.data);bm.free();join.data.update()
    changed={ep.name,pad.name,join.name}
    for ob in objects:
        if ob!=join:assert s24.mesh_invariants(ob)==invariants[ob.name],ob.name
        if ob.name not in changed:assert geometry.geometry_hash(ob)==fixed[ob.name],ob.name
    assert s23.rig_hash(rig)==rig_hash
    report={'parent':str(SOURCE),'parent_sha256':digest,'native_skeleton_sha256':rig_hash,'bones_unchanged':True,'pad_upper_plan_scale':.72,'pad_bottom_vertices_unchanged':len(bottom),'pad_height_unchanged':bool(np.array_equal(p0[:,2],p1[:,2])),'epaulette_max_drop_m':float((e0[:,2]-e1[:,2]).max()),'epaulette_outer_curl_start_x_m':.245,'epaulette_outer_radius_m':.030,'join_sections':len(j0)//4,'join_backtracking_segments_before':int(reversed_before),'join_backtracking_segments_after':0,'topology_uv_skin_unchanged':True,'unchanged_geometry':{n:h for n,h in fixed.items() if n not in changed},'new_polygons':0,'game_launched':False}
    report['join_backtracking_segments_after']=int(reversed_after)
    report['rear_gold_return_tuck_max_m']=.025
    report['left_lapel_front_return']='Tucked outside neckline and 12 mm down underneath the asymmetric grey lapel'
    report['removed_redundant_gold_front_quads']=removed_faces
    report['topology_uv_skin_unchanged']=False
    report['unchanged_attributes']='All existing skin weights and UVs retained; only redundant gold front-return faces removed'
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    native.activate(ep);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));runtime.cull_materials(edit.objects)
    if '--no-render' not in sys.argv:render(scene,'after')
    print(json.dumps({k:v for k,v in report.items() if k!='unchanged_geometry'}),flush=True)

if __name__=='__main__':main()
