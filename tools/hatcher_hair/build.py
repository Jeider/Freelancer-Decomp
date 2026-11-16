"""Hair-only DFM refinement; retain face triangles, UV deformation and skeleton."""
from pathlib import Path
from io import BytesIO
import importlib.util, json, sys, struct, hashlib
import numpy as np
from PIL import Image
from locks import add_locks

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from generate_station_lods import read_tree,write_tree,Node
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/hatcher_hair'
REL='CHARACTERS/HEADS/li_hatcher_head.dfm'
spec=importlib.util.spec_from_file_location('data_folder',GAME/'Assets/Pythonlancer/tools/data_folder.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
DataFolder=module.DataFolder

def child(node,name):return next(n for n in node.children if n.name==name)
def blob(node,name):return child(node,name).blob
def arr(node,name,kind,width=1):return np.frombuffer(blob(node,name),dtype=kind).copy().reshape(-1,width)
def put(node,name,value):child(node,name).blob=value
def strand_normal(p,n,mask,level):
    x,y,z=p
    # Mirror the strand field, not the hairstyle. Both sides get equal relief.
    across=np.sqrt(x*x+.000004)
    phase=across*230+y*130+z*110+1.2*np.sin(across*27)
    gradient=np.array([(230+32.4*np.cos(across*27))*x/across,130.,110.])
    tangent=gradient-n*np.dot(gradient,n)
    tangent/=max(np.linalg.norm(tangent),1e-9)
    strength=(1.,.65,.3,0.,0.,0.)[level]*mask
    strand=(.46*np.sin(phase)+.09*np.sin(phase*2+.4))*strength
    shaded=n-tangent*strand
    return shaded/np.linalg.norm(shaded)
def triangles(group):
    names={n.name for n in group.children}
    if 'Face_indices' in names:return arr(group,'Face_indices','<u2',3).tolist()
    ix=arr(group,'Tristrip_indices','<u2').ravel();out=[]
    for i in range(2,len(ix)):
        f=[int(x) for x in ix[i-2:i+1]]
        if len(set(f))<3:continue
        if i%2:f[0],f[1]=f[1],f[0]
        out.append(f)
    return out
def faces(group,values):
    group.children=[n for n in group.children if n.name not in ('Tristrip_indices','Face_indices')]
    group.children.append(Node('Face_indices',np.asarray(values,dtype='<u2').tobytes()))

def export(root,target):
    mesh=child(child(root,'MultiLevel'),'Mesh0');geo=child(mesh,'Geometry')
    result=dict(points=arr(geo,'Points','<f4',3).tolist(),normals=arr(geo,'Vertex_normals','<f4',3).tolist(),point_indices=arr(geo,'Point_indices','<u4').ravel().tolist(),
                uv_indices=arr(geo,'UV0_indices','<u4').ravel().tolist(),uv=arr(geo,'UV0','<f4',2).tolist(),groups=[])
    mats=child(root,'Material library');textures=child(root,'Texture library')
    for group in child(mesh,'Face_groups').children:
        if not group.children:continue
        name=blob(group,'Material_name').rstrip(b'\0').decode();mat=child(mats,name)
        tex=next((n.blob.rstrip(b'\0').decode() for n in mat.children if n.name=='Dt_name'),None)
        path=None
        if tex:
            path=target.with_name(tex+'.png');Image.open(BytesIO(blob(child(textures,tex),'MIP0'))).save(path)
        result['groups'].append(dict(name=name,texture=str(path) if path else None,faces=triangles(group)))
    target.write_text(json.dumps(result))

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=OUT/'original.dfm'
    if not baseline.exists():baseline.write_bytes((GAME/'DATA'/REL).read_bytes())
    source=baseline.read_bytes();header,roots=read_tree(source);root=roots[0]
    export(root,OUT/'before.json')
    original_image=Image.open(BytesIO(blob(child(child(root,'Texture library'),'li_hatcher_head02.TGA'),'MIP0'))).convert('RGB')
    pixels=np.asarray(original_image)/255.;height,width=pixels.shape[:2]
    def hair_uv(uv):
        u,v=uv; rgb=pixels[int((1-v)%1*(height-1)),int(u%1*(width-1))]
        return rgb[0]>rgb[1]*1.55 and rgb[0]>rgb[2]*2.0
    report=[]
    for lod in child(root,'MultiLevel').children:
        if not lod.name.startswith('Mesh'):continue
        level=int(lod.name[4:]);geo=child(lod,'Geometry');groups=child(lod,'Face_groups')
        points=arr(geo,'Points','<f4',3);normals=arr(geo,'Vertex_normals','<f4',3)
        pi=arr(geo,'Point_indices','<u4').ravel();ui=arr(geo,'UV0_indices','<u4').ravel();uv=arr(geo,'UV0','<f4',2)
        uv1=arr(geo,'UV1','<f4',2);ui1=arr(geo,'UV1_indices','<u4').ravel()
        target=next(g for g in groups.children if g.children and blob(g,'Material_name').rstrip(b'\0')==b'li_hatcher_head01')
        original_faces=triangles(target);hair=[];face=[]
        for tri in original_faces:
            samples=[uv[ui[x]] for x in tri]
            # Conservative classification: never replace a triangle crossing the skin/hair boundary.
            is_hair=(min(points[pi[tri],1])>.12 or
                     all(hair_uv(s) for s in samples+[np.mean(samples,axis=0)]))
            (hair if is_hair else face).append(tri)
        protected=set(int(pi[x]) for g in groups.children if g.children for tri in (face if g is target else triangles(g)) for x in tri)
        # DFM duplicates points at UV seams. Sculpt those copies as one surface.
        weld={}
        for i,p in enumerate(points):weld.setdefault(tuple(np.round(p,5)),[]).append(i)
        shape_points=points.copy();shape_normals=normals.copy()
        for copies in weld.values():
            if any(i in protected for i in copies):protected.update(copies)
            else:
                shape_points[copies]=points[copies].mean(axis=0)
                n=normals[copies].mean(axis=0);n/=max(np.linalg.norm(n),1e-9)
                shape_normals[copies]=n
        counts=arr(geo,'Point_bone_count','<u4').ravel();ids=arr(geo,'Bone_id_chain','<u4').ravel();weights=arr(geo,'Bone_weight_chain','<f4').ravel()
        skin=[];cursor=0
        for count in counts:
            skin.append(dict(zip(map(int,ids[cursor:cursor+count]),map(float,weights[cursor:cursor+count]))));cursor+=count
        outp=points.tolist();outn=normals.tolist();outpi=pi.tolist();outui=ui.tolist();outuv=uv.tolist();outuv1=uv1.tolist();outui1=ui1.tolist()
        original_count=len(points);generated=[];emitted={};frozen=set(protected)
        hair_masks=[0. if i in protected else 1. for i in range(len(points))]
        def deform(p,n,mask):
            x,y,z=p
            high=np.clip((y-.065)/.09,0,1)
            # Sculpt the existing closed surface, so every lock joins the scalp.
            # Taper the rear mass and sides while keeping the hairline fixed.
            rear=np.clip((-z+.005)/.07,0,1)
            p=p.copy()
            p[0]*=1-mask*high*(.20+.06*rear)
            p[2]+=mask*rear*.014*np.clip((y+.015)/.09,0,1)
            crown=np.clip((y-.115)/.045,0,1)
            phase=x*230+z*70+1.2*np.sin(x*27)
            wave=max(0.,1-abs((phase/(2*np.pi))%1-.5)*5)
            ridge=(wave-.28)*.009*high
            p=p+n*ridge*mask
            # Broad roots rise into swept tips at the crown instead of added cones.
            p[1]+=mask*crown*(-.006+.004*np.sin(x*32+.7)+.007*wave)
            p[1]+=mask*crown*.010*np.exp(-((z+.018)/.038)**2)
            p[2]-=mask*crown*(.007+.006*wave)
            # Lower the hairstyle by roughly a quarter above the fixed hairline.
            p[1]-=mask*.26*max(0.,p[1]-.090)
            # Pull the overhanging front lock back, fading into the fixed hairline.
            front=np.clip((z-.025)/.065,0.,1.)
            front=front*front*(3.-2.*front)
            p[2]-=mask*.009*front*np.clip((y-.075)/.045,0.,1.)
            p[1]+=mask*.005*front*np.clip((y-.075)/.045,0.,1.)
            return p
        for index in range(original_count):
            if index not in protected:outp[index]=deform(shape_points[index].copy(),shape_normals[index],1).tolist()
        def emit(tri,bary):
            verts=[]
            for b in bary:
                exact=np.flatnonzero(b>.999999)
                if len(exact):verts.append(tri[int(exact[0])]);continue
                key=tuple(sorted((tri[k],round(float(b[k]),6)) for k in range(3) if b[k]>0))
                if key in emitted:verts.append(emitted[key]);continue
                pp=shape_points[pi[tri]];nn=shape_normals[pi[tri]];p=b@pp;n=b@nn;n/=max(np.linalg.norm(n),1e-9)
                mask=float(sum(b[k] for k in range(3) if int(pi[tri[k]]) not in protected))
                # Phong tessellation rounds the low-poly cap but fades out at untouched face edges.
                projected=np.array([p-nn[k]*np.dot(p-pp[k],nn[k]) for k in range(3)])
                p=p+(b@projected-p)*(.25*mask)
                p=deform(p,n,mask)
                point_index=len(outp);outp.append(p.tolist());outn.append(n.tolist())
                hair_masks.append(mask)
                if mask<1e-6:frozen.add(point_index)
                influence={}
                for k in range(3):
                    for bone,weight in skin[int(pi[tri[k]])].items():influence[bone]=influence.get(bone,0)+float(b[k])*weight
                influence={bone:w for bone,w in influence.items() if w>1e-7}
                total=sum(influence.values());skin.append({bone:w/total for bone,w in influence.items()})
                emitted[key]=len(outpi)
                verts.append(len(outpi));outpi.append(point_index);outui.append(len(outuv));outuv.append((b@uv[ui[tri]]).tolist())
                outui1.append(len(outuv1));outuv1.append((b@uv1[ui1[tri]]).tolist())
            generated.append(verts)
        def subdiv(tri,bary,depth):
            if depth==0:emit(tri,bary);return
            a,b,c=bary;ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
            for sub in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)):subdiv(tri,np.array(sub),depth-1)
        for tri in hair:subdiv(tri,np.eye(3),3 if level==0 else 2 if level==1 else 1 if level==2 else 0)
        if level<3:
            # Relax small tessellation irregularities on the welded surface.
            keys=[tuple(np.round(p,5)) for p in outp];members={};neighbors={}
            for tri in generated:
                ids3=[outpi[v] for v in tri]
                for v in ids3:
                    k=keys[v];members.setdefault(k,set()).add(v)
                    neighbors.setdefault(k,set()).update(keys[w] for w in ids3 if keys[w]!=k)
            fixed={keys[v] for v in frozen};values={k:np.mean([outp[v] for v in ids],axis=0) for k,ids in members.items()}
            for iteration in range(1):
                updated={}
                for k,p in values.items():
                    updated[k]=p if k in fixed or not neighbors[k] else p*.6+np.mean([values[w] for w in neighbors[k]],axis=0)*.4
                values=updated
            for k,ids in members.items():
                if k not in fixed:
                    for v in ids:outp[v]=values[k].tolist()
        # Smooth geometric normals across UV seams; keep all face normals untouched.
        position_keys=[tuple(np.round(p,6)) for p in outp];normal_sum={}
        for tri in generated:
            ids3=[outpi[v] for v in tri];a,b,c=[np.asarray(outp[v]) for v in ids3]
            normal=np.cross(b-a,c-a)
            if np.dot(normal,np.mean([outn[v] for v in ids3],axis=0))<0:normal=-normal
            for v in ids3:
                key=position_keys[v];normal_sum[key]=normal_sum.get(key,np.zeros(3))+normal
        for v in set(outpi[x] for tri in generated for x in tri)-protected:
            n=normal_sum[position_keys[v]];length=np.linalg.norm(n)
            if length>1e-10:
                n=n/length
                # Directional strand normals, consumed by native DFM lighting.
                # Perturb only the tangent component; no new texture/shader pass.
                shaded=strand_normal(outp[v],n,hair_masks[v],level)
                assert np.dot(shaded,n)>.86
                outn[v]=shaded.tolist()
        lock_count=add_locks(outp,outn,outpi,outuv,outui,outuv1,outui1,skin,hair_masks,generated,level)
        faces(target,face)
        hair_group=Node('Group'+str(len([g for g in groups.children if g.children])))
        hair_group.children=[Node('Material_name',b'hatcher_hair_v1\0')];faces(hair_group,generated);groups.children.append(hair_group)
        put(groups,'Count',struct.pack('<I',len([g for g in groups.children if g.children])))
        assert len(outpi)<65536
        for name,value,kind in [('Points',outp,'<f4'),('Vertex_normals',outn,'<f4'),('Point_indices',outpi,'<u4'),('UV0',outuv,'<f4'),('UV0_indices',outui,'<u4'),('UV1',outuv1,'<f4'),('UV1_indices',outui1,'<u4')]:put(geo,name,np.asarray(value,dtype=kind).tobytes())
        first=[];newids=[];newweights=[];newcounts=[]
        for influence in skin:
            first.append(len(newids));newcounts.append(len(influence));newids.extend(influence);newweights.extend(influence.values())
        for name,value,kind in [('Point_bone_first',first,'<u4'),('Point_bone_count',newcounts,'<u4'),('Bone_id_chain',newids,'<u4'),('Bone_weight_chain',newweights,'<f4')]:put(geo,name,np.array(value,dtype=kind).tobytes())
        # Every original non-hair point stays byte-identical; facial animation tables remain intact.
        actual=arr(geo,'Points','<f4',3)
        assert np.array_equal(actual[list(protected)],points[list(protected)])
        if level<3:
            motion=np.asarray(hair_masks,dtype=np.float32)**2
            motion*=np.clip((actual[:,1]-.065)/.075,0,1)**2
            motion*=(1.,.65,.25)[level]
            totals={}
            for v,w in enumerate(motion):
                for bone,bw in skin[v].items():totals[bone]=totals.get(bone,0)+w*bw
            bone=max(totals,key=totals.get)
            geo.children.extend([Node('Hair_motion_weights',motion.astype('<f4').tobytes()),Node('Hair_motion_bone',struct.pack('<I',bone))])
        report.append(dict(lod=level,hair_before=len(hair),hair_after=len(generated),folded_locks=lock_count,points_before=original_count,points_after=len(outp),protected_points=len(protected)))
    mat=Node('hatcher_hair_v1');mat.children=[Node('Type',b'DcDt\0'),Node('Dt_name',b'hatcher_hair_v1.tga\0'),Node('Dt_flags',struct.pack('<I',64))]
    materials=child(root,'Material library');materials.children.append(mat);put(materials,'Material count',struct.pack('<I',len([m for m in materials.children if m.children])))
    tex=Node('hatcher_hair_v1.tga')
    image=Image.open(ROOT/'tools/hatcher_hair/assets/hair_atlas_v1.png').convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    level=0
    while True:
        buffer=BytesIO();image.save(buffer,format='TGA');tex.children.append(Node('MIP'+str(level),buffer.getvalue()))
        # Native LoadTgaTexture accepts exactly one digit after MIP (0..9).
        # A 1024px texture must stop at 2px; MIP10 rejects the entire texture.
        if image.width==1 or level==9:break
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.LANCZOS);level+=1
    child(root,'Texture library').children.append(tex)
    output=write_tree(header,roots);DataFolder(root=OUT/'stage').sync_data_file(REL,output)
    export(root,OUT/'after.json')
    (OUT/'report.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),lods=report),indent=2))
    print(json.dumps(report))

if __name__=='__main__':build()
