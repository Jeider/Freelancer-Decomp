"""Continue the LEFT hanging collar into the released cross-front tunic panel.

The right shoulder is the fastening location, not the origin of an independent
lapel. Step 05's sewn sleeves, cuff UVs and native transferred shading are kept.
"""
import sys,json,math
from pathlib import Path
import bpy,numpy as np
from types import SimpleNamespace
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
import hassler_native_step05 as s5
from hassler_step04_pattern import pattern
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_06';PARENT=TOP/'step_05/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — left collar into released front'
R=.18;H=.4

def inherited_shell(old,report,rig,edit,names,surface):
    me=old.data;count=report['reverse_material_offset']
    mats=list(me.materials[:count]);g=s3.Garment(surface,names,rig,edit,mats)
    g.p=[np.array(v.co,dtype=float) for v in me.vertices];g.w=[]
    for v in me.vertices:
        row=np.zeros(len(names))
        for a in v.groups:row[names.index(old.vertex_groups[a.group].name)]=a.weight
        g.w.append(row)
    g.ids={tuple(np.round(p,7)):i for i,p in enumerate(g.p)}
    removed=set(report['flap']['faces']+report['collar']['faces']);uv=me.uv_layers.active
    kept=[]
    for f in me.polygons:
        if f.index in removed:continue
        g.face(list(f.vertices),f.material_index,[tuple(uv.data[li].uv) for li in f.loop_indices]);kept.append(f.index)
    params,_,_=pattern(R,H)
    for s,h in params:
        k=tuple(np.round(s3.shell_point(s,h),7))
        if k in g.ids:g.param[g.ids[k]]=(float(s),float(h))
    changed=[]
    # The gold front itself opens below the fixed shoulder fastening. Reduce
    # only its upper right neckline, fading the change into the chest fabric.
    for i,(s,h) in g.param.items():
        theta=s/R
        if -.12<theta<1.32:
            taper=s3.smooth(-.12,.35,theta)*(1-s3.smooth(1.05,1.32,theta))
            d=.025*taper*s3.smooth(.31,.40,h)*(1-s3.smooth(.12,.16,abs(g.p[i][0])))
            if d>1e-8:g.p[i][2]-=d;changed.append(i)
    g.ids={tuple(np.round(p,7)):i for i,p in enumerate(g.p)}
    # Preserve the non-decorative native forearm joins and bracer transitions.
    for mat,f in g.faces:
        for a,b in zip(f,f[1:]+f[:1]):
            if min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32:
                g.no_trim.add(tuple(sorted((a,b))))
    return g,kept,changed

