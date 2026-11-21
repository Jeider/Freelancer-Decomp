"""Seated gold epaulettes fully wrap padding; the open collar lies over them."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
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
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_10';PARENT=TOP/'step_09/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — outward collar over gold'
EPAULETTES='14 Epaulettes — closed gold wrap to collar root'
PAD='16 Shoulder padding — fully enclosed by gold'
SHIRT=s9.SHIRT;LINING=s9.LINING

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def wrap_shoulders(old_ep,old_pad,coat,edit,archive,rig,names):
    pad=s8.clone(old_pad,PAD,edit,archive);me=pad.data;n=48;nr=22
    assert len(me.vertices)==2*n*nr
    # Extend the padding itself to the collar attachment. The gold and its
    # support share one complete fitted volume, without a floating canopy.
    for i,v in enumerate(me.vertices):
        side=1 if v.co.x>0 else -1;a=2*math.pi*(i%n)/n;inner=max(0,-math.cos(a))**1.35
        p=np.array(v.co);p[0]-=side*.068*inner
        p[1]+=(.100*max(0,math.sin(a))+.012*min(0,math.sin(a)))*inner
        p[2]+=.035*inner*(1-s3.smooth(.49,.558,p[2]))
        p[2]-=.032*inner*s3.smooth(.550,.600,p[2])
        # The inward end stops at the collar root; never grow a gold lobe
        # through the neckline. Retain the long front end below the lapel.
        if abs(p[1])<.145:p[0]=side*max(abs(p[0]),math.sqrt(max(0,.145**2-p[1]**2)))
        v.co=p
    s9.recalc(pad)
    surface=s8.SampleMesh(coat,names,lambda f:f.material_index!=4 and f.center.z>.45)
    skin=[s9.shoulder_skin(surface,np.array(v.co),names) for v in me.vertices]
    # Close the sculpted ends explicitly. A nonplanar 48-gon is not a sound
    # bottom for the raised inner shoulder; its arbitrary diagonals can fold.
    used_rings=19;indices=[side*n*nr+j*n+k for side in range(2) for j in range(used_rings) for k in range(n)]
    ps=[np.array(me.vertices[i].co) for i in indices];skin=[skin[i] for i in indices];faces=[];charts=[]
    for side in range(2):
        start=side*n*used_rings
        for j in range(used_rings-1):
            for k in range(n):
                a=start+j*n+k;b=start+j*n+(k+1)%n;faces.append([a,b,b+n,a+n]);charts.append([(k/n,j/(used_rings-1)),((k+1)/n,j/(used_rings-1)),((k+1)/n,(j+1)/(used_rings-1)),(k/n,(j+1)/(used_rings-1))])
        for top in (True,False):
            ids=[start+(0 if top else (used_rings-1)*n)+k for k in range(n)];q=np.mean([ps[i] for i in ids],axis=0)
            q[2]=(max(ps[i][2] for i in ids)+.001) if top else (min(ps[i][2] for i in ids)-.006)
            ci=len(ps);ps.append(q);w=np.mean([skin[i] for i in ids],axis=0);w[np.argsort(w)[:-4]]=0;w/=w.sum();skin.append(w)
            for k,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):
                aa=2*math.pi*k/n;bb=2*math.pi*(k+1)/n;faces.append([a,b,ci]);charts.append([(.5+.45*math.cos(aa),.5+.45*math.sin(aa)),(.5+.45*math.cos(bb),.5+.45*math.sin(bb)),(.5,.5)])
    new=bpy.data.meshes.new('Seated shoulder closed sections');new.from_pydata(ps,[],faces);new.materials.append(me.materials[0]);layer=new.uv_layers.new(name=me.uv_layers.active.name)
    for f,qs in zip(new.polygons,charts):
        f.use_smooth=True
        for li,q in zip(f.loop_indices,qs):layer.data[li].uv=q
    pad.data=new;me=new
    for name in names:pad.vertex_groups.new(name=name)
    s8.set_weights(pad,np.array(skin));s9.recalc(pad)
    gold=pad.copy();gold.data=pad.data.copy();edit.objects.link(gold);gold.name=EPAULETTES;gold.hide_render=False;gold.hide_viewport=False
    gold.data.materials.clear();gold.data.materials.append(old_ep.data.materials[0]);gold.data.uv_layers.active.name=old_ep.data.uv_layers.active.name
    normals=[np.array(v.normal) for v in me.vertices]
    for v,no in zip(gold.data.vertices,normals):v.co+=Vector(no*.0035)
    s9.recalc(gold)
    gold.data.materials.append(coat.data.materials[5])
    backing=[]
    for f in gold.data.polygons:
        p=np.array(f.center);r=np.linalg.norm(p[:2]);inward=float(np.dot(np.array(f.normal)[:2],p[:2]/max(r,1e-9)))
        if (len(f.vertices)==3 and f.normal.z<-.45) or (r<.170 and inward<-.40):f.material_index=1;backing.append(f.index)
    for v,g in zip(me.vertices,gold.data.vertices):v.co=g.co-g.normal*.002
    s9.recalc(pad)
    # One continuous circumference chart per shoulder, plus closed top/bottom
    # charts. Both shoulders retain the actual Dietrich gold texture.
    uv=gold.data.uv_layers.active
    for f in gold.data.polygons:
        if len(f.vertices)>4:
            for k,li in enumerate(f.loop_indices):
                a=2*math.pi*k/len(f.vertices);uv.data[li].uv=(.60+.27*math.cos(a),.25+.12*math.sin(a))
        else:
            for li in f.loop_indices:
                q=uv.data[li].uv.copy();uv.data[li].uv=(.30+.60*q.x,.12+.25*(1-q.y))
    native.move(old_ep,archive)
    gold['construction']='Closed gold shell follows and fully encloses the padded shoulder, extending inward to the collar root. The entire perimeter returns into the shell; no free canopy edge.'
    pad['construction']='Padded support extended to the collar root, fitted 2 mm inside the closed shell with identical skin weights.'
    return gold,pad,{'padding_vertex_count':len(me.vertices),'gold_offset_m':.0035,'padding_inset_m':.002,'same_topology_and_skin':True,'closed_shell':True,'inner_extension_m':.068,'front_inner_extension_m':.100,'inner_hem_rise_m':.035,'gold_material':gold.data.materials[0].name,'inner_return_backing_faces':backing}

def spread_collar(old,ep,edit,archive,prior):
    ob=s8.clone(old,GARMENT,edit,archive);me=ob.data;before=np.array([v.co[:] for v in me.vertices]);normals=[n.vector[:] for n in me.corner_normals];faces=prior['cut']['collar_faces'];rows=[]
    for k in range(0,len(faces),5):
        ff=[list(me.polygons[i].vertices) for i in faces[k:k+5]]
        if not rows:rows.append([ff[0][0]]+[f[1] for f in ff])
        rows.append([ff[0][3]]+[f[2] for f in ff])
    tree=BVHTree.FromPolygons([v.co[:] for v in ep.data.vertices],[list(f.vertices) for f in ep.data.polygons])
    fitted=[]
    for row in rows:
        hinge,roll,edge=[before[row[j]].copy() for j in (0,2,5)];side=1 if edge[0]>0 else -1;band=s3.smooth(.465,.535,edge[2])
        if band<1e-6:continue
        new_roll=roll+np.array([side*.009,(.004 if roll[1]>0 else -.006),.004])*band
        new_edge=edge+np.array([side*.025,(.010 if edge[1]>0 else -.008),.012])*band
        hit,no,fi,dist=tree.ray_cast(Vector((new_edge[0],new_edge[1],.8)),Vector((0,0,-1)))
        if hit is not None:
            new_edge[2]=(1-band)*new_edge[2]+band*(hit.z+.006);fitted.append(row[5])
        # A smooth rolled section: raised turn near the neck, falling edge
        # seated on the gold. No independently lifted outer collar points.
        rr=[hinge,.45*hinge+.55*new_roll,new_roll,
            .70*new_roll+.30*new_edge+np.array([0,0,.003]),
            .30*new_roll+.70*new_edge+np.array([0,0,.002]),new_edge]
        for j in range(1,6):me.vertices[row[j]].co=(1-band)*before[row[j]]+band*rr[j]
    # The falling front portions lie OUTSIDE the gold, while the shoulder
    # portions lie ABOVE it. Check the appropriate direction for each region.
    for row in rows:
        for j in range(2,6):
            i=row[j];q=me.vertices[i].co.copy()
            if q.y>.065:
                hit,no,fi,dist=tree.ray_cast(Vector((q.x,.5,q.z)),Vector((0,-1,0)))
                if hit is not None and q.y<hit.y+.008:q.y=hit.y+.008;fitted.append(i)
            elif q.y<-.065:
                hit,no,fi,dist=tree.ray_cast(Vector((q.x,-.5,q.z)),Vector((0,1,0)))
                if hit is not None and q.y>hit.y-.008:q.y=hit.y-.008;fitted.append(i)
            else:
                hit,no,fi,dist=tree.ray_cast(Vector((q.x,q.y,.8)),Vector((0,0,-1)))
                if hit is not None and q.z<hit.z+.008:q.z=hit.z+.008;fitted.append(i)
            f=s3.smooth(.045,.09,q.y)*s3.smooth(.49,.53,q.z)*(1-s3.smooth(.57,.60,q.z))*s3.smooth(.06,.10,abs(q.x))*(1-s3.smooth(.16,.19,abs(q.x)))
            q.y+=.028*f
            me.vertices[i].co=q
    me.update();changed={i for i,v in enumerate(me.vertices) if np.linalg.norm(np.array(v.co)-before[i])>1e-8}
    me.normals_split_custom_set([me.vertices[l.vertex_index].normal[:] if l.vertex_index in changed else normals[i] for i,l in enumerate(me.loops)])
    ob['construction']='Grey collar opens outwards above the epaulettes and drapes over their inward ends. Original neck sewing line and chest end retained.'
    return ob,{'changed_vertices':sorted(changed),'outside_gold_fitted_vertices':sorted(set(fitted)),'max_absolute_delta_m':np.max(abs(np.array([v.co[:] for v in me.vertices])-before),axis=0).tolist(),'hinge_vertices_unchanged':[r[0] for r in rows]}

def main():
    OUT.mkdir(parents=True,exist_ok=True);digest=s2.sha(PARENT);bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step 09 before closed shoulder wrap');archive.hide_viewport=archive.hide_render=True
    rig=bpy.data.objects['RIG — native Rheinland'];names=[b['name'] for b in native.load('body')['bones']];prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'));previous=json.loads((TOP/'step_09/report.json').read_text(encoding='utf8'))
    old={key:next(o for o in edit.objects if o.name.startswith(key)) for key in ('10 ','11 ','14 ','16 ')}
    ep,pad,wrapped=wrap_shoulders(old['14 '],old['16 '],old['10 '],edit,archive,rig,names)
    coat,collar=spread_collar(old['10 '],ep,edit,archive,prior);binding=s9.trim(old['11 '],coat,edit,archive,rig,names,prior)
    report={'step':'10 closed gold shoulder wrap and external spread collar','parent':str(PARENT),'parent_sha256':digest,'wrap':wrapped,'collar':collar,'trim':binding,
            'neck':previous['neck'],'cords':previous['cords'],'inherited_opening':previous['inherited_opening'],
            'references':[str(TOP/'source/art/hassler1.png'),str(TOP/'source/art/hassler2.png')],'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(coat);scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    if '--no-render' not in sys.argv:
        render(scene,'front',(0,1,0));render(scene,'three_quarter',(.65,1,.12));render(scene,'shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43)
    assert s2.sha(PARENT)==digest;print('STEP10',json.dumps({'collar_vertices':len(collar['changed_vertices']),'wrap':wrapped}),flush=True)

if __name__=='__main__':main()
