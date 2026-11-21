"""Scrote-inspired belt below the accepted tunic, with native Rheinland fittings."""
import sys,json,gzip,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step08 as s8
import hassler_native_step09 as s9
import hassler_native_step13 as s13
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_14';PARENT=s13.OUT/'hassler_native_upper.blend'
BASE='00 Native lower body — original pouch belt removed'
BELT='19 Hassler waist belt — fitted Scrote construction'
BUCKLE='20 Rheinland clasp — gold frame and native latch'
LOOPS='21 Belt keepers — Rheinland fittings'
WAIST='22 Trouser waist — sewn continuation under belt'
OLD='00 Native lower body and belt'
COUNT=72

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s9.OUT=OUT;s9.render(scene,label,direction,target,scale)

def material(name,texture,lo,hi,metal=0):
    mat=upper.material(name,(.2,.2,.2),.66,metal,texture)
    n=mat.node_tree.nodes;l=mat.node_tree.links;tex=next(x for x in n if x.type=='TEX_IMAGE');tex.image.pack()
    bw=n.new('ShaderNodeRGBToBW');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*lo,1);ramp.color_ramp.elements[1].color=(*hi,1)
    l.new(tex.outputs[0],bw.inputs[0]);l.new(bw.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    return mat

def remove_old(old,indices,edit,archive):
    # Keep all native vertex indices/weights and copy retained loop data exactly.
    ob=s8.clone(old,BASE,edit,archive);src=old.data;me=bpy.data.meshes.new(BASE)
    retained=[f for f in src.polygons if f.index not in indices]
    me.from_pydata([v.co[:] for v in src.vertices],[],[list(f.vertices) for f in retained]);me.update()
    for mat in src.materials:me.materials.append(mat)
    for a,b in zip(me.polygons,retained):a.material_index=b.material_index;a.use_smooth=b.use_smooth
    for srcuv in src.uv_layers:
        layer=me.uv_layers.new(name=srcuv.name)
        for a,b in zip(me.polygons,retained):
            for la,lb in zip(a.loop_indices,b.loop_indices):layer.data[la].uv=srcuv.data[lb].uv
    me.normals_split_custom_set([src.corner_normals[li].vector[:] for f in retained for li in f.loop_indices])
    # Mesh vertex groups are stored on mesh vertices; restore them after swapping.
    names=[g.name for g in old.vertex_groups];w=s8.weights(old,names);ob.data=me
    if not ob.vertex_groups:
        for name in names:ob.vertex_groups.new(name=name)
    s8.set_weights(ob,w)
    return ob,[f.index for f in retained]

class Builder:
    def __init__(self,surface,materials):self.p=[];self.f=[];self.uv=[];self.w=[];self.mi=[];self.surface=surface;self.materials=materials
    def point(self,p):
        p=np.array(p,dtype=float);hit,no,idx,dist=self.surface.tree.find_nearest(Vector(p));self.w.append(self.surface.skin(hit,idx));self.p.append(p);return len(self.p)-1
    def face(self,ids,uv,mat=0):self.f.append(ids);self.uv.append(uv);self.mi.append(mat)
    def build(self,name,edit,rig,names):
        ob=upper.geometry(name,self.p,self.f,[(0,0)]*len(self.p),self.w,self.materials[0],edit,rig,names)
        for mat in self.materials[1:]:ob.data.materials.append(mat)
        for f,uv,mi in zip(ob.data.polygons,self.uv,self.mi):
            f.material_index=mi
            for li,q in zip(f.loop_indices,uv):ob.data.uv_layers[0].data[li].uv=q
        s9.recalc(ob);return ob

def contour(donor):
    p=np.array(donor['points']);selected=donor['groups'][0]['faces'][233:257];ids=sorted({i for f in selected for i in f})
    # Use the actual 12-station Scrote band. Average each upper/lower pair;
    # fit its width/depth to the unchanged Rheinland waist.
    points=np.unique(np.round(p[ids],7),axis=0);bottom=points[points[:,1]<.15];top=points[points[:,1]>.15]
    angle=lambda q:math.atan2(q[0]-.000998,-q[2]-.035)
    bottom=sorted(bottom,key=angle);top=sorted(top,key=angle);assert len(bottom)==len(top)==12
    controls=[]
    for a,b in zip(bottom,top):
        q=(a+b)/2;controls.append(np.array([(q[0]-.000998)*1.15,-q[2]*1.27]))
    # Symmetrise the donor's slightly skewed back. Preserve its broad front.
    def sample(t):
        k=int(math.floor(t))%12;v=t-math.floor(t);a,b,c,e=[controls[(k+j)%12] for j in (-1,0,1,2)]
        return .5*((2*b)+(-a+c)*v+(2*a-5*b+4*c-e)*v*v+(-a+3*b-3*c+e)*v*v*v)
    raw=np.array([sample(k*12/COUNT) for k in range(COUNT)])
    # The native stations start near the rear. Sort by polar angle for a seam
    # underneath the central clasp, then resample the smooth radial profile.
    ang=np.unwrap(np.arctan2(raw[:,0],raw[:,1]-.04));order=np.argsort((ang+2*math.pi)%(2*math.pi));ang=(ang[order]+2*math.pi)%(2*math.pi);raw=raw[order]
    def at(theta):
        t=theta%(2*math.pi);a=np.r_[ang[-1]-2*math.pi,ang,ang[0]+2*math.pi];q=np.vstack((raw[-1],raw,raw[0]));return np.array([np.interp(t,a,q[:,j]) for j in (0,1)])
    result=[]
    for i in range(COUNT):
        t=2*math.pi*i/COUNT;a=at(t);b=at(-t);b[0]*=-1;q=(a+b)/2;n=q-np.array([0,.04]);n/=np.linalg.norm(n);result.append(q+.004*n)
    return np.array(result),controls

def belt_mesh(xy,surface,mat,edit,rig,names):
    g=Builder(surface,[mat]);bottom=.128;top=.214
    # Closed 6 mm strap with small rounded returns, not a floating sheet.
    section=[(-.001,top),(0,top-.002),(0,bottom+.002),(-.001,bottom),(-.005,bottom),(-.006,bottom+.002),(-.006,top-.002),(-.005,top)]
    rows=[]
    for q in xy:
        n=q-np.array([0,.04]);n/=np.linalg.norm(n);rows.append([g.point([*(q+off*n),z]) for off,z in section])
    seg=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1);arc=np.r_[0,np.cumsum(seg)];half=arc[COUNT//2]
    for i in range(COUNT):
        k=(i+1)%COUNT
        for j in range(8):
            l=(j+1)%8;ids=[rows[i][j],rows[k][j],rows[k][l],rows[i][l]]
            def uv(idx,sj):
                phase=arc[idx]/half if idx<=COUNT//2 else (arc[-1]-arc[idx])/half
                # One native plain belt field per half, joined under the clasp
                # and rear keeper, without crossing donor shirt or buckle art.
                return (.045+.255*phase,.025+.075*(section[sj][1]-bottom)/(top-bottom))
            qs=[uv(i,j),uv(i+1,j),uv(i+1,l),uv(i,l)]
            # Thickness edges also need nonzero UV area.
            if j in (3,7):
                a=.045+.255*arc[i]/arc[-1];b=.045+.255*arc[i+1]/arc[-1];qs=[(a,.03),(b,.03),(b,.038),(a,.038)]
            g.face(ids,qs)
    ob=g.build(BELT,edit,rig,names);ob['source']='24 actual li_scrote belt faces, 12 stations; fitted to Rheinland waist and rebuilt as closed strap'
    return ob,{'height_m':top-bottom,'z_bounds':[bottom,top],'thickness_m':.006,'source_faces':list(range(233,257)),'stations':COUNT}

def plate(g,center,tangent,outward,width,height,depth,front_mat=0,body_mat=0,uvrect=(.83,.022,.866,.105)):
    # A shaped, closed fitting: bevelled perimeter and inset front, complete back.
    c=np.array(center);t=np.array(tangent);n=np.array(outward);up=np.array([0,0,1.]);cut=min(.003,width*.13,height*.13)
    shape=[(-width/2+cut,-height/2),(width/2-cut,-height/2),(width/2,-height/2+cut),(width/2,height/2-cut),(width/2-cut,height/2),(-width/2+cut,height/2),(-width/2,height/2-cut),(-width/2,-height/2+cut)]
    rows=[]
    for d,scale in [(0,1),(depth-.0015,1),(depth,.90)]:rows.append([g.point(c+t*x*scale+up*z*scale+n*d) for x,z in shape])
    u0,v0,u1,v1=uvrect
    uv=lambda i,scale=1:(u0+(shape[i][0]*scale/width+.5)*(u1-u0),v0+(shape[i][1]*scale/height+.5)*(v1-v0))
    for j in range(2):
        for i in range(8):k=(i+1)%8;g.face([rows[j][i],rows[j][k],rows[j+1][k],rows[j+1][i]],[(.84,.03),(.86,.03),(.86,.09),(.84,.09)],body_mat)
    g.face(rows[-1],[uv(i,.90) for i in range(8)],front_mat);g.face(rows[0][::-1],[uv(i) for i in range(7,-1,-1)],body_mat)

def fittings(xy,surface,gold,rhmat,edit,rig,names):
    g=Builder(surface,[gold,rhmat]);front=float(xy[0,1]);zc=.170
    plate(g,(0,front-.0006,zc),(1,0,0),(0,1,0),.066,.072,.009,0,0)
    # Native RH belt latch replaces the donor's Liberty eagle. Its slim inset
    # and split closure give a restrained Rheinland rectangular fitting.
    plate(g,(0,front+.0088,zc),(1,0,0),(0,1,0),.039,.051,.0025,1,0,(.065,.173,.155,.260))
    buckle=g.build(BUCKLE,edit,rig,names)
    g=Builder(surface,[rhmat]);angles=[.43,-.43,math.pi-.62,math.pi,math.pi+.62]
    for t in angles:
        k=(t%(2*math.pi))*COUNT/(2*math.pi);i=int(k)%COUNT;v=k-int(k);q=(1-v)*xy[i]+v*xy[(i+1)%COUNT]
        n=q-np.array([0,.04]);n/=np.linalg.norm(n);tangent=np.array([n[1],-n[0],0.])
        plate(g,(*q,.170),tangent,(*n,0.),.011,.071,.003,0,0,(.10,.174,.145,.253))
    loops=g.build(LOOPS,edit,rig,names)
    return buckle,loops,{'buckle_width_m':.066,'buckle_height_m':.072,'buckle_front_y':front+.0113,'keeper_angles':angles,'rationale':'Front/back art: dark strap, rectangular gold closure, small grey rear keepers. Native RH latch imagery replaces Liberty eagle. No holster.'}

def waist_continuation(base,xy,surface,edit,rig,names):
    me=base.data;p=np.array([v.co[:] for v in me.vertices]);uv=me.uv_layers[0];adj={};key=lambda i:tuple(np.round(p[i],5));skin=s8.weights(base,names)
    for f in me.polygons:
        ids=list(f.vertices);lis=list(f.loop_indices)
        for j,(a,b) in enumerate(zip(ids,ids[1:]+ids[:1])):adj.setdefault(tuple(sorted((key(a),key(b)))),[]).append((a,b,uv.data[lis[j]].uv[:],uv.data[lis[(j+1)%len(ids)]].uv[:],f.material_index))
    edges=[v[0] for k,v in adj.items() if len(v)==1 and min(p[list(v[0][:2]),2])>.05];assert len(edges)==12
    g=Builder(surface,list(me.materials));attachments=[]
    for a,b,ua,ub,mi in edges:
        bottom=[];top=[]
        for i in (a,b):
            bottom.append(g.point(p[i]));g.w[-1]=skin[i].copy()
            theta=math.atan2(p[i,0],p[i,1]-.04)%(2*math.pi);v=theta*COUNT/(2*math.pi);k=int(v);f=v-k;q=(1-f)*xy[k%COUNT]+f*xy[(k+1)%COUNT];n=q-np.array([0,.04]);n/=np.linalg.norm(n)
            top.append(g.point([*(q-.007*n),.151]))
            attachments.append([bottom[-1],i])
        g.face([bottom[0],bottom[1],top[1],top[0]],[ua,ub,(ub[0],ub[1]+.025),(ua[0],ua[1]+.025)],mi)
    ob=g.build(WAIST,edit,rig,names)
    for face in ob.data.polygons:
        if np.dot(face.normal,[face.center.x,face.center.y-.04,0])<0:face.flip()
    ob.data.update();ob['construction']='Exact 12 native trouser boundary edges continued inside the belt. Closes the old pouch-belt opening without moving the original trousers.'
    return ob,{'native_boundary_edges':[[a,b] for a,b,*_ in edges],'bottom_attachments':attachments,'top_z':.151,'original_trouser_vertices_unchanged':True}

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(PARENT);study=json.loads((TOP/'source/belt_study/geometry.json').read_text(encoding='utf8'));assert study['parent_sha256']==digest
    donorpath=TOP/'source/scrote/source/scrote.json.gz';d=json.loads(gzip.decompress(donorpath.read_bytes()))
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step13 original pouch belt');archive.hide_render=archive.hide_viewport=True
    rig=bpy.data.objects['RIG — native Rheinland'];names=[b['name'] for b in native.load('body')['bones']];old=bpy.data.objects[OLD];indices=set(study['belt_faces']);surface=s8.SampleMesh(old,names,lambda f:f.index in indices)
    base,kept=remove_old(old,indices,edit,archive)
    strap=material('Hassler 14 — Scrote charcoal leather belt',d['groups'][0]['texture'],(.012,.015,.014),(.18,.19,.18))
    gold=upper.material('Hassler 14 — restrained gold buckle',(.42,.27,.065),.55,.3,d['groups'][0]['texture'])
    tex=next(n for n in gold.node_tree.nodes if n.type=='TEX_IMAGE');tex.image.pack()
    rhtexture=native.load('body')['groups'][1]['texture'];rh=material('Hassler 14 — native Rheinland latch and keepers',rhtexture,(.024,.028,.027),(.38,.39,.35),.2)
    xy,controls=contour(d);belt,br=belt_mesh(xy,surface,strap,edit,rig,names);buckle,loops,fr=fittings(xy,surface,gold,rh,edit,rig,names)
    waist,wr=waist_continuation(base,xy,surface,edit,rig,names)
    report={'step':'14 belt below tunic; Scrote construction with Rheinland fittings','parent':str(PARENT),'parent_sha256':digest,'accepted_upper_geometry_and_materials_unchanged':True,'removed_old_belt_faces':sorted(indices),'retained_base_faces':kept,'donor':{'json':str(donorpath),'json_sha256':s13.sha(donorpath),'dfm_sha256':d['sha256'],'native_belt_faces':list(range(233,257)),'controls_xy':[p.tolist() for p in controls]},'art':[{'path':str(TOP/'source/art'/n),'sha256':s13.sha(TOP/'source/art'/n)} for n in ('hassler1.png','hassler2.png')],'belt':br,'fittings':fr,'textures':[{'path':str(p),'sha256':s13.sha(Path(p))} for p in (d['groups'][0]['texture'],rhtexture)],'game_installed':False,'game_animations_validated':False}
    report['waist_closure']=wr
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2));native.activate(belt)
    scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(PARENT)==digest
    if '--no-render' not in sys.argv:
        render(scene,'front',(0,1,0));render(scene,'waist_front',(0,1,.08),(0,.02,1.15),.59);render(scene,'waist_back',(0,-1,.08),(0,.02,1.15),.59)
    print('STEP14 SAVED',flush=True)

if __name__=='__main__':main()