def continuous_turn(g):
    top=s5.neckline(g,1.22,2*math.pi-.24);first=top[0][0];end=top[-1][0]
    roll=[(first,.085,.076,.597),(1.57,.095,0,.614),(2.20,.080,-.069,.614),
          (math.pi,0,-.089,.612),(4.10,-.080,-.065,.614),(4.71,-.095,0,.612),
          (5.18,-.091,.075,.587),(5.53,-.071,.128,.546),(5.83,-.035,.162,.492),(end,.006,.180,.459)]
    edge=[(first,.067,.126,.553),(1.57,.139,0,.565),(2.20,.111,-.094,.564),
          (math.pi,0,-.125,.562),(4.10,-.114,-.091,.564),(4.71,-.140,0,.563),
          (5.18,-.131,.095,.533),(5.53,-.095,.158,.481),(5.83,-.037,.196,.439),(end,.015,.207,.433)]
    rows=[];collar_start=len(g.faces)
    for theta,i in top:
        p=g.p[i];r=s4.rail(roll,theta);e=s4.rail(edge,theta);radial=np.array([math.sin(theta),math.cos(theta),0.])
        rr=[i,g.vertex(.45*p+.55*r),g.vertex(r),g.vertex(.7*r+.3*e+radial*.003),
            g.vertex(.33*r+.67*e+np.array([0,.004*max(math.cos(theta),0),-.002])),g.vertex(e)]
        rows.append(rr);g.collar_join.append(i)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        for j in range(5):
            uv=[(.28+k/len(rows)*.25,.65+j*.05),(.28+k/len(rows)*.25,.65+(j+1)*.05),
                (.28+(k+1)/len(rows)*.25,.65+(j+1)*.05),(.28+(k+1)/len(rows)*.25,.65+j*.05)]
            g.face([a[j],a[j+1],b[j+1],b[j]],4,uv)
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    collar_faces=list(range(collar_start,len(g.faces)))
    # Continue across centre chest from the SAME cross-section at the long left
    # collar end. The hanging edge cannot be a detached right shoulder patch.
    join=rows[-1];front=[(end,top[-1][1])]
    for i,(s,h) in g.param.items():
        a=(s/R)%(2*math.pi)
        if abs(h-H)>1e-8:continue
        if a>end+1e-6:front.append((a,i))
        elif a<=1.08+1e-6:front.append((a+2*math.pi,i))
    front=sorted(set(front));limit=front[-1][0];frows=[join];flap_start=len(g.faces)
    joins=[]
    for theta,i in front[1:]:
        u=(theta-end)/(limit-end);p=g.p[i]
        # An asymmetric cross-front fold, with the detached fastening corner
        # visibly below its old shoulder position. Broad cloth, no new clasp.
        r=s4.rail([(0,.006,.180,.459),(.25,.040,.188,.452),
                   (.58,.090,.162,.491),(1,.116,.110,.542)],u)
        e=s4.rail([(0,.015,.207,.433),(.25,.061,.216,.423),
                   (.58,.123,.196,.444),(1,.187,.124,.508)],u)
        radial=np.array([math.sin(theta),math.cos(theta),0.])
        rr=[i,g.vertex(.45*p+.55*r),g.vertex(r),g.vertex(.7*r+.3*e+radial*.003),
            g.vertex(.33*r+.67*e+np.array([0,.004*max(math.cos(theta),0),-.002])),g.vertex(e)]
        frows.append(rr);joins.append(i)
    for k,(a,b) in enumerate(zip(frows,frows[1:])):
        for j in range(5):
            # Entire exterior remains gold. Its true reversed side is red.
            # Use a non-degenerate fabric chart carried across this full strip.
            uv=[(.38+k/len(frows)*.20,.25+j*.07),(.38+k/len(frows)*.20,.25+(j+1)*.07),
                (.38+(k+1)/len(frows)*.20,.25+(j+1)*.07),(.38+(k+1)/len(frows)*.20,.25+j*.07)]
            g.face([a[j],a[j+1],b[j+1],b[j]],1,uv)
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for a,b in zip(join,join[1:]):g.no_trim.add(tuple(sorted((a,b))))
    for row in (rows[0],frows[-1]):
        g.no_trim.update(tuple(sorted((row[j],row[j+1]))) for j in (0,1))
    return {'collar_faces':collar_faces,'front_faces':list(range(flap_start,len(g.faces))),
            'red_reverse_faces':[flap_start+5*k+j for k in range(len(frows)-1) for j in (2,3,4)],
            'left_collar_to_front_shared_section':join,'collar_hinge':[i for a,i in top],
            'front_hinge':[i for a,i in front],'front_free_edge':[r[-1] for r in frows],
            'fixed_right_fastening_reference':[.187,.099,.566],
            'released_right_corner':g.p[frows[-1][-1]].tolist(),
            'construction':'Long wearer-left collar edge continues into the same turned cross-front panel. Right shoulder is the released fastening corner; old independent right flap removed.'}

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    cam=scene.camera;d=Vector(direction).normalized();cam.location=Vector(target)+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)

def views(scene,quick=False):
    scene.frame_set(1)
    for label,d in [('front',(0,1,0)),('three_quarter',(.65,1,.12))]:render(scene,label,d)
    if quick:return
    render(scene,'back',(0,-1,.03));render(scene,'side',(1,0,.02))
    render(scene,'collar_close',(.35,1,.18),(0,.02,1.53),.64)
    render(scene,'fold_side',(.90,1,.1),(.025,.07,1.50),.50)
    scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)

