"""Drawn shoulder tailoring: compact pads, sleeve support, grey draped collar."""
import sys,json,math,shutil
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
import hassler_native_step08 as s8
import hassler_native_step09 as s9
import hassler_native_step11 as s11
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_12';PARENT=TOP/'step_11/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — grey draped collar and fitted sleeves'
EPAULETTES=s11.EPAULETTES
PAD='16 Grey shoulder pads — tailored inside gold contour'
GUSSET='17 Gold cloth — fitted under draped grey collar';SHIRT=s11.SHIRT;LINING=s11.LINING
TRIM='18 Collar — continuous red edge'

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def collar_rows(coat):
    prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'));faces=prior['cut']['collar_faces'];rows=[]
    for k in range(0,len(faces),5):
        ff=[list(coat.data.polygons[i].vertices) for i in faces[k:k+5]]
        if not rows:rows.append([ff[0][0]]+[f[1] for f in ff])
        rows.append([ff[0][3]]+[f[2] for f in ff])
    return faces,rows

def resize_pad(old,ep,edit,archive,names):
    ob=s8.clone(old,PAD,edit,archive);roof=s8.SampleMesh(ep,names);before=np.array([v.co[:] for v in ob.data.vertices])
    def height(x,y):
        x=abs(x)  # identical fit on mirrored non-planar gold quads
        p,no,fi,dd=roof.tree.ray_cast(Vector((x,y,.8)),Vector((0,0,-1)))
        if p is None:p,no,fi,dd=roof.tree.find_nearest(Vector((x,y,.57)))
        return p.z
    for v in ob.data.vertices:
        p=np.array(v.co);side=1 if p[0]>0 else -1
        q=p.copy();q[0]=side*(.205+(abs(p[0])-.205)*.65);q[1]=.008+(p[1]-.008)*.92
        oldh=height(p[0],p[1]);newh=height(q[0],q[1]);depth=float(np.clip((oldh-p[2]-.009)/max(.004,oldh-.493-.009),0,1))
        u=float(np.clip((abs(q[0])-.078)/.160,0,1));hem=s11.point(u,1,1)[2]-.018+.018*max(0,-q[1])/.10
        q[2]=(1-depth)*(newh-.009)+depth*min(hem,newh-.013)
        v.co=q
    s9.recalc(ob)
    ob['construction']='Same closed padding topology, narrowed in plan and raised under the gold roof. It retains a rounded visible grey band, not a uniform thin strip. Mirrored geometry on both shoulders.'
    return ob,{'plan_width_scale':.65,'depth_scale':.92,'lower_hem':'18 mm below the drawn front gold contour, rising towards the outer tip and rear','gold_clearance_m':.009,'old_bounds':[before.min(axis=0).tolist(),before.max(axis=0).tolist()],'new_bounds':[np.array([v.co[:] for v in ob.data.vertices]).min(axis=0).tolist(),np.array([v.co[:] for v in ob.data.vertices]).max(axis=0).tolist()]}

