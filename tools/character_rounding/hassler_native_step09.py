"""User's shoulder drawing: long gold yokes, low red boundary, rounded grey caps."""
import sys,json,math,shutil
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
import hassler_native_step04 as s4
import hassler_native_step07 as s7
import hassler_native_step08 as s8
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_09';PARENT=TOP/'step_08/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — hanging grey collar'
LINING='15 Red lining — below drawn blue boundary'
EPAULETTES='14 Epaulettes — continuous long gold shoulders'
PAD='16 Grey shoulder caps — rounded over sleeves'
SHIRT=s8.SHIRT

def recalc(ob):
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()

def blue_z(x):return .5476-.200*x

def collar(old,edit,archive,prior,names,rig):
    ob=s8.clone(old,GARMENT,edit,archive);me=ob.data;normals=[n.vector[:] for n in me.corner_normals]
    faces=prior['cut']['collar_faces'];rows=[]
    for k in range(0,len(faces),5):
        ff=[list(me.polygons[i].vertices) for i in faces[k:k+5]]
        if not rows:rows.append([ff[0][0]]+[f[1] for f in ff])
        rows.append([ff[0][3]]+[f[2] for f in ff])
    changes=[];deltas=[]
    for row in rows:
        edge=np.array(me.vertices[row[-1]].co)
        along=s3.smooth(.015,.115,edge[1])*s3.smooth(.015,.06,edge[0])
        for j,i in enumerate(row):
            f=along*max(0,(j-2)/3)**1.25
            if f>0:
                delta=np.array([.012*f,.043*f,-.041*f])
                # A turned end, rather than a narrow vertical strip: the
                # intermediate corner falls toward the chest, the tip returns.
                delta+=along*np.array({3:(-.010,.014,-.003),4:(-.022,.020,-.014)}.get(j,(0,0,0)))
                me.vertices[i].co+=Vector(delta);changes.append(i);deltas.append(delta)
    # The historical rolled collar doubled back through its sewing root at
    # the right-front bend. Keep its falling surface outside that root.
    for row in rows:
        for i in row[3:]:
            p=np.array(me.vertices[i].co);r=np.linalg.norm(p[:2]);f=s3.smooth(.025,.065,p[0])*s3.smooth(-.020,.025,p[1])
            if f and r<.135:
                q=p.copy();q[:2]*=1+f*(.135-r)/r;me.vertices[i].co=q;changes.append(i);deltas.append(q-p)
    me.update();changed=set(changes)
    me.normals_split_custom_set([me.vertices[l.vertex_index].normal[:] if l.vertex_index in changed else normals[i] for i,l in enumerate(me.loops)])
    ob['construction']='Step08 shell retained; only the free end of the wearer-right grey collar hangs lower. Native neck remains open.'
    return ob,{'changed_vertices':sorted(changed),'tip':list(me.vertices[rows[0][-1]].co),'max_absolute_delta_m':np.max(abs(np.array(deltas)),axis=0).tolist(),'front_end_row':[[i,list(me.vertices[i].co)] for i in rows[0]]}

def clip_red(old,edit,archive,rig,names):
    me=old.data;ww=s8.weights(old,names);layer=me.uv_layers.active;ps=[];ws=[];fs=[];uvs=[];normals=[];lookup={}
    for f in me.polygons:
        rr=[(np.array(me.vertices[i].co),ww[i],np.array(layer.data[li].uv),np.array(me.corner_normals[li].vector)) for i,li in zip(f.vertices,f.loop_indices)]
        kept,_=s7.split(rr,lambda p:blue_z(p[0])-p[2]);ids=[];uv=[]
        for p,w,q,normal in kept:
            key=tuple(np.round(p,7))
            if key not in lookup:
                w=w.copy();w[np.argsort(w)[:-4]]=0;w/=w.sum();lookup[key]=len(ps);ps.append(p);ws.append(w);normals.append(normal/max(np.linalg.norm(normal),1e-9))
            if not ids or ids[-1]!=lookup[key]:ids.append(lookup[key]);uv.append(q)
        if len(ids)>2 and ids[0]==ids[-1]:ids.pop();uv.pop()
        if len(set(ids))>=3:fs.append(ids);uvs.append(uv)
    ob=s8.clone(old,LINING,edit,archive);new=bpy.data.meshes.new(LINING);new.from_pydata(ps,[],fs);new.update();new.materials.append(me.materials[3]);layer=new.uv_layers.new(name=me.uv_layers.active.name)
    for f,chart in zip(new.polygons,uvs):
        f.use_smooth=True
        for li,q in zip(f.loop_indices,chart):layer.data[li].uv=q
    ob.data=new
    for name in names:ob.vertex_groups.new(name=name)
    s8.set_weights(ob,np.array(ws));recalc(ob);new.normals_split_custom_set([normals[l.vertex_index] for l in new.loops])
    ob['construction']='Actual red geometry clipped below the manually interpreted blue line in the user drawing; no hidden red shoulder panel remains above it.'
    return ob,{'front_boundary_z':'.5476 - .200*x','vertices':len(ps),'faces':len(fs),'original_smooth_normals_interpolated':True,'max_above_boundary_m':float(max(p[2]-blue_z(p[0]) for p in ps))}