def fitted_red_underlap(edit,archive,rig,names,red):
    old=next(o for o in edit.objects if o.name.startswith('15 '));native.move(old,archive)
    shirt=next(o for o in edit.objects if o.name.startswith('12 '));me=shirt.data;me.calc_loop_triangles()
    p=np.array([v.co[:] for v in me.vertices]);n=np.array([v.normal[:] for v in me.vertices]);w=np.zeros((len(p),len(names)))
    for v in me.vertices:
        for a in v.groups:w[v.index,names.index(shirt.vertex_groups[a.group].name)]=a.weight
    actual=SimpleNamespace(p=p,n=n,w=w,faces=[list(t.vertices) for t in me.loop_triangles])
    contour=[(-.075,.405),(.150,.405),(.150,.520),(.100,.545),(.060,.555),(0,.530),(-.075,.492)]
    ob=upper.panel('15 Red coat underlap — exact sewn backing',contour,True,actual,red,edit,rig,names,offset=.0025,texture_kind='red')
    tree=BVHTree.FromPolygons(p.tolist(),actual.faces,all_triangles=True);normals=[]
    for v in ob.data.vertices:
        point=v.co-Vector((0,.0025,0));hit,no,idx,dist=tree.find_nearest(point);tri=actual.faces[idx]
        b=np.array(barycentric_transform(hit,*[Vector(p[i]) for i in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
        b=np.maximum(b,0);b/=b.sum();normal=b@n[tri];normal/=max(np.linalg.norm(normal),1e-9);normals.append(normal)
    ob.data.normals_split_custom_set([normals[l.vertex_index] for l in ob.data.loops])
    ob['construction']='Red lining clipped to the actual black inner torso triangles; shared skin interpolation and constant forward clearance prevent gaps after the outer panel opens.'
    return {'source_shirt':shirt.name,'contour_xz':contour,'clearance_m':.0025,'faces':len(ob.data.polygons)}

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=s2.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    old=bpy.data.objects[s5.GARMENT];old_report=json.loads((TOP/'step_05/report.json').read_text(encoding='utf8'))
    source=native.load('body');names=[b['name'] for b in source['bones']];rig=bpy.data.objects['RIG — native Rheinland'];surface=upper.Surface(source)
    edit=bpy.data.collections['EDIT — native costume upper study']
    oldtrim=next(o for o in edit.objects if o.name.startswith('11 '))
    archive=native.collection('ARCHIVE — step 05 independent right flap');archive.hide_viewport=archive.hide_render=True
    native.move(old,archive);native.move(oldtrim,archive)
    g,kept,changed=inherited_shell(old,old_report,rig,edit,names,surface)
    seam=continuous_turn(g);garment=g.build();garment.name=GARMENT
    # Keep exactly the successful sleeve shading and unaffected native parts.
    donor={}
    for loop,no in zip(old.data.loops,old.data.corner_normals):donor.setdefault(loop.vertex_index,np.array(no.vector))
    keptverts={v for fi in kept for v in old.data.polygons[fi].vertices};changed=set(changed)
    normals=[];preserved_normals=0
    for loop in garment.data.loops:
        i=loop.vertex_index
        if i in keptverts and i not in changed and not(abs(g.p[i][0])<.15 and g.p[i][2]>.43 and g.p[i][1]>.05):
            normals.append(donor[i]);preserved_normals+=1
        else:normals.append(garment.data.vertices[i].normal[:])
    garment.data.normals_split_custom_set(normals)
    count=len(garment.data.materials);reverse=[3,3,3,1,4,5,3]+list(range(7,count))
    for i in reverse:garment.data.materials.append(g.mats[i])
    solid=next(m for m in garment.modifiers if m.type=='SOLIDIFY');solid.material_offset=count
    garment['construction']=seam['construction'];garment['left_collar_to_front_shared_section']=seam['left_collar_to_front_shared_section']
    garment['shoulder_stitch_vertices']=old['shoulder_stitch_vertices'];garment['forearm_stitch_vertices']=old['forearm_stitch_vertices']
    trim=s3.piping(garment,g,g.mats[3],edit,rig,names)
    underlap=fitted_red_underlap(edit,archive,rig,names,g.mats[3])
    guides=native.collection('REFERENCE — fastening construction');guides.hide_render=guides.hide_viewport=True
    for name,p in [('Right shoulder fastening — closed-position reference',seam['fixed_right_fastening_reference']),
                   ('Released corner — current position',seam['released_right_corner'])]:
        ob=bpy.data.objects.new(name,None);guides.objects.link(ob);ob.parent=rig;ob.location=p;ob.empty_display_size=.012
    scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    views(scene,'--quick' in sys.argv)
    report={'step':'06 left collar continues into released cross-front panel','parent':str(PARENT),'parent_sha256':parent_hash,
            'seam':seam,'sleeves':old_report['sleeves'],'retained_parent_face_indices':kept,
            'lowered_front_neckline_vertices':sorted(changed),'trim':trim,'underlap':underlap,'reverse_material_offset':count,
            'preserved_parent_normal_corners':preserved_normals,'game_installed':False,'game_animations_validated':False,
            'user_correction':'Long hanging collar on the wearer-left continues into the opened tunic. The wearer-right shoulder is the unfastened corner, not a separate right lapel.'}
    upper.dump(OUT/'report.json',report)
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(garment);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    assert s2.sha(PARENT)==parent_hash
    print(json.dumps({'step':6,'shared_collar_front_vertices':len(seam['left_collar_to_front_shared_section']),
                      'front_faces':len(seam['front_faces']),'right_corner':seam['released_right_corner']}),flush=True)

if __name__=='__main__':main()