def tailor_coat(old,ep,pad,edit,archive,names):
    ob=s8.clone(old,GARMENT,edit,archive);me=ob.data;before=np.array([v.co[:] for v in me.vertices]);normals=[n.vector[:] for n in me.corner_normals]
    faces,rows=collar_rows(ob);collarids={i for fi in faces for i in me.polygons[fi].vertices};roof=s8.SampleMesh(ep,names)
    # Both cloth faces and the small returned rim are grey. No gold collar face.
    for i in (15,22,33):me.materials[i]=me.materials[4]
    for fi in faces:me.polygons[fi].material_index=4
    targets={};seated=[]
    for row in rows:
        edge=before[row[-1]].copy();roll=before[row[2]].copy();side=1 if edge[0]>0 else -1
        band=s3.smooth(.490,.550,edge[2])*s3.smooth(.075,.115,abs(edge[0]))
        if band<1e-7:continue
        # Lower the outer fall onto the epaulette, preserving its sewn neck root.
        hit,no,fi,dd=roof.tree.ray_cast(Vector((edge[0],edge[1],.8)),Vector((0,0,-1)))
        if hit is not None:
            newedge=edge.copy();newedge[2]=hit.z+.006;seated.append(row[-1])
        else:newedge=edge.copy();newedge[2]-=.025*band
        # Wearer-right short tip: fall outwards over the shoulder, not vertically
        # inside it. The long wearer-left lapel keeps its existing chest end.
        front=s3.smooth(.045,.115,edge[1])*s3.smooth(.035,.08,edge[0])
        newedge[0]+=.014*front;newedge[1]+=.006*front
        newroll=roll.copy();newroll[2]-=.006*band
        for j in range(1,6):
            if j<2:target=before[row[j]].copy();target[2]-=.002*band
            else:
                t=(j-2)/3;target=(1-t)*newroll+t*newedge;target[2]+=.006*math.sin(math.pi*t)
            targets[row[j]]=(1-band)*before[row[j]]+band*target
    for i,p in targets.items():me.vertices[i].co=p
    # Interpolate the few conforming collar-edge vertices outside the row grid.
    segments=[(a,b) for row in rows for a,b in zip(row,row[1:])]+[(a[j],b[j]) for a,b in zip(rows,rows[1:]) for j in range(6)]
    for i in collarids-{v for row in rows for v in row}:
        p=before[i];best=None
        for a,b in segments:
            d=before[b]-before[a];t=float(np.clip(np.dot(p-before[a],d)/max(np.dot(d,d),1e-15),0,1));dist=np.linalg.norm(p-before[a]-t*d)
            if best is None or dist<best[0]:best=(dist,a,b,t)
        dist,a,b,t=best
        if dist<1e-5:me.vertices[i].co=p+(1-t)*(np.array(me.vertices[a].co)-before[a])+t*(np.array(me.vertices[b].co)-before[b])
    # Continue the real green sleeve into its smaller shoulder pad. Only green
    # upper-arm vertices move; the original cuff, elbow and torso are unchanged.
    green={i for f in me.polygons if f.material_index==0 for i in f.vertices};sleeves=[]
    for i in sorted(green-collarids):
        p=before[i].copy();a=abs(p[0]);f=s3.smooth(.460,.520,p[2])*s3.smooth(.222,.250,a)*(1-s3.smooth(.28,.34,a))
        if f<=0:continue
        # A monotone extension retains the sleeve's fabric volume. Snapping
        # several old height rows onto one contact height would flatten them.
        q=p.copy();q[2]+=.026*f
        if np.linalg.norm(q-p)>1e-8:me.vertices[i].co=q;sleeves.append(i)
    me.update();changed={i for i,v in enumerate(me.vertices) if np.linalg.norm(np.array(v.co)-before[i])>1e-8}
    me.normals_split_custom_set([me.vertices[l.vertex_index].normal[:] if l.vertex_index in changed else normals[i] for i,l in enumerate(me.loops)])
    ob['construction']='Grey collar on both sides, lowered to lie on the gold epaulettes. Green upper sleeves continue into the compact shoulder pads. Neck sewing root, red opened flap and long left chest lapel retained.'
    return ob,{'changed_vertices':sorted(changed),'sleeve_vertices':sleeves,'collar_vertices':sorted(changed&collarids),'seated_edge_vertices':seated,'collar_faces':faces,'hinge_vertices':[r[0] for r in rows],'max_delta_m':np.max(abs(np.array([v.co[:] for v in me.vertices])-before),axis=0).tolist()}

def red_collar_edge(coat,edit,rig,names):
    faces,rows=collar_rows(coat);me=coat.data;adj={}
    for fi in faces:
        ids=list(me.polygons[fi].vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):adj[tuple(sorted((a,b)))]=adj.get(tuple(sorted((a,b))),0)+1
    hinge={r[0] for r in rows};edges={e for e,count in adj.items() if count==1 and not set(e)<=hinge}
    # Generate the boundary piping explicitly; all other garment seams are
    # rebuilt with the usual collar-exclusion rule, so there is no double trim.
    graph={}
    for a,b in edges:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
    pending=set(edges);paths=[]
    while pending:
        endpoints=[i for i,ns in graph.items() if len(ns)==1 and any(tuple(sorted((i,j))) in pending for j in ns)]
        a=endpoints[0] if endpoints else next(iter(pending))[0];path=[a]
        while True:
            candidates=[b for b in graph[a] if tuple(sorted((a,b))) in pending]
            if not candidates:break
            b=candidates[0];pending.remove(tuple(sorted((a,b))));path.append(b);a=b
        if len(path)>1:paths.append(path)
    skin=s8.weights(coat,names);ps=[];uv=[];ws=[];fs=[];radius=.0014
    for path in paths:
        offset=len(ps);length=0.
        for j,i in enumerate(path):
            p=np.array(me.vertices[i].co);a=np.array(me.vertices[path[max(0,j-1)]].co);b=np.array(me.vertices[path[min(len(path)-1,j+1)]].co);t=b-a;t/=np.linalg.norm(t)
            no=np.array(me.vertices[i].normal);no-=t*np.dot(no,t)
            if np.linalg.norm(no)<1e-7:no=np.cross(t,[0,0,1])
            no/=np.linalg.norm(no);other=np.cross(t,no)
            if j:length+=np.linalg.norm(p-a)
            for k in range(8):
                angle=k*2*math.pi/8;ps.append(p-np.array(me.vertices[i].normal)*.0012+radius*(no*math.cos(angle)+other*math.sin(angle)));uv.append((length*20,k/8));ws.append(skin[i])
        for j in range(len(path)-1):
            for k in range(8):a=offset+j*8+k;b=offset+j*8+(k+1)%8;fs.append([a,b,b+8,a+8])
        fs.extend([[offset+k for k in range(7,-1,-1)],[offset+(len(path)-1)*8+k for k in range(8)]])
    ob=upper.geometry(TRIM,ps,fs,uv,ws,me.materials[3],edit,rig,names);s9.recalc(ob)
    for f in ob.data.polygons:
        if len(f.vertices)==8:
            for k,li in enumerate(f.loop_indices):a=k*2*math.pi/8;ob.data.uv_layers.active.data[li].uv=(.5+.45*math.cos(a),.5+.45*math.sin(a))
    ob['construction']='Continuous red piping along the exposed collar edge, 2.8 mm diameter; no red face field.'
    return ob,{'paths':paths,'diameter_m':radius*2}

