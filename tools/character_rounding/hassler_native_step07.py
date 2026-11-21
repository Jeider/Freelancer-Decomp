"""User-drawn opening: red upper lining and a lower, freely turned gold front.

The hanging cloth is part of the tunic facing. Its hinge does not join the
grey collar. Step 05 supplies the unchanged sewn sleeves and independent collar;
step 06 is retained in the saved archive and is the review parent.
"""
import sys,json,math,shutil
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
import hassler_native_step04 as s4
import hassler_native_step05 as s5
import hassler_native_step06 as s6
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_07';PARENT=TOP/'step_06/hassler_native_upper.blend'
BASE=TOP/'step_05/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — lowered gold front with red reverse'
LINING='15 Exposed red tunic lining — upper right chest'
REFERENCE=TOP/'source/open_uniform_study/user_front_opening_step07.png'

def hinge_z(x):return .466-.13*x-2.4*x*x

def split(records,fn):
    """Split full position/skin/UV records, interpolating at each shared edge."""
    sides=[[],[]]
    for a,b in zip(records,records[1:]+records[:1]):
        da,db=fn(a[0]),fn(b[0]);eps=1e-9
        if da>=-eps:sides[0].append(a)
        if da<=eps:sides[1].append(a)
        if (da>eps and db<-eps) or (da<-eps and db>eps):
            t=da/(da-db);r=tuple(x+(y-x)*t for x,y in zip(a,b))
            sides[0].append(r);sides[1].append(r)
    return [r if len(r)>=3 else [] for r in sides]

def skin_vertex(g,r):
    i=g.vertex(r[0]);w=r[1].copy();w[w<1e-7]=0;w[np.argsort(w)[:-4]]=0;w/=w.sum();g.w[i]=w
    return i

def add_records(g,records,mat):
    if len(records)<3:return None
    ids=[];uv=[]
    for r in records:
        i=skin_vertex(g,r)
        if not ids or ids[-1]!=i:ids.append(i);uv.append(r[2])
    if ids and ids[-1]==ids[0]:ids.pop();uv.pop()
    if len(set(ids))<3:return None
    start=len(g.faces);g.face(ids,mat,uv);return start

def conform(g,new_start):
    """Insert cut vertices into adjacent untouched polygons, preserving UVs."""
    tree=KDTree(len(g.p)-new_start)
    for i in range(new_start,len(g.p)):tree.insert(Vector(g.p[i]),i)
    tree.balance();changed=[]
    for fi,((mat,ids),uv) in enumerate(zip(g.faces,g.uv)):
        ring=[];chart=[]
        for k,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):
            p,q=g.p[a],g.p[b];d=q-p;length=np.linalg.norm(d);candidates=[(0,a)]
            if length>1e-8:
                for co,i,dist in tree.find_range(Vector((p+q)*.5),length*.501+1e-7):
                    t=np.dot(g.p[i]-p,d)/(length*length)
                    if 1e-6<t<1-1e-6 and np.linalg.norm(g.p[i]-(p+t*d))<2e-7:candidates.append((t,i))
            for t,i in sorted(candidates):
                ring.append(i);chart.append((1-t)*np.array(uv[k])+t*np.array(uv[(k+1)%len(uv)]))
        if len(ring)!=len(ids):changed.append(fi)
        g.faces[fi]=(mat,ring);g.uv[fi]=chart
    return changed

def cut_shell(old,report,rig,edit,names,surface):
    me=old.data;count=report['reverse_material_offset'];g=s3.Garment(surface,names,rig,edit,list(me.materials[:count]))
    g.p=[np.array(v.co,dtype=float) for v in me.vertices];g.w=[]
    for v in me.vertices:
        row=np.zeros(len(names))
        for a in v.groups:row[names.index(old.vertex_groups[a.group].name)]=a.weight
        g.w.append(row)
    g.ids={tuple(np.round(p,7)):i for i,p in enumerate(g.p)};base_count=len(g.p)
    lining=[];kept=[];removed=[];collar=[];uv=me.uv_layers.active
    flap=set(report['flap']['faces']);grey=set(report['collar']['faces'])
    for f in me.polygons:
        if f.index in flap:continue
        records=[(g.p[i].copy(),g.w[i].copy(),np.array(uv.data[li].uv)) for i,li in zip(f.vertices,f.loop_indices)]
        if f.material_index not in (1,2) or max(p[0][0] for p in records)<.005 or max(p[0][1] for p in records)<.02:
            dst=add_records(g,records,f.material_index);kept.append((dst,f.index))
            if f.index in grey:collar.append(dst)
            continue
        remaining=records;outside=[]
        for fn in (lambda p:p[0]-.005,lambda p:p[1]-.02,lambda p:p[2]-hinge_z(p[0])):
            remaining,out=split(remaining,fn) if remaining else ([],[])
            if out:outside.append(out)
        if not remaining:
            dst=add_records(g,records,f.material_index);kept.append((dst,f.index));continue
        removed.append(f.index)
        for part in outside:add_records(g,part,f.material_index)
        lining.append(remaining)
    conformed=conform(g,base_count);kept=[(dst,src) for dst,src in kept if dst not in conformed]
    # Locate the new lower opening boundary on the actual gold facing.
    adj={}
    for mat,ids in g.faces:
        for a,b in zip(ids,ids[1:]+ids[:1]):adj.setdefault(tuple(sorted((a,b))),[]).append(mat)
    hinge_edges=[]
    for (a,b),mats in adj.items():
        if len(mats)==1 and mats[0] in (1,2) and all(g.p[i][0]>.005-1e-6 and g.p[i][1]>.02 and abs(g.p[i][2]-hinge_z(g.p[i][0]))<.0005 for i in (a,b)):
            hinge_edges.append((a,b))
    graph={}
    for a,b in hinge_edges:graph.setdefault(a,[]).append(b);graph.setdefault(b,[]).append(a)
    ends=[i for i,v in graph.items() if len(v)==1];assert len(ends)==2,('Hinge endpoints',ends)
    hinge=[min(ends,key=lambda i:g.p[i][0])]
    while True:
        todo=[i for i in graph[hinge[-1]] if i not in hinge]
        if not todo:break
        assert len(todo)==1;hinge.append(todo[0])
    assert len(hinge)==len(graph)
    for mat,ids in g.faces:
        for a,b in zip(ids,ids[1:]+ids[:1]):
            if min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32:g.no_trim.add(tuple(sorted((a,b))))
    return g,lining,{'retained_base_faces':kept,'removed_upper_gold_faces':removed,'collar_faces':collar,'hinge_vertices':hinge}

