"""Thin Dietrich-like gold shoulders, inward rolled hems and brocade collar lining."""
import sys,json,math
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
import hassler_native_step04 as s4
import hassler_native_step08 as s8
import hassler_native_step09 as s9
import hassler_native_step10 as s10
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_11';PARENT=TOP/'step_10/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — grey collar with brocade lining'
EPAULETTES='14 Epaulettes — thin gold with inward rolled hem'
PAD='16 Grey shoulder pads — exposed below gold hem'
GUSSET='17 Gold cloth — closes collar to shoulder'
SHIRT=s10.SHIRT;LINING=s10.LINING

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def point(u,v,side):
    t=2*v-1;front=max(0,t);back=max(0,-t);roof=1-t*t
    xi=.130-.052*front*front-.010*back*back;xo=.286-.048*front*front-.025*back*back
    x=xi+(xo-xi)*u;y=(.137-.006*u)*front+(-.093-.018*u)*back
    crown=.558+.039*math.sin(math.pi*u/2)
    zfront=float(s4.rail([(0,.532),(.50,.520),(.72,.527),(1,.550)],u)[0]);zback=.548+.014*u
    z=crown*roof+(zfront if v>=.5 else zback)*(1-roof)-.025*(1-u)**2*back
    return np.array([side*x,y,z])

def axes(u,v,side):
    e=1e-4;du=(point(u+e,v,side)-point(u-e,v,side))/(2*e);dv=(point(u,v+e,side)-point(u,v-e,side))/(2*e)
    no=np.cross(du,dv)*side;no/=np.linalg.norm(no)
    return du,dv,no

def chart(u,v):return np.array([.30+.60*v,.25+(u-.5)*.30*math.sqrt(1-((v-.5)*1.5)**2)])