def body_binding(old,coat,edit,archive,rig,names,prior):
    native.move(old,archive);g=s3.Garment(upper.Surface(native.load('body')),names,rig,edit,list(coat.data.materials[:prior['reverse_material_offset']]))
    g.p=[np.array(v.co) for v in coat.data.vertices];g.w=list(s8.weights(coat,names));layer=coat.data.uv_layers.active
    for f in coat.data.polygons:g.face(list(f.vertices),f.material_index,[layer.data[li].uv[:] for li in f.loop_indices])
    cf=set(prior['cut']['collar_faces'])
    for fi,(mat,ids) in enumerate(g.faces):
        for a,b in zip(ids,ids[1:]+ids[:1]):
            if fi in cf or (min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32):g.no_trim.add(tuple(sorted((a,b))))
            if min(abs(g.p[i][0]) for i in (a,b))>.085 and min(g.p[i][2] for i in (a,b))>.500:g.no_trim.add(tuple(sorted((a,b))))
    rows=prior['flap']['section_vertices']
    for a,b in zip(rows,rows[1:]):g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for row in (rows[0],rows[-1]):
        for j in (0,1):g.no_trim.add(tuple(sorted((row[j],row[j+1]))))
    return s3.piping(coat,g,g.mats[3],edit,rig,names)

def main():
    OUT.mkdir(parents=True,exist_ok=True);ref=TOP/'source/shoulder_fit_study/user_front_step12.png'
    if not ref.exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-Mh8cGT.png',ref)
    digest=s2.sha(PARENT);bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step11 before annotated shoulder tailoring');archive.hide_viewport=archive.hide_render=True
    names=[b['name'] for b in native.load('body')['bones']];rig=bpy.data.objects['RIG — native Rheinland'];old={key:next(o for o in edit.objects if o.name.startswith(key)) for key in ('10 ','11 ','16 ','17 ')};ep=bpy.data.objects[EPAULETTES]
    pad,padr=resize_pad(old['16 '],ep,edit,archive,names);coat,tailor=tailor_coat(old['10 '],ep,pad,edit,archive,names)
    # Joining gold belongs to the tunic under the grey collar, not its reverse.
    native.move(old['17 '],archive);gusset,join=s11.close_collar_gap(coat,ep,edit,rig,names,{'faces':tailor['collar_faces']});gusset.name=GUSSET
    solid=next(m for m in gusset.modifiers if m.type=='SOLIDIFY');solid.thickness=.0006;solid.name='Gold joining cloth 0.6 mm';join['thickness_m']=.0006
    prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'))
    binding=body_binding(old['11 '],coat,edit,archive,rig,names,prior);edge,red=red_collar_edge(coat,edit,rig,names)
    previous=json.loads((TOP/'step_11/report.json').read_text(encoding='utf8'))
    report={'step':'12 annotated compact shoulders and grey draped collar','parent':str(PARENT),'parent_sha256':digest,'reference':str(ref),'pad':padr,'tailoring':tailor,'collar_lining':{'faces':tailor['collar_faces'],'all_sides_grey':True},'collar_red_edge':red,'gold_join':join,'neck':previous['neck'],'cords':previous['cords'],'inherited_opening':previous['inherited_opening'],'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2));native.activate(coat)
    scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    if '--no-render' not in sys.argv:
        render(scene,'front',(0,1,0));render(scene,'right_shoulder_detail',(.7,1,.25),(.18,0,1.51),.43);render(scene,'shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43)
    assert s2.sha(PARENT)==digest;print('STEP12 SAVED',flush=True)

if __name__=='__main__':main()
