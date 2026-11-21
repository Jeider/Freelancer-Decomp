"""Sewn uniform, peeled gold front with red lining, independently ending collar."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
import hassler_native_step04 as s4
from hassler_step04_pattern import pattern
from hassler_step05_sleeves import sew
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_05';PARENT=TOP/'step_04/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — sleeves and opened gold front'
R=.18;H=.4

def neckline(g,lo,hi):
    return sorted(((s/R)%(2*math.pi),i) for i,(s,h) in g.param.items()
                  if abs(h-H)<1e-8 and lo-1e-6<=(s/R)%(2*math.pi)<=hi+1e-6)

def front_flap(g):
    """Peel the gold chest edge outward: gold exterior, red reverse."""
    top=neckline(g,.14,1.08);rows=[];start=len(g.faces)
    for theta,i in top:
        p=g.p[i];t=(theta-.14)/(1.08-.14)
        # The hinge belongs to the gold front below the collar, not to the grey
        # collar strip. A broader, almost rectangular corner folds down/right.
        bend=p+np.array([.004,.008,.006])
        edge=np.array([.075+.105*t,.208-.110*t,.427+.101*t])
        middle=.48*bend+.52*edge+np.array([0,.006,-.003])
        row=[i,g.vertex(.4*p+.6*bend),g.vertex(bend),g.vertex(middle),g.vertex(edge)]
        rows.append(row)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        for j in range(4):
            # The entire panel has GOLD on its outside. After it turns over,
            # Solidify's explicitly RED reverse is the visible side.
            mat=1
            uv=[(.30+k/len(rows)*.24,.66+j*.05),(.30+k/len(rows)*.24,.66+(j+1)*.05),
                (.30+(k+1)/len(rows)*.24,.66+(j+1)*.05),(.30+(k+1)/len(rows)*.24,.66+j*.05)]
            g.face([a[j],a[j+1],b[j+1],b[j]],mat,None)
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for row in (rows[0],rows[-1]):
        g.no_trim.update(tuple(sorted((row[j],row[j+1]))) for j in (0,1))
    return {'faces':list(range(start,len(g.faces))),'red_faces':[start+4*k+j for k in range(len(rows)-1) for j in (2,3)],
            'hinge_vertices':[i for t,i in top],'free_edge_vertices':[r[-1] for r in rows],
            'construction':'The upper right corner of the GOLD chest folds out; the visible reverse is red. It does not continue into the grey collar.'}

def collar(g):
    # Keep a separate free end above the turned gold chest. The gap in this
    # sewing line is intentional and visibly separates the two pieces of cloth.
    top=neckline(g,1.22,2*math.pi-.24);end=top[-1][0];rows=[];start=len(g.faces)
    first=top[0][0]
    roll=[(first,.085,.076,.597),(1.57,.095,0,.614),(2.20,.080,-.069,.614),
          (math.pi,0,-.089,.612),(4.10,-.080,-.065,.614),(4.71,-.095,0,.612),
          (5.18,-.091,.075,.587),(5.53,-.071,.128,.546),(5.83,-.035,.162,.492),(end,.006,.180,.459)]
    edge=[(first,.067,.126,.553),(1.57,.139,0,.565),(2.20,.111,-.094,.564),
          (math.pi,0,-.125,.562),(4.10,-.114,-.091,.564),(4.71,-.140,0,.563),
          (5.18,-.131,.095,.533),(5.53,-.095,.158,.481),(5.83,-.037,.196,.439),(end,.015,.207,.433)]
    for theta,i in top:
        p=g.p[i];r=s4.rail(roll,theta);e=s4.rail(edge,theta)
        radial=np.array([math.sin(theta),math.cos(theta),0.])
        rr=[i,g.vertex(.45*p+.55*r),g.vertex(r),g.vertex(.7*r+.3*e+radial*.003),
            g.vertex(.33*r+.67*e+np.array([0,.004*max(math.cos(theta),0),-.002])),g.vertex(e)]
        rows.append(rr);g.collar_join.append(i)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        for j in range(5):
            uv=[(.28+k/len(rows)*.25,.65+j*.05),(.28+k/len(rows)*.25,.65+(j+1)*.05),
                (.28+(k+1)/len(rows)*.25,.65+(j+1)*.05),(.28+(k+1)/len(rows)*.25,.65+j*.05)]
            g.face([a[j],a[j+1],b[j+1],b[j]],4,uv)
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for row in (rows[0],rows[-1]):
        g.no_trim.update(tuple(sorted((row[j],row[j+1]))) for j in (0,1))
    return {'faces':list(range(start,len(g.faces))),'hinge_vertices':[i for t,i in top],
            'free_edge_vertices':[r[-1] for r in rows], 'wearer_right_tip':g.p[rows[0][-1]].tolist(),
            'construction':'Grey collar sewn to the neck/left facing, with its own finished right end above the red chest flap.'}

def red_underlap(shirt,g,edit,rig,names,red):
    """Visible red coat layer behind the peeled gold facing; black throat stays."""
    tree=BVHTree.FromPolygons([v.co[:] for v in shirt.data.vertices],[list(f.vertices) for f in shirt.data.polygons])
    p=[];uv=[];skin=[];faces=[];nx=15;ny=12
    for j in range(ny):
        t=j/(ny-1)
        for i in range(nx):
            u=i/(nx-1);x=-.075+.225*u
            top=np.interp(x,[-.075,0,.06,.10,.15],[.492,.53,.555,.545,.52]);z=.405+(top-.405)*t
            hit,no,ti,dist=tree.ray_cast(Vector((x,.5,z)),Vector((0,-1,0)))
            if hit is None:raise AssertionError(('Underlap outside torso',x,z))
            q=np.array(hit)+np.array([0,.0018,0]);p.append(q);uv.append((u,t));skin.append(s3.torso_weights(g.surface,names,q,True))
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;faces.append([a,a+1,a+1+nx,a+nx])
    ob=upper.geometry('15 Red coat underlap — behind opened gold front',p,faces,uv,skin,red,edit,rig,names)
    # Winding faces +Y, consistent with the shirt and outer chest.
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if sum(f.normal.y for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data);bm.free()
    solid=ob.modifiers.new('Red inner coat cloth 1 mm','SOLIDIFY');solid.thickness=.001;solid.offset=-1
    ob['construction']='Red inner coat layer exposed behind the folded gold front. Separate from the black throat and grey collar.'
    return ob

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    cam=scene.camera;d=Vector(direction).normalized();cam.location=Vector(target)+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)

def sleeve_normals(ob,g,names):
    """Transfer native sleeve shading through the dense-to-native sewn joint."""
    me=ob.data;me.update();normals=[];changed=0
    limbs=[names.index(n) for n in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand')]
    for v in me.vertices:
        current=np.array(v.normal,dtype=float);strength=s3.smooth(.05,.55,sum(g.w[v.index][i] for i in limbs))
        if strength and abs(v.co.x)>.18:
            loc,no,idx,dist=g.surface.tree.find_nearest(v.co);tri=g.surface.faces[idx]
            w=np.array(barycentric_transform(loc,*[Vector(g.surface.p[i]) for i in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
            w=np.maximum(w,0);w/=w.sum();donor=w@g.surface.n[tri];donor/=max(np.linalg.norm(donor),1e-8)
            if np.dot(current,donor)>.15:
                current=current*(1-strength*.94)+donor*strength*.94;current/=max(np.linalg.norm(current),1e-8);changed+=1
        normals.append(current)
    me.normals_split_custom_set([normals[l.vertex_index] for l in me.loops])
    ob['sleeve_normals']='Barycentric transfer from actual native body normals, blended by arm skin influence across the sewn shoulder'
    return changed

def additional_views(scene):
    scene.frame_set(1)
    render(scene,'back',(0,-1,.03));render(scene,'side',(1,0,.02))
    render(scene,'collar_close',(.35,1,.18),(0,.02,1.53),.64)
    render(scene,'fold_side',(.90,1,.1),(.025,.07,1.50),.50)
    scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=s2.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland']
    source=native.load('body');names=[b['name'] for b in source['bones']];surface=upper.Surface(source)
    edit=bpy.data.collections['EDIT — native costume upper study']
    oldbase=bpy.data.objects['00 Native sleeves and lower body']
    oldep=next(ob for ob in edit.objects if ob.name.startswith('14 '));oldcord=next(ob for ob in edit.objects if ob.name.startswith('13 '))
    archive=native.collection('ARCHIVE — step 04 separate sleeves and collar flap');archive.hide_viewport=archive.hide_render=True
    for ob in list(edit.objects):native.move(ob,archive)
    mats=s3.make_materials()
    for m in mats:m.name=m.name.replace('03','05')
    side=mats[0].copy();side.name='Hassler 05 — rear dart panel';mats.append(side)
    g=s3.Garment(surface,names,rig,edit,mats)
    params,faces,layout=pattern(R,H);mapping={}
    for i,(s,h) in enumerate(params):
        idx=g.vertex(s3.shell_point(s,h));mapping[i]=idx;g.param[idx]=(float(s),float(h))
    for material,ids in faces:
        uv=None
        if material==2:uv=[(.39+(abs(params[i][0])-.125)/.270*.43,.11+(params[i][1]-.337)/.063*.22) for i in ids]
        if material==6:uv=[g.default_uv(g.p[mapping[i]],0) for i in ids]
        g.face([mapping[i] for i in ids],material,uv)
    sleeves,keep=sew(g,oldbase,names)
    flap=front_flap(g);grey=collar(g)
    garment=g.build();garment.name=GARMENT
    normal_count=sleeve_normals(garment,g,names)
    # Explicit reverse materials on actual thickness: red inside gold/green,
    # gold behind the outward-facing red flap. The collar has its own grey back.
    offset=len(garment.data.materials)
    reverse=[3,3,3,1,4,5,3]+list(range(7,offset))
    for i in reverse:garment.data.materials.append(mats[i])
    solid=next(m for m in garment.modifiers if m.type=='SOLIDIFY');solid.material_offset=offset
    garment['construction']='One sewn coat with continuous sleeves; gold right chest peeled to expose red reverse; independently ending grey collar.'
    garment['shoulder_stitch_vertices']=json.dumps([s['shoulder_stitch_vertices'] for s in sleeves])
    garment['forearm_stitch_vertices']=json.dumps([s['native_forearm_stitch_vertices'] for s in sleeves])
    garment['flap_red_faces']=flap['red_faces'];garment['collar_faces']=grey['faces']
    trim=s3.piping(garment,g,mats[3],edit,rig,names)
    # Keep the lower native body as the original editable source topology.
    base=oldbase.copy();base.data=oldbase.data.copy();edit.objects.link(base);base.name='00 Native lower body and belt'
    bm=bmesh.new();bm.from_mesh(base.data);bm.faces.ensure_lookup_table()
    keep=set(keep);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in keep],context='FACES_ONLY');bm.to_mesh(base.data);bm.free()
    shirt=s3.inner_shirt(surface,rig,names,edit,mats[5],mats[0],garment)
    for v in shirt.data.vertices:
        if v.co.z<.18:v.co.z=.211;v.co.y*=.70
    red_underlap(shirt,g,edit,rig,names,mats[3])
    for old,name in ((oldep,'14 Projecting epaulettes — retained fit'),(oldcord,'13 Aiguillette — retained fit')):
        ob=old.copy();ob.data=old.data.copy();edit.objects.link(ob);ob.name=name
    scene.cycles.samples=32;scene.render.resolution_x=1000;scene.render.resolution_y=1000
    views=[('front',(0,1,0)),('three_quarter',(.65,1,.12))]
    for label,d in views:render(scene,label,d)
    if '--quick' not in sys.argv:additional_views(scene)
    upper.dump(OUT/'pattern.json',layout)
    report={'step':'05 sewn sleeves, opened GOLD front, independent grey collar','parent':str(PARENT),'parent_sha256':parent_hash,
            'sleeves':sleeves,'flap':flap,'collar':grey,'trim':trim,'reverse_material_offset':offset,'native_sleeve_normals_transferred_vertices':normal_count,
            'red_underlap_visible':True,'head_hands_rig_unchanged':True,'game_installed':False,'game_animations_validated':False,
            'user_correction':'Gold tunic opens like a wrapper: red inside and red behind it. Grey collar belongs to a different cloth section and has its own end. Sleeves must read as one uniform.'}
    upper.dump(OUT/'report.json',report)
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(garment);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    assert s2.sha(PARENT)==parent_hash
    print(json.dumps({'step':5,'sleeve_stitches':[len(s['shoulder_stitch_vertices']) for s in sleeves],
                      'flap_faces':len(flap['faces']),'collar_faces':len(grey['faces'])}),flush=True)

if __name__=='__main__':
    if '--views' in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');additional_views(bpy.context.scene)
    else:main()