def shoulder_skin(surface,p,names):
    hit,no,idx,dist=surface.tree.find_nearest(Vector(p));w=surface.skin(hit,idx);side='R' if p[0]>0 else 'L';clav=names.index(side+'CollarBone');arm=names.index(side+'UpArm')
    for bone in ('LLowArm','RLowArm','LHand','RHand','Body_Head','Body_Neck'):
        j=names.index(bone);w[clav]+=w[j];w[j]=0
    excess=max(0,w[arm]-.28);w[arm]-=excess;w[clav]+=excess;w[np.argsort(w)[:-4]]=0;w/=w.sum();return w

def board_point(u,v,side):
    # Cross section runs back -> roof -> front. The front outline follows
    # the user's gold/blue landmarks, with no outward increase over step08.
    a=(v-.5)*math.pi;roof=math.cos(a);front=max(0,math.sin(a));back=max(0,-math.sin(a))
    xi=.149-.051*front-.003*back;xo=.280-.047*front-.025*back
    x=xi+(xo-xi)*u
    yf=.169-.041*u;yb=-.093-.018*u
    y=yf*front+yb*back
    crown=.589+.012*math.sin(math.pi*u*.82)
    zfront=float(np.interp(u,[0,.67,1],[.528,.5096,.520]))
    zback=.548-.015*u
    z=crown*roof+zfront*(1-roof)*front+zback*(1-roof)*back
    # The sine weights do not sum to one away from the section endpoints.
    z=crown*roof+(zfront if v>=.5 else zback)*(1-roof)
    return np.array([side*x,y,z])

def epaulettes(old,coat,edit,archive,rig,names):
    surface=s8.SampleMesh(coat,names,lambda f:f.material_index!=4 and f.center.z>.45)
    ps=[];uv=[];ws=[];fs=[];nu=19;nv=25;grids={}
    for side in (1,-1):
        grid=[]
        for j,v in enumerate(np.linspace(0,1,nv)):
            row=[]
            for i,u in enumerate(np.linspace(0,1,nu)):
                p=board_point(u,v,side);row.append(len(ps));ps.append(p);ws.append(shoulder_skin(surface,p,names));uv.append((.30+.60*v,.25+(u-.5)*.30*math.sqrt(1-((v-.5)*1.5)**2)))
            grid.append(row)
        for j in range(nv-1):
            for i in range(nu-1):
                ring=[grid[j][i],grid[j][i+1],grid[j+1][i+1],grid[j+1][i]];fs.append(ring if side>0 else ring[::-1])
        grids[str(side)]=grid
    ob=upper.geometry(EPAULETTES,ps,fs,uv,ws,old.data.materials[0],edit,rig,names);ob.data.uv_layers.active.name=old.data.uv_layers.active.name;ob.data.materials.append(old.data.materials[1]);recalc(ob)
    solid=ob.modifiers.new('Gold board thickness 2 mm','SOLIDIFY');solid.thickness=.002;solid.offset=-1;solid.material_offset=1;solid.material_offset_rim=1;solid.use_quality_normals=True
    ob['construction']='Continuous shoulder yoke extended inward to collar and blue boundary. Manual contours from the user drawing, Dietrich gold image with a new continuous UV chart.'
    native.move(old,archive)
    return ob,surface,{'grid_vertices':grids,'maximum_half_width_m':.280,'front_inner_xz':[.098,.528],'front_outer_xz':[.233,.520],'uv_crop':'U .30+.60*v; V .25+(u-.5)*.30*sqrt(1-((v-.5)*1.5)^2)','native_texture_retained':True,'native_uv_retained':False}