def shoulders(old_ep,old_pad,coat,edit,archive,rig,names):
    nu=19;nv=25;radius=.0025;ps=[];uv=[];ws=[];fs=[];padp=[];paduv=[];padws=[];padfs=[];grids={};rims={}
    surface=s8.SampleMesh(coat,names,lambda f:f.material_index!=4 and f.center.z>.45)
    for side in (1,-1):
        top=[];bottom=[];normals=[];parameters=[];skin=[]
        for j,v in enumerate(np.linspace(0,1,nv)):
            for i,u in enumerate(np.linspace(0,1,nu)):
                p=point(u,v,side);no=axes(u,v,side)[2]
                top.append(p);bottom.append(p-2*radius*no);normals.append(no);parameters.append((u,v));skin.append(s9.shoulder_skin(surface,p,names))
        start=len(ps);count=len(top)
        for pp in (top,bottom):
            for p,q,w in zip(pp,parameters,skin):ps.append(p);uv.append(chart(*q));ws.append(w)
        for j in range(nv-1):
            for i in range(nu-1):
                a=j*nu+i;ids=[a,a+1,a+nu+1,a+nu]
                fs.append([start+k for k in (ids if side>0 else ids[::-1])]);fs.append([start+count+k for k in (ids[::-1] if side>0 else ids)])
        boundary=list(range(nu))+[j*nu+nu-1 for j in range(1,nv)]+list(range((nv-1)*nu+nu-2,(nv-1)*nu-1,-1))+[j*nu for j in range(nv-2,0,-1)]
        rings=[[start+k for k in boundary]]
        for angle in np.linspace(0,math.pi,7)[1:-1]:
            ring=[]
            for k in boundary:
                u,v=parameters[k];du,dv,no=axes(u,v,side);out=np.zeros(3);quv=np.zeros(2)
                if u==0:out-=du/np.linalg.norm(du);quv+=np.array([0,-1])
                if u==1:out+=du/np.linalg.norm(du);quv+=np.array([0,1])
                if v==0:out-=dv/np.linalg.norm(dv);quv+=np.array([-1,0])
                if v==1:out+=dv/np.linalg.norm(dv);quv+=np.array([1,0])
                out-=no*np.dot(no,out);out/=np.linalg.norm(out);quv/=np.linalg.norm(quv)
                p=top[k]+out*radius*math.sin(angle)-no*radius*(1-math.cos(angle))
                ring.append(len(ps));ps.append(p);uv.append(chart(u,v)+quv*radius*angle*1.7);ws.append(skin[k])
            rings.append(ring)
        # The return joins the complete underside. No free/flapping gold edge.
        rings.append([start+count+k for k in boundary])
        for aa,bb in zip(rings,rings[1:]):
            for k in range(len(aa)):
                ids=[aa[k],aa[(k+1)%len(aa)],bb[(k+1)%len(bb)],bb[k]];fs.append(ids)
        grids[str(side)]=[list(range(start+j*nu,start+(j+1)*nu)) for j in range(nv)];rims[str(side)]=rings
        # A fitted grey support follows the underside then closes into the sleeve.
        # Its lower wall is intentionally visible, unlike step10's all-gold volume.
        pstart=len(padp);ptop=[point(.32+.68*u,v,side)-axes(.32+.68*u,v,side)[2]*.009 for u,v in parameters];plow=[]
        pskin=[s9.shoulder_skin(surface,p,names) for p in ptop]
        for p in ptop:
            q=p.copy();q[0]=side*(.205+(abs(p[0])-.205)*.68);q[1]=.012+(p[1]-.012)*.68
            q[2]=.493;plow.append(q)
        for pp in (ptop,plow):
            for p,q,w in zip(pp,parameters,pskin):padp.append(p);paduv.append(q);padws.append(w)
        for j in range(nv-1):
            for i in range(nu-1):
                a=j*nu+i;ids=[a,a+1,a+nu+1,a+nu]
                padfs.append([pstart+k for k in ids]);padfs.append([pstart+count+k for k in ids[::-1]])
        previous=[pstart+k for k in boundary]
        for t in (.12,.25,.40,.56,.70,.82,.92,1):
            ring=[]
            for k in boundary:
                if t==1:ring.append(pstart+count+k);continue
                # Quarter-ellipse descent turns underneath at the lower hem.
                zt=math.sin(t*math.pi/2);xt=1-math.cos(t*math.pi/2)
                q=(1-xt)*ptop[k]+xt*plow[k];q[2]=(1-zt)*ptop[k][2]+zt*plow[k][2];u,v=parameters[k]
                # Small convex rounding only on the exposed support perimeter.
                direction=q-np.array([side*.205,.012,q[2]]);length=np.linalg.norm(direction)
                if length>0:q+=direction/length*.004*math.sin(math.pi*t)
                ring.append(len(padp));padp.append(q);paduv.append((u+v*.07,t*.12));padws.append(pskin[k])
            for k in range(len(ring)):padfs.append([previous[k],previous[(k+1)%len(ring)],ring[(k+1)%len(ring)],ring[k]])
            previous=ring
    ep=upper.geometry(EPAULETTES,ps,fs,uv,ws,old_ep.data.materials[0],edit,rig,names);ep.data.uv_layers.active.name=old_ep.data.uv_layers.active.name;s9.recalc(ep)
    pad=upper.geometry(PAD,padp,padfs,paduv,padws,old_pad.data.materials[0],edit,rig,names);s9.recalc(pad)
    # Native-coloured padding is a single plain fabric; use face-local UVs on
    # its closed hidden bottom/walls to avoid degenerate charts at return edges.
    layer=pad.data.uv_layers.active
    for f in pad.data.polygons:
        normal=np.array(f.normal);axis=int(np.argmax(abs(normal)));axes2=[i for i in range(3) if i!=axis]
        for li,i in zip(f.loop_indices,f.vertices):layer.data[li].uv=np.array(pad.data.vertices[i].co)[axes2]*2+.5
    native.move(old_ep,archive);native.move(old_pad,archive)
    ep['construction']='Thin Dietrich-inspired shoulder; rounded 5 mm closed hem turns into its own underside. Upper half gold, grey support exposed below. Hand-authored contour follows step11 user sketch.'
    pad['construction']='Fitted grey under-pad follows the gold underside with a visible lower wall and closes into the sleeve.'
    return ep,pad,{'gold_grid_vertices':grids,'gold_rim_rings':rims,'gold_thickness_m':radius*2,'padding_top_offset_m':.009,'outline':'Manual interpretation of user_front_step11.png; native Dietrich and Reichman surfaces inspected separately.','native_references':str(TOP/'source/shoulder_fit_study/native_reference_geometry.json')}

