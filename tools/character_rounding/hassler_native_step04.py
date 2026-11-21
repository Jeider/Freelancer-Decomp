"""Hassler's unbuttoned uniform: hanging red facing and continuous collar.

The user-supplied nineteenth-century uniform explains the cut, not the palette.
The original Hassler art still controls silhouette and asymmetric free edges.
"""
import sys,json,math,copy
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
from hassler_step04_pattern import pattern
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_04';PARENT=TOP/'step_03/hassler_native_upper.blend'
R=.18;H=.4
GARMENT='10 Open tunic — turned red facing and hanging collar'

def rail(keys,t):
    a=np.array(keys);k=a[:,0];v=a[:,1:]
    slopes=np.gradient(v,k,axis=0)
    i=max(0,min(len(k)-2,np.searchsorted(k,t)-1));d=k[i+1]-k[i];u=(t-k[i])/d
    return (2*u**3-3*u**2+1)*v[i]+(u**3-2*u*u+u)*d*slopes[i]+(-2*u**3+3*u*u)*v[i+1]+(u**3-u*u)*d*slopes[i+1]

def folded_front(g):
    """Extend the actual neckline, then turn its free cloth edge out and down.

    On the unbuttoned right this is a broad red reverse of the tunic facing.
    Behind the neck and down the left it becomes the grey folded collar.
    Every hinge vertex is shared with the coat; there is no red patch beneath.
    """
    end=2*math.pi-.24
    top=[((s/R)%(2*math.pi),i) for i,(s,h) in g.param.items() if abs(h-H)<1e-8]
    top=sorted((a,i) for a,i in top if .14-1e-7<=a<=end+1e-7)
    # Inner turning line follows the neck at the back, and falls towards the
    # sternum in front. The previous high collar on both sides is discarded.
    roll_keys=[(.14,.018,.185,.469),(.30,.036,.178,.491),(.55,.066,.155,.528),
               (.85,.084,.116,.568),(1.08,.088,.074,.599),(1.57,.095,0,.614),
               (2.20,.080,-.069,.614),(math.pi,0,-.089,.612),
               (4.10,-.080,-.065,.614),(4.71,-.095,0,.612),
               (5.18,-.091,.075,.587),(5.53,-.071,.128,.546),
               (5.83,-.035,.162,.492),(end,.006,.180,.459)]
    edge_keys=[(.14,.078,.207,.433),(.30,.098,.199,.458),(.55,.128,.170,.495),
               (.82,.165,.122,.533),(1.08,.143,.070,.565),(1.57,.139,0,.565),
               (2.20,.111,-.094,.564),(math.pi,0,-.125,.562),
               (4.10,-.114,-.091,.564),(4.71,-.140,0,.563),
               (5.18,-.131,.095,.533),(5.53,-.095,.158,.481),
               (5.83,-.037,.196,.439),(end,.015,.207,.433)]
    rows=[];angles=[];red_faces=[];grey_faces=[];red_vertices=set()
    for theta,idx in top:
        p=g.p[idx];roll=rail(roll_keys,theta);edge=rail(edge_keys,theta)
        radial=np.array([math.sin(theta),math.cos(theta),0.])
        # Explicit bend: coat rises to the fold, rounds over it, and descends
        # under gravity. The wide right free edge is visibly clear of the coat.
        q1=.45*p+.55*roll
        q2=roll
        q3=.70*roll+.30*edge+radial*.003
        q4=.33*roll+.67*edge+np.array([0,.004*max(math.cos(theta),0),-.002])
        section=[p,q1,q2,q3,q4,edge]
        ids=[idx]+[g.vertex(q) for q in section[1:]]
        rows.append(ids);angles.append(theta);g.collar_join.append(idx)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        theta=(angles[k]+angles[k+1])*.5
        visible=3 if theta<.82 else 4
        for j in range(5):
            # The upstanding inside of the right fold keeps the native gold
            # outside; the part turned towards the viewer exposes red facing.
            mat=1 if visible==3 and j<2 else visible
            uv=[(.28+k/(len(rows)-1)*.25,.65+j/5*.25),
                (.28+k/(len(rows)-1)*.25,.65+(j+1)/5*.25),
                (.28+(k+1)/(len(rows)-1)*.25,.65+(j+1)/5*.25),
                (.28+(k+1)/(len(rows)-1)*.25,.65+j/5*.25)]
            if mat==1:uv=None
            ids=[a[j],a[j+1],b[j+1],b[j]];fi=len(g.faces);g.face(ids,mat,uv)
            if mat==3:red_faces.append(fi);red_vertices.update(ids)
            elif mat==4:grey_faces.append(fi)
        # No fake red sewn line on the actual hinge beneath the turned fabric.
        g.no_trim.add(tuple(sorted((a[0],b[0]))))
    # Avoid a red line between the grey and red faces: this is a fabric colour
    # transition on the same fold, not another rolled border.
    for a,theta in zip(rows,angles):
        if abs(theta-.82)<1e-6:
            g.no_trim.update(tuple(sorted((a[j],a[j+1]))) for j in range(5))
    for endrow in (rows[0],rows[-1]):
        g.no_trim.update(tuple(sorted((endrow[j],endrow[j+1]))) for j in (0,1))
    return {'sewn_sections':len(rows),'red_faces':red_faces,'grey_faces':grey_faces,
            'red_vertex_ids':sorted(red_vertices),'profile_rows':6,
            'roll_rail':roll_keys,'free_edge_rail':edge_keys,
            'construction':'One unbuttoned right front folded down; red is its reverse, not shirt or applique. Grey collar continues around the neck to a hanging left end.'}