def hang_front(g,hinge):
    rows=[];start=len(g.faces);xmin=g.p[hinge[0]][0];xmax=g.p[hinge[-1]][0]
    # Manually authored from the user's red silhouette, not auto image tracing.
    free=[(0,.010,.217,.451),(.22,.042,.235,.414),(.48,.087,.242,.350),
          (.68,.110,.225,.386),(1,xmax+.001,g.p[hinge[-1]][1]+.012,g.p[hinge[-1]][2]-.016)]
    for i in hinge:
        p=g.p[i];u=(p[0]-xmin)/(xmax-xmin);e=s4.rail(free,u)
        # Gold side rises into a narrow roll, then turns down with its red
        # reverse facing the viewer. The tip floats clear of the chest.
        roll=p+np.array([0,.009,.0045]);q=.74*roll+.26*e+np.array([0,.006,0])
        row=[i,g.vertex(p+np.array([0,.003,.0025])),g.vertex(roll),g.vertex(q),
             g.vertex(.35*roll+.65*e+np.array([0,.004,-.002])),g.vertex(e)]
        for j in row[1:]:g.w[j]=g.w[i].copy()
        rows.append(row)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        for j in range(5):
            ua=(g.p[a[0]][0]-xmin)/(xmax-xmin);ub=(g.p[b[0]][0]-xmin)/(xmax-xmin)
            uv=[(.48+ua*.23,.25+j*.075),(.48+ua*.23,.25+(j+1)*.075),
                (.48+ub*.23,.25+(j+1)*.075),(.48+ub*.23,.25+j*.075)]
            g.face([a[j],a[j+1],b[j+1],b[j]],1,uv)
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    # No ornamental piping buried in the first millimetres of the bend.
    for row in (rows[0],rows[-1]):
        for j in (0,1):g.no_trim.add(tuple(sorted((row[j],row[j+1]))))
    return {'faces':list(range(start,len(g.faces))),'red_reverse_faces':[start+5*k+j for k in range(len(rows)-1) for j in (3,4)],
            'hinge_vertices':hinge,'free_edge_vertices':[r[-1] for r in rows],'section_vertices':rows,
            'free_edge_authored_rails':free,'origin':'Lower cut edge of the gold tunic facing; independent of the grey collar.'}