def collar_lining(old,edit,archive):
    ob=s8.clone(old,GARMENT,edit,archive);me=ob.data
    mat=next(o for o in edit.objects if o.name.startswith('14 ')).data.materials[0].copy();mat.name='Hassler collar inside — Dietrich shoulder brocade'
    uvname='Collar inside brocade UV';layer=me.uv_layers.new(name=uvname);base=me.uv_layers[0]
    for a,b in zip(layer.data,base.data):a.uv=b.uv
    nodes=mat.node_tree.nodes;tex=next(n for n in nodes if n.type=='TEX_IMAGE')
    for n in list(nodes):
        if n.type=='UVMAP':nodes.remove(n)
    n=nodes.new('ShaderNodeUVMap');n.uv_map=uvname;mat.node_tree.links.new(n.outputs[0],tex.inputs['Vector'])
    grey=me.materials[4];me.materials[15]=mat
    # The historical collar reverses winding around the folded lapel. Select
    # the physical outward/inside side per face, not a universal slot swap.
    while len(me.materials)<34:me.materials.append(grey)
    me.materials[22]=mat;me.materials[33]=grey
    prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'));faces=prior['cut']['collar_faces'];rows=[]
    for k in range(0,len(faces),5):
        ff=[list(me.polygons[i].vertices) for i in faces[k:k+5]]
        if not rows:rows.append([ff[0][0]]+[f[1] for f in ff])
        rows.append([ff[0][3]]+[f[2] for f in ff])
    arc=[0.]
    for a,b in zip(rows,rows[1:]):arc.append(arc[-1]+(me.vertices[a[2]].co-me.vertices[b[2]].co).length)
    mapping={}
    for i,row in enumerate(rows):
        width=0.
        for j,v in enumerate(row):
            if j:width+=(me.vertices[row[j]].co-me.vertices[row[j-1]].co).length
            mapping[v]=(.30+.60*arc[i]/arc[-1],.13+width*1.6)
    # Conforming vertices inserted into neighbouring collar edges by step07
    # are not part of the original regular section rows. Interpolate their UV.
    segments=[(a,b) for row in rows for a,b in zip(row,row[1:])]+[(a[j],b[j]) for a,b in zip(rows,rows[1:]) for j in range(6)]
    for i in {i for fi in faces for i in me.polygons[fi].vertices}-set(mapping):
        p=np.array(me.vertices[i].co);best=None
        for a,b in segments:
            aa=np.array(me.vertices[a].co);d=np.array(me.vertices[b].co)-aa;t=float(np.clip(np.dot(p-aa,d)/max(np.dot(d,d),1e-15),0,1));distance=np.linalg.norm(p-aa-t*d)
            if best is None or distance<best[0]:best=(distance,(1-t)*np.array(mapping[a])+t*np.array(mapping[b]))
        mapping[i]=best[1]
    for fi in faces:
        f=me.polygons[fi];radial=Vector((f.center.x,f.center.y,0))
        if f.normal.dot(radial)<0:f.material_index=22
        for li,i in zip(f.loop_indices,f.vertices):layer.data[li].uv=mapping[i]
    me.uv_layers.active_index=0
    ob['collar_inside']='Separate UV chart on physical inner faces (slots15/22); outside grey, inner face Dietrich shoulder brocade. Geometry unchanged from step10.'
    return ob,{'material_slots':[15,22],'grey_slots':[4,33],'material':mat.name,'uv_layer':uvname,'faces':faces,'uv_bounds':np.array(list(mapping.values())).min(axis=0).tolist()+np.array(list(mapping.values())).max(axis=0).tolist(),'geometry_unchanged':True,'outside_grey_retained':True}