def epaulettes(edit,rig,surface,names):
    source=bpy.data.objects['02 Epaulettes — Reichman source geometry']
    ob=source.copy();ob.data=source.data.copy();edit.objects.link(ob)
    ob.name='14 Projecting epaulettes — Dietrich fabric';ob.hide_render=False;ob.hide_viewport=False
    # Restored native shoulder silhouette. Slightly closer to the continuous
    # yoke than step 02; it seats into the gold shoulder instead of hovering.
    for v in ob.data.vertices:
        v.co.x-=.014 if v.co.x>0 else -.014;v.co.z-=.024
    for mod in ob.modifiers:
        if mod.type=='SOLIDIFY':
            mod.thickness=.008;mod.name='Grey shoulder-board backing 8 mm'
    if ob.data.has_custom_normals:
        native.activate(ob);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    ob['construction']='Restored projecting native Reichman shoulder boards with the step-02 Dietrich UV transfer; fitted into the continuous gold yoke.'
    return ob

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    cam=scene.camera;d=Vector(direction).normalized();cam.location=Vector(target)+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=s2.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['RIG — native Rheinland']
    source=native.load('body');names=[b['name'] for b in source['bones']];surface=upper.Surface(source)
    edit=bpy.data.collections['EDIT — native costume upper study']
    archive=native.collection('ARCHIVE — step 03 closed front');archive.hide_viewport=archive.hide_render=True
    for ob in list(edit.objects):
        if ob.name!='00 Native sleeves and lower body':native.move(ob,archive)
    mats=s3.make_materials()
    for mat in mats:mat.name=mat.name.replace('03','04')
    side=mats[0].copy();side.name='Hassler 04 — native-inspired rear dart panel';mats.append(side)
    g=s3.Garment(surface,names,rig,edit,mats)
    params,faces,layout=pattern(R,H);mapping={}
    for i,(s,h) in enumerate(params):
        idx=g.vertex(s3.shell_point(s,h));mapping[i]=idx;g.param[idx]=(float(s),float(h))
    for material,ids in faces:
        uv=None
        if material==2:uv=[(.39+(abs(params[i][0])-.125)/.270*.43,.11+(params[i][1]-.337)/.063*.22) for i in ids]
        if material==6:uv=[g.default_uv(g.p[mapping[i]],0) for i in ids]
        g.face([mapping[i] for i in ids],material,uv)
    fold=folded_front(g);garment=g.build();garment.name=GARMENT
    garment['construction']=fold['construction'];garment['turned_red_faces']=fold['red_faces']
    garment['turned_grey_faces']=fold['grey_faces'];garment['red_face_is_part_of_tunic']=True
    # Editable selections remain distinct from deform groups.
    garment['edit_red_vertex_ids']=fold['red_vertex_ids']
    trim=s3.piping(garment,g,mats[3],edit,rig,names)
    shirt=s3.inner_shirt(surface,rig,names,edit,mats[5],mats[0],garment)
    # Tuck the lowest lining row above the belt's visible back edge.
    for v in shirt.data.vertices:
        if v.co.z<.18:v.co.z=.211;v.co.y*=.70
    ep=epaulettes(edit,rig,surface,names)
    # Keep the secondary cord at its previous fit, without embellishment.
    old=bpy.data.objects['13 Aiguillette — fitted to tunic volume'];cord=old.copy();cord.data=old.data.copy();edit.objects.link(cord)
    cord.name='13 Aiguillette — previous fit';cord.hide_render=False;cord.hide_viewport=False
    scene.cycles.samples=32;scene.render.resolution_x=1000;scene.render.resolution_y=1000
    views=[('front',(0,1,0)),('three_quarter',(.65,1,.12)),('back',(0,-1,.03)),('side',(1,0,.02))]
    if '--quick' in sys.argv:views=views[:2]
    for label,d in views:render(scene,label,d)
    if '--quick' not in sys.argv:
        render(scene,'collar_close',(.35,1,.18),(0,.02,1.53),.64)
        render(scene,'fold_side',(.90,1,.1),(.025,.07,1.50),.50)
        scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    upper.dump(OUT/'pattern.json',layout)
    report={'step':'04 unbuttoned uniform and hanging facing','parent':str(PARENT),'parent_sha256':parent_hash,
            'fold':fold,'trim':trim,'projecting_epaulettes_restored':True,
            'shoulder_texture':'Dietrich native shoulder artwork, transferred in step 02',
            'back':'Gold Y and stem from art; red curved side darts based on native elite rear seams',
            'source_uniform_reference':str(TOP/'source/open_uniform_study/user_uniform_reference.png'),
            'head_hands_base_and_rig_unchanged':True,'game_installed':False,'game_animations_validated':False,
            'reference_interpretation':'Manual art interpretation; red is the turned uniform facing, explicitly not a separate red shirt. User uniform photograph clarifies the asymmetric buttoned cut.'}
    upper.dump(OUT/'report.json',report)
    doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(garment)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    assert s2.sha(PARENT)==parent_hash
    print(json.dumps({'step':4,'sewn_sections':len(g.collar_join),'red_faces':len(fold['red_faces']),'parent_unchanged':True}),flush=True)

if __name__=='__main__':main()
