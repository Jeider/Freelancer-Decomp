"""Archived rejected silhouette experiment. Do not use as the current builder."""
from pathlib import Path
import sys,json,hashlib
from io import BytesIO
import numpy as np
from PIL import Image,ImageFilter

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder,read_tree,write_tree,child,blob,arr,put,triangles,faces,export
from repair_panel_normals import leaves
OUT=ROOT/'out/reichman_body_test_v2'
REL='CHARACTERS/BODIES/rh_reichman_body.dfm'
ACTIVE_LODS=(0,1,2,3)
SUBDIVISIONS=1
FOCUS_REFINEMENT=True
POSITION_SAMPLE=None

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def masks(rgb):
    r,g,b=np.moveaxis(rgb,-1,0)
    red=smooth(.10,.35,r-g)*smooth(.08,.3,r-b)
    gold=smooth(.06,.24,r-b)*smooth(.03,.18,g-b)*(1-red)
    return red,gold

def sample(im,uv):
    x=np.clip(uv[0],0,1)*(im.shape[1]-1);y=np.clip(1-uv[1],0,1)*(im.shape[0]-1)
    ix,iy=int(x),int(y);jx=min(ix+1,im.shape[1]-1);jy=min(iy+1,im.shape[0]-1)
    return im[iy,ix]*(1-x+ix)*(1-y+iy)+im[iy,jx]*(x-ix)*(1-y+iy)+im[jy,ix]*(1-x+ix)*(y-iy)+im[jy,jx]*(x-ix)*(y-iy)

def relief(p,n,uv,mat,atlas,level):
    x,y,z=p;red,gold=masks(sample(atlas,uv))
    torso=smooth(.18,.28,y)*(1-smooth(.54,.62,y))*(1-smooth(.16,.23,abs(x)))
    front=1-smooth(-.09,-.035,z)
    # Broad folds only: colour is a semantic mask, never a height field.
    redfold=(.006+.004*np.cos((y-.32-abs(x)*.45)*110))*red*torso
    bib=.0025*gold*torso*front
    shoulder=np.exp(-((abs(x)-.235)/.062)**2-((y-.568)/.047)**2)
    epaulette=0.
    cuff=np.exp(-((y-.115)/.055)**2)*smooth(.22,.28,abs(x))
    cuffrelief=.0045*cuff*gold
    collar=np.exp(-((y-.625)/.020)**2)*(1-smooth(.075,.125,abs(x)))
    collarrelief=.003*collar
    clothfold=0.
    sleeve=0.
    medal=0.
    if mat=='reich 3' and uv[0]>.6 and uv[1]<.4 and y>.32 and abs(x)<.16:
        radius=np.sqrt(((uv[0]-.783)/.16)**2+((uv[1]-.18)/.20)**2)
        medal=.011*max(0,1-radius)**1.3
    amount=redfold+bib+epaulette+cuffrelief+collarrelief+medal
    delta=n*amount
    # Raised domed shoulder plate, with a stronger outer overhang. Keep the
    # arm/socket shape anchored by a smooth spatial falloff.
    shoulder_form=shoulder*smooth(.12,.18,abs(x))
    delta+=np.array([np.sign(x)*.022,.056,.012*np.tanh(z/.07)])*shoulder_form
    # Coat tails: flare away from the trousers and roll the curved hem.
    # This atlas region is the coat, unlike the trousers in reich 1 / reich 2.
    if mat=='reich 3' and z>.012 and abs(x)<.205 and -.12<y<.32:
        panel=smooth(.012,.055,z)*(1-smooth(.20,.32,y))*smooth(-.12,-.07,y)
        flare=(1-smooth(-.04,.24,y))*panel
        hem_y=.20-.29*(1-np.clip(abs(x)/.18,0,1)**1.5)
        rolled=np.exp(-((y-hem_y)/.023)**2)*panel
        delta+=np.array([np.tanh(x/.06)*(.030*flare+.009*rolled),-.008*rolled,.040*flare+.012*rolled])
        # Two broad tailoring folds; no fine fabric noise.
        delta[2]+=.008*np.cos(x*55)*panel
    # Front coat lower edge and the raised gold facing surrounding the sash.
    if mat=='reich 1' and y>.15 and z<-.055:
        lower=np.exp(-((y-.225)/.025)**2)*(1-smooth(.15,.20,abs(x)))
        delta+=n*(.009*lower+.006*gold*torso)
    return delta*(1,.75,.4,.2,0,0)[level]