def red_lining(records,g,rig,edit,names):
    panel=s3.Garment(g.surface,names,rig,edit,g.mats)
    for rs in records:
        # This is an exposed inner panel replacing the removed upper gold
        # fabric, not a red overlay hiding an intact outer gold face.
        shifted=[(p-np.array([0,.006,0]),w,uv) for p,w,uv in rs]
        add_records(panel,shifted,3)
    conform(panel,0)
    ob=panel.build();ob.name=LINING
    solid=next(m for m in ob.modifiers if m.type=='SOLIDIFY');solid.thickness=.0014
    # The cut pattern has several extremely narrow triangles. Use the cloth
    # surface area, rather than their corner angles, for a calm lining normal.
    me=ob.data;me.calc_loop_triangles();normals=np.zeros((len(me.vertices),3));adj=[set() for _ in me.vertices]
    for tri in me.loop_triangles:
        ids=list(tri.vertices);a,b,c=[np.array(me.vertices[i].co) for i in ids];n=np.cross(b-a,c-a)
        for i in ids:normals[i]+=n;adj[i].update(j for j in ids if j!=i)
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    for iteration in range(3):
        normals=np.array([.6*n+.4*np.mean(normals[list(adj[i])],axis=0) if adj[i] else n for i,n in enumerate(normals)])
        normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    me.normals_split_custom_set([normals[l.vertex_index] for l in me.loops])
    ob['construction']='Upper red lining replaces removed wearer-right gold faces; black throat is exposed centrally.'
    return ob

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s6.OUT=OUT;s6.render(scene,label,direction,target,scale)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Path('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-8eZx84.png')
    if not REFERENCE.exists():shutil.copyfile(source,REFERENCE)
    parent_hash=s2.sha(PARENT);base_hash=s2.sha(BASE)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    old=bpy.data.objects[s5.GARMENT];base_report=json.loads((TOP/'step_05/report.json').read_text(encoding='utf8'))
    source=native.load('body');names=[b['name'] for b in source['bones']];rig=bpy.data.objects['RIG — native Rheinland'];surface=upper.Surface(source)
    edit=bpy.data.collections['EDIT — native costume upper study']
    archive=native.collection('ARCHIVE — step 06 high collar-connected opening');archive.hide_viewport=archive.hide_render=True
    for ob in list(edit.objects):
        if ob.name.startswith(('10 ','11 ','15 ')):native.move(ob,archive)
    g,lining,cut=cut_shell(old,base_report,rig,edit,names,surface);flap=hang_front(g,cut['hinge_vertices'])
    garment=g.build();garment.name=GARMENT
    donor={}
    for loop,no in zip(old.data.loops,old.data.corner_normals):donor.setdefault(loop.vertex_index,np.array(no.vector))
    # Preserve the authored sleeve/forearm shading; new cuts and rolls receive
    # geometric normals. Collar normals retain the independently ending shape.
    fold_normals={};rows=flap['section_vertices']
    for k,row in enumerate(rows):
        for j in range(1,len(row)):
            along=g.p[rows[min(k+1,len(rows)-1)][j]]-g.p[rows[max(k-1,0)][j]]
            across=g.p[row[min(j+1,len(row)-1)]]-g.p[row[j-1]]
            n=np.cross(across,along);n/=max(np.linalg.norm(n),1e-12);fold_normals[row[j]]=n
    normals=[]
    for loop in garment.data.loops:
        i=loop.vertex_index;p=g.p[i]
        preserve=i in donor and (abs(p[0])>.17 or p[1]<.01 or p[2]<.35)
        normals.append(fold_normals[i] if i in fold_normals else donor[i] if preserve else garment.data.vertices[i].normal[:])
    garment.data.normals_split_custom_set(normals)
    count=len(g.mats)
    for i in [3,3,3,1,4,5,3]+list(range(7,count)):garment.data.materials.append(g.mats[i])
    next(m for m in garment.modifiers if m.type=='SOLIDIFY').material_offset=count
    garment['construction']=flap['origin'];garment['shoulder_stitch_vertices']=old['shoulder_stitch_vertices'];garment['forearm_stitch_vertices']=old['forearm_stitch_vertices']
    for name,ids in [('EDIT — hanging gold front',sorted({v for fi in flap['faces'] for v in g.faces[fi][1]})),('EDIT — front fold hinge',cut['hinge_vertices']),('EDIT — free hanging edge',flap['free_edge_vertices'])]:
        # Named mesh attributes are edit selections, not extra skin groups.
        attr=garment.data.attributes.new(name=name,type='BOOLEAN',domain='POINT')
        for i in ids:attr.data[i].value=True
    lining_ob=red_lining(lining,g,rig,edit,names);trim=s3.piping(garment,g,g.mats[3],edit,rig,names)
    # The old central red backing is archived, revealing the original black
    # shirt; no geometry or material change is made to that shirt.
    report={'step':'07 user-drawn lower opening','parent':str(PARENT),'parent_sha256':parent_hash,
            'geometry_base':str(BASE),'geometry_base_sha256':base_hash,'drawing':str(REFERENCE),'drawing_sha256':s2.sha(REFERENCE),
            'cut':cut,'flap':flap,'sleeves':base_report['sleeves'],'reverse_material_offset':count,'trim':trim,
            'red_lining_faces':len(lining_ob.data.polygons),'red_lining_inset_m':.006,'game_installed':False,'game_animations_validated':False,
            'construction':'Upper wearer-right gold front removed to expose red lining. Lower gold front turns down, red reverse visible, gold backside retained. Grey collar ends independently. Central neck/chest remains black.'}
    upper.dump(OUT/'report.json',report)
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    native.activate(garment);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    render(scene,'front',(0,1,0));render(scene,'three_quarter',(.65,1,.12))
    if '--quick' not in sys.argv:
        render(scene,'collar_close',(.35,1,.18),(0,.02,1.53),.64)
        render(scene,'fold_side',(.90,1,.1),(.065,.07,1.42),.45)
        render(scene,'back',(0,-1,.03));render(scene,'side',(1,0,.02))
        scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    assert s2.sha(PARENT)==parent_hash and s2.sha(BASE)==base_hash
    print(json.dumps({'step':7,'removed_gold_faces':len(cut['removed_upper_gold_faces']),'hinge_vertices':len(cut['hinge_vertices']),'hanging_faces':len(flap['faces'])}),flush=True)

if __name__=='__main__':main()