def close_collar_gap(coat,ep,edit,rig,names,lining):
    me=coat.data;faces=lining['faces'];rows=[]
    for k in range(0,len(faces),5):
        ff=[list(me.polygons[i].vertices) for i in faces[k:k+5]]
        if not rows:rows.append([ff[0][0]]+[f[1] for f in ff])
        rows.append([ff[0][3]]+[f[2] for f in ff])
    source=s8.SampleMesh(ep,names);ww=s8.weights(coat,names);ps=[];uv=[];ws=[];fs=[];attachments=[]
    for side in (1,-1):
        # Sew underneath the stable collar roll, not to the curling free lip.
        # The lip doubles back in plan at the rear: extruding it would create
        # a folded curtain. The concealed roll provides an ordered seam.
        chosen=[r[2] for r in rows if side*me.vertices[r[2]].co.x>(.055 if me.vertices[r[2]].co.y>.03 else .09) and me.vertices[r[2]].co.z>.535]
        # Turn the joining cloth around the rear end of the rolled collar.
        # Without this short end return the side slit still sees background.
        end=chosen[-1] if side>0 else chosen[0];endrow=next(r for r in rows if r[2]==end)
        front=chosen[0] if side>0 else chosen[-1];frontrow=next(r for r in rows if r[2]==front)
        chosen=frontrow[:2:-1]+chosen+endrow[3:] if side>0 else endrow[:2:-1]+chosen+frontrow[3:]
        chain=[];arc=0.;prev=None;ordered=[]
        for i in chosen:
            p=np.array(me.vertices[i].co)
            if prev is not None and np.linalg.norm(p-prev)<.002:continue
            if prev is not None:arc+=np.linalg.norm(p-prev)
            ordered.append((i,p,arc));prev=p
        for i,p,s in ordered:
            hit,no,fi,dist=source.tree.ray_cast(Vector((p[0],p[1],.8)),Vector((0,0,-1)))
            if hit is None:hit,no,fi,dist=source.tree.find_nearest(Vector(p))
            q=np.array(hit);bottomw=source.skin(hit,fi)
            # Exact shared top coordinates and weights form a sewn attachment.
            # The strip's edge lies under the collar roll; the 1 mm thickness
            # is the only overlap allowed at this seam by the validator.
            q+=np.array(no)*.0007
            if np.linalg.norm(p-q)<.003:continue
            chain.append((p,q,ww[i],bottomw,s))
        total=chain[-1][-1];grid=[]
        for p,q,wa,wb,s in chain:
            row=[]
            for t in (0,.25,.6,1):
                pp=(1-t)*p+t*q
                if side>0:
                    fit=s3.smooth(-.02,.04,p[1])*(1-s3.smooth(.11,.14,p[0]))
                    pp[0]+=.009*fit*math.sin(math.pi*t)
                w=(1-t)*wa+t*wb;w[np.argsort(w)[:-4]]=0;w/=w.sum()
                row.append(len(ps));ps.append(pp);ws.append(w);uv.append((.30+.60*s/total,.17+np.linalg.norm(p-q)*t*1.6))
            grid.append(row)
        for a,b in zip(grid,grid[1:]):
            for j in range(3):fs.append([a[j],b[j],b[j+1],a[j+1]])
        attachments.append({'side':side,'top_vertices':[r[0] for r in grid],'lower_vertices':[r[-1] for r in grid],'section_vertices':grid})
    ob=upper.geometry(GUSSET,ps,fs,uv,ws,ep.data.materials[0],edit,rig,names);ob.data.uv_layers.active.name=ep.data.uv_layers.active.name;s9.recalc(ob)
    solid=ob.modifiers.new('Gold joining cloth 1 mm','SOLIDIFY');solid.thickness=.001;solid.offset=-1;solid.use_quality_normals=True
    ob['construction']='Gold cloth closes the real gap below the outward collar. Its concealed upper seam shares the collar roll coordinates and skin weights; the lower hem meets the gold shoulder.'
    return ob,{'attachments':attachments,'thickness_m':.001,'top_seam_shared_with_collar':True,'attachment':'Concealed inside collar roll, section column2. The free grey lip stays outside.','note':'Intentional sewn contacts are distinguished from free cloth collisions.'}

def main():
    OUT.mkdir(parents=True,exist_ok=True);digest=s2.sha(PARENT);bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step10 full gold shoulder before thin rolled hem');archive.hide_viewport=archive.hide_render=True
    rig=bpy.data.objects['RIG — native Rheinland'];names=[b['name'] for b in native.load('body')['bones']]
    old={key:next(o for o in edit.objects if o.name.startswith(key)) for key in ('10 ','14 ','16 ')}
    coat,lining=collar_lining(old['10 '],edit,archive);ep,pad,shoulder=shoulders(old['14 '],old['16 '],coat,edit,archive,rig,names);gusset,join=close_collar_gap(coat,ep,edit,rig,names,lining)
    previous=json.loads((TOP/'step_10/report.json').read_text(encoding='utf8'))
    report={'step':'11 thin rolled-in epaulettes and gold collar inside','parent':str(PARENT),'parent_sha256':digest,'shoulders':shoulder,'collar_lining':lining,'gold_join':join,'neck':previous['neck'],'cords':previous['cords'],'inherited_opening':previous['inherited_opening'],'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(coat);scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    if '--no-render' not in sys.argv:
        render(scene,'front',(0,1,0));render(scene,'three_quarter',(.65,1,.12));render(scene,'shoulder_detail',(-.7,1,.25),(-.18,0,1.51),.43)
    assert s2.sha(PARENT)==digest;print('STEP11 SAVED',flush=True)

if __name__=='__main__':main()