def surface_maps(root):
    maps={};atlases={}
    for mat in child(root,'Material library').children:
        if not mat.children:continue
        name=blob(mat,'Dt_name').rstrip(b'\0').decode()
        im=Image.open(BytesIO(blob(child(child(root,'Texture library'),name),'MIP0'))).convert('RGB')
        rgb=np.asarray(im,dtype=float)/255;red,gold=masks(rgb)
        atlases[mat.name]=np.asarray(im.filter(ImageFilter.GaussianBlur(3)),dtype=float)/255
        luma=im.convert('L');a=np.asarray(luma.filter(ImageFilter.GaussianBlur(.7)),float)/255;b=np.asarray(luma.filter(ImageFilter.GaussianBlur(2.3)),float)/255
        dy,dx=np.gradient(a-b)
        strength=2+gold*6+red*.5
        nx=-dx*strength;ny=dy*strength;nz=np.ones_like(nx)
        length=np.sqrt(nx*nx+ny*ny+nz*nz)
        normal=np.stack((nx/length,ny/length,nz/length),-1)
        normalpath=OUT/(name+'_normal.png');Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255)).save(normalpath)
        surface=np.stack((.78*(1-red)*(1-gold)+.38*red+.42*gold,.72*gold,red),-1)
        surfacepath=OUT/(name+'_surface.png');Image.fromarray(np.uint8(np.clip(surface,0,1)*255)).save(surfacepath)
        maps[mat.name]=dict(normal=str(normalpath),surface=str(surfacepath))
    return maps,atlases

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=(GAME/'DATA'/REL).read_bytes();sha=hashlib.sha256(source).hexdigest()
    DataFolder(root=OUT/'original').sync_data_file(REL,source)
    header,roots=read_tree(source);root=roots[0];export(root,OUT/'before.json')
    maps,atlases=surface_maps(root);report=[]
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        level=int(mesh.name[4:]);geo=child(mesh,'Geometry');groups=[g for g in child(mesh,'Face_groups').children if g.children]
        if level not in ACTIVE_LODS:
            count=sum(len(triangles(g)) for g in groups)
            report.append(dict(lod=level,before_triangles=count,after_triangles=count,unchanged=True));continue
        p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3);pi=arr(geo,'Point_indices','<u4').ravel()
        uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
        extra=any(v.name=='UV1' for v in geo.children)
        uv1=arr(geo,'UV1','<f4',2) if extra else uv;ui1=arr(geo,'UV1_indices','<u4').ravel() if extra else ui
        first=arr(geo,'Point_bone_first','<u4').ravel();count=arr(geo,'Point_bone_count','<u4').ravel();ids=arr(geo,'Bone_id_chain','<u4').ravel();weights=arr(geo,'Bone_weight_chain','<f4').ravel()
        op=[];on=[];ou=[];ou1=[];skin=[];offsets=[];keys=[];alltris=[];before=0
        for group in groups:
            mat=blob(group,'Material_name').rstrip(b'\0').decode();new=[]
            for tri in triangles(group):
                before+=1;t=np.array(tri);a,b,c=np.eye(3);ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
                subs=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)] if level<2 else [(a,b,c)]
                if level==0:
                    for _ in range(1,SUBDIVISIONS):
                        refined=[]
                        for aa,bb,cc in subs:
                            ab=(aa+bb)/2;bc=(bb+cc)/2;ca=(cc+aa)/2
                            refined.extend([(aa,ab,ca),(ab,bb,bc),(ca,bc,cc),(ab,bc,ca)])
                        subs=refined
                center=p[pi[t]].mean(axis=0)
                focus=(center[1]>.48 and abs(center[0])>.13) or (mat=='reich 3' and -.12<center[1]<.32 and center[2]>.012) or (mat=='reich 1' and .17<center[1]<.27)
                if level==0 and focus and FOCUS_REFINEMENT:
                    # Interior fans add samples only where the silhouette and
                    # tailoring change, without T-junctions on shared edges.
                    refined=[]
                    for aa,bb,cc in subs:
                        middle=(aa+bb+cc)/3
                        refined.extend([(aa,bb,middle),(bb,cc,middle),(cc,aa,middle)])
                    subs=refined
                for sub in subs:
                    face=[]
                    for bary in sub:
                        pos=bary@p[pi[t]];normal=bary@n[pi[t]];normal/=max(np.linalg.norm(normal),1e-9);tex=bary@uv[ui[t]]
                        if POSITION_SAMPLE is not None:pos=POSITION_SAMPLE(p[pi[t]],bary,level)
                        influence={}
                        for k,v in enumerate(pi[t]):
                            for bone,w in zip(ids[first[v]:first[v]+count[v]],weights[first[v]:first[v]+count[v]]):
                                influence[int(bone)]=influence.get(int(bone),0)+float(bary[k]*w)
                        influence={k:v for k,v in influence.items() if v>1e-8};total=sum(influence.values());influence={k:v/total for k,v in influence.items()}
                        face.append(len(op));op.append(pos);on.append(normal);ou.append(tex);ou1.append(bary@uv1[ui1[t]]);skin.append(influence)
                        keys.append(tuple(np.round(pos,6)));offsets.append(relief(pos,normal,tex,mat,atlases[mat],level))
                    new.append(face)
            faces(group,new);alltris.extend(new)
        # Weld displacement across UV/material seams. No topology is removed.
        buckets={}
        for i,key in enumerate(keys):buckets.setdefault(key,[]).append(i)
        op=np.asarray(op);on=np.asarray(on);offsets=np.asarray(offsets)
        for indices in buckets.values():op[indices]+=offsets[indices].mean(axis=0)
        sums={}
        for tri in alltris:
            a,b,c=op[tri];cross=np.cross(b-a,c-a)
            if np.dot(cross,on[tri].mean(axis=0))<0:cross=-cross
            for i in tri:sums[i]=sums.get(i,np.zeros(3))+cross
        newnorm=on.copy()
        for indices in buckets.values():
            for i in indices:
                near=[j for j in indices if np.dot(on[i],on[j])>.75]
                normal=sum((sums[j] for j in near),np.zeros(3))
                if np.linalg.norm(normal)>1e-10:newnorm[i]=normal/np.linalg.norm(normal)
        collar=(op[:,1]>.57)&(abs(op[:,0])<.13)
        newnorm[collar]=on[collar]
        assert len(op)<65536 and np.isfinite(op).all() and np.isfinite(newnorm).all()
        identity=np.arange(len(op),dtype='<u4');lookup={};remap=[];unique=[]
        for i in range(len(op)):
            key=tuple(np.round(op[i],7))+tuple(np.round(newnorm[i],6))+tuple(sorted((k,round(v,7)) for k,v in skin[i].items()))
            if key not in lookup:lookup[key]=len(unique);unique.append(i)
            remap.append(lookup[key])
        op=op[unique];newnorm=newnorm[unique];skin=[skin[i] for i in unique]
        for name,data,kind in [('Points',op,'<f4'),('Vertex_normals',newnorm,'<f4'),('Point_indices',remap,'<u4'),('UV0',ou,'<f4'),('UV0_indices',identity,'<u4')]:put(geo,name,np.asarray(data,dtype=kind).tobytes())
        if extra:put(geo,'UV1',np.asarray(ou1,dtype='<f4').tobytes());put(geo,'UV1_indices',identity.tobytes())
        starts=[];counts=[];bones=[];ws=[]
        for influence in skin:starts.append(len(bones));counts.append(len(influence));bones.extend(influence);ws.extend(influence.values())
        for name,data,kind in [('Point_bone_first',starts,'<u4'),('Point_bone_count',counts,'<u4'),('Bone_id_chain',bones,'<u4'),('Bone_weight_chain',ws,'<f4')]:put(geo,name,np.asarray(data,dtype=kind).tobytes())
        report.append(dict(lod=level,before_triangles=before,after_triangles=len(alltris),points=len(op),max_offset_m=float(max(np.linalg.norm(offsets,axis=1)))))
    data=write_tree(header,roots)
    old={path:b for path,_,b in leaves(source)[1]};new={path:b for path,_,b in leaves(data)[1]}
    for path,value in old.items():
        if '/MultiLevel/' not in path:assert new[path]==value,path
    DataFolder(root=OUT/'stage').sync_data_file(REL,data);export(root,OUT/'after.json')
    (OUT/'preview_materials.json').write_text(json.dumps(maps,indent=2))
    result=dict(source_sha256=sha,prototype_sha256=hashlib.sha256(data).hexdigest(),lods=report,original_textures_materials_skeleton_unchanged=True,preview_shaders_only=True)
    assert hashlib.sha256((GAME/'DATA'/REL).read_bytes()).hexdigest()==sha
    (OUT/'report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