def caps(old,ep,surface,edit,archive,rig,names):
    ps=[];uv=[];ws=[];fs=[];n=48
    # Rounded, closed shoulder cap. Ring geometry is fitted below the actual
    # gold sheet, while the hem enters the sleeve instead of floating above it.
    rings=[(.583,.023,.037),(.576,.043,.064),(.558,.057,.090),(.538,.061,.105),(.517,.060,.103),(.498,.055,.091),(.489,.045,.074),(.496,.030,.052)]
    parameters=np.linspace(0,len(rings)-1,22);profiles=[s4.rail([(i,*r) for i,r in enumerate(rings)],t) for t in parameters]
    roof=s8.SampleMesh(ep,names)
    for side in (1,-1):
        start=len(ps)
        for j,(z,rx,ry) in enumerate(profiles):
            for k in range(n):
                a=2*math.pi*k/n;p=np.array([side*(.222+rx*math.cos(a)),.004+ry*math.sin(a)*(.86 if math.sin(a)<0 else 1),z])
                hit,no,idx,dist=roof.tree.ray_cast(Vector((p[0],p[1],.8)),Vector((0,0,-1)))
                if hit is not None:
                    fit=1-s3.smooth(1,2,parameters[j]);p[2]=min((1-fit)*p[2]+fit*(hit.z-.006),hit.z-.006)
                ps.append(p);uv.append((k/n,j/(len(profiles)-1)));ws.append(shoulder_skin(surface,p,names))
        for j in range(len(profiles)-1):
            for k in range(n):a=start+j*n+k;b=start+j*n+(k+1)%n;fs.append([a,b,b+n,a+n])
        fs.extend([[start+k for k in range(n-1,-1,-1)],[start+(len(profiles)-1)*n+k for k in range(n)]])
    ob=upper.geometry(PAD,ps,fs,uv,ws,ep.data.materials[1],edit,rig,names);recalc(ob)
    layer=ob.data.uv_layers.active
    for f in ob.data.polygons:
        if len(f.vertices)>4:
            for k,li in enumerate(f.loop_indices):a=2*math.pi*k/len(f.vertices);layer.data[li].uv=(.5+.45*math.cos(a),.5+.45*math.sin(a))
        else:
            qs=[layer.data[li].uv[:] for li in f.loop_indices]
            if max(q[0] for q in qs)-min(q[0] for q in qs)>.8:
                for li in f.loop_indices:
                    if layer.data[li].uv.x<.5:layer.data[li].uv.x+=1
    ob['construction']='Rounded grey cap over upper sleeve, inside the gold shoulder, with a smooth lower return. Separate editable shell; original green sleeve preserved.'
    native.move(old,archive);return ob,{'rings_z_rx_ry':rings,'smooth_profile_samples':len(profiles),'cap_center_xy':[.222,.004],'gold_clearance_m':.006}

def trim(old,coat,edit,archive,rig,names,prior):
    native.move(old,archive);g=s3.Garment(upper.Surface(native.load('body')),names,rig,edit,list(coat.data.materials[:prior['reverse_material_offset']]))
    g.p=[np.array(v.co) for v in coat.data.vertices];g.w=list(s8.weights(coat,names));layer=coat.data.uv_layers.active
    for f in coat.data.polygons:g.face(list(f.vertices),f.material_index,[layer.data[li].uv[:] for li in f.loop_indices])
    for mat,ids in g.faces:
        for a,b in zip(ids,ids[1:]+ids[:1]):
            if min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32:g.no_trim.add(tuple(sorted((a,b))))
            if min(abs(g.p[i][0]) for i in (a,b))>.085 and min(g.p[i][2] for i in (a,b))>.500:g.no_trim.add(tuple(sorted((a,b))))
    rows=prior['flap']['section_vertices']
    for a,b in zip(rows,rows[1:]):g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for row in (rows[0],rows[-1]):
        for j in (0,1):g.no_trim.add(tuple(sorted((row[j],row[j+1]))))
    return s3.piping(coat,g,g.mats[3],edit,rig,names)

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s7.OUT=OUT;s7.render(scene,label,direction,target,scale)

def main():
    OUT.mkdir(parents=True,exist_ok=True);ref=TOP/'source/shoulder_fit_study';ref.mkdir(parents=True,exist_ok=True)
    for src,name in [('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-ojVXlF.png','user_front_step09.png'),('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-rCSXZ9.png','user_grey_shoulder_step09.png')]:
        if not (ref/name).exists():shutil.copyfile(src,ref/name)
    digest=s2.sha(PARENT);bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step 08 before drawn shoulder correction');archive.hide_viewport=archive.hide_render=True
    rig=bpy.data.objects['RIG — native Rheinland'];names=[b['name'] for b in native.load('body')['bones']];prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'));previous=json.loads((TOP/'step_08/report.json').read_text(encoding='utf8'))
    old={key:next(o for o in edit.objects if o.name.startswith(key)) for key in ('10 ','11 ','14 ','15 ','16 ')}
    coat,collar_report=collar(old['10 '],edit,archive,prior,names,rig);lining,red=clip_red(old['15 '],edit,archive,rig,names)
    ep,surface,gold=epaulettes(old['14 '],coat,edit,archive,rig,names);pad,grey=caps(old['16 '],ep,surface,edit,archive,rig,names)
    binding=trim(old['11 '],coat,edit,archive,rig,names,prior)
    report={'step':'09 user-drawn long shoulders, low red boundary, rounded grey caps','parent':str(PARENT),'parent_sha256':digest,'collar':collar_report,'red':red,'gold':gold,'grey':grey,'trim':binding,
            'neck':previous['neck'],'cords':previous['cords'],'inherited_opening':previous['inherited_opening'],'references':[str(ref/'user_front_step09.png'),str(ref/'user_grey_shoulder_step09.png')],
            'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(coat);scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    render(scene,'front',(0,1,0));render(scene,'three_quarter',(.65,1,.12));render(scene,'shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43)
    assert s2.sha(PARENT)==digest;print('STEP09',json.dumps({'parent_sha256':digest,'red':red,'collar':collar_report}),flush=True)

if __name__=='__main__':main()
