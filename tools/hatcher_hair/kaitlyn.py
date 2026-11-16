"""Separate short, voluminous Kaitlyn concept; original head is never replaced."""
import argparse,json,struct,hashlib
from io import BytesIO
from datetime import datetime
import numpy as np
from PIL import Image
import darcy
from build import ROOT,GAME,DataFolder,read_tree,write_tree,child,blob,arr,put,triangles,faces,Node,export

OUT=ROOT/'out/kaitlyn_concept'
SOURCE='CHARACTERS/HEADS/br_kaitlyn_head.dfm'
REL='CHARACTERS/HEADS/br_kaitlyn_concept_head.dfm'
ASSET=ROOT/'tools/hatcher_hair/assets/kaitlyn_concept_hair_v1.png'

def face_shape(p):
    x,y,z=p;q=p.copy()
    # Gentle neutral-shape correction, concentrated on chin and cheeks;
    # retain the existing animation skeleton and facial skin weights.
    chin=np.exp(-((y+.052)/.012)**2)*np.exp(-(x/.035)**2)*np.clip((z-.055)/.025,0,1)
    q[1]+=.0035*chin;q[0]+=x*.08*chin
    cheek=np.exp(-((abs(x)-.045)/.013)**2)*np.exp(-((y-.005)/.022)**2)*np.clip((z-.045)/.035,0,1)
    q[0]+=np.sign(x)*.0015*cheek;q[2]+=.001*cheek
    return q

def prepare(root):
    atlas=np.asarray(Image.open(BytesIO(blob(child(child(root,'Texture library'),'br_kaitlyn_head01.tga'),'MIP0'))).convert('RGB'))/255.
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        geo=child(mesh,'Geometry');p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3)
        pi=arr(geo,'Point_indices','<u4').ravel()
        groups=child(mesh,'Face_groups');uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
        target=next((g for g in groups.children if g.children and blob(g,'Material_name').startswith(b'short_hair_')),None)
        if target:
            selected=triangles(target)
            def is_ear(t):
                pts=p[pi[t]]
                return min(abs(pts[:,0]))>.045 and pts[:,2].mean()>0 and max(pts[:,1])<.05 and max(pts[:,1])>-.01
            eartris=[t for t in selected if is_ear(t)]
            selected=[t for t in selected if not is_ear(t)]
            for group in groups.children:
                if not group.children or blob(group,'Material_name').rstrip(b'\0')!=b'br_kaitlyn_head01':continue
                kept=list(eartris)
                for t in triangles(group):
                    if is_ear(t):kept.append(t);continue
                    pts=p[pi[t]];samples=uv[ui[t]]
                    colours=[atlas[int((1-v)%1*(len(atlas)-1)),int(u%1*(atlas.shape[1]-1))] for u,v in list(samples)+[samples.mean(axis=0)]]
                    region=min(pts[:,1])>.07 or (max(pts[:,2])<.005 and min(abs(pts[:,0]))>.045) or max(pts[:,2])<-.025
                    hair=region and all(np.dot(c,[.299,.587,.114])<.58 and c[0]>c[2]*1.5 for c in colours)
                    (selected if hair else kept).append(t)
                faces(group,kept)
            faces(target,selected)
        hair={int(pi[v]) for g in child(mesh,'Face_groups').children if g.children and blob(g,'Material_name').startswith(b'short_hair_') for t in triangles(g) for v in t}
        skinpoints={int(pi[v]) for g in groups.children if g.children and not blob(g,'Material_name').startswith(b'short_hair_') for t in triangles(g) for v in t}
        for i,point in enumerate(p.copy()):
            if i in hair:
                # Compress the hanging hair into a rounded occipital cap.
                # This also moves boundary vertices before the protected-face
                # subdivision pass; otherwise a long strip survives at seams.
                ear_seam=point[1]>0 and abs(point[0])>.055 and point[2]>-.025
                if i not in skinpoints and point[2]<.005 and point[1]<.075 and not ear_seam:
                    depth=.075-point[1]
                    p[i,1]=.075-depth*.23
                    p[i,2]+=.020*np.clip(depth/.16,0,1)
                continue
            p[i]=face_shape(point)
            jac=np.column_stack([(face_shape(point+np.eye(3)[axis]*1e-5)-face_shape(point-np.eye(3)[axis]*1e-5))/2e-5 for axis in range(3)])
            normal=np.linalg.solve(jac.T,n[i]);n[i]=normal/max(np.linalg.norm(normal),1e-9)
        put(geo,'Points',p.astype('<f4').tobytes());put(geo,'Vertex_normals',n.astype('<f4').tobytes())

def sculpt(p,n,mask,level):
    x,y,z=p;q=p.copy();top=np.clip((y-.045)/.08,0,1)
    angle=np.arctan2(x,z+.012)
    waves=np.sin(angle*5+y*37)+.35*np.sin(angle*9-y*24)
    q+=n*mask*(.010*top+.006*waves*(1 if level<3 else .5))
    q[0]*=1+.17*mask*top
    q[1]+=.006*mask*top*np.exp(-((z-.025)/.08)**2)
    # Broader short curls around the sides, with the bulk above the ears.
    side=np.exp(-((y-.09)/.045)**2)
    q[0]+=np.sign(x)*.024*mask*side*np.clip((abs(x)-.025)/.035,0,1)
    q[2]-=.012*mask*side*np.clip((-z-.015)/.045,0,1)
    return q

def finish():
    stage=DataFolder(root=OUT/'stage');header,roots=read_tree(stage.data_path(REL).read_bytes());root=roots[0]
    texname='kaitlyn_concept_hair_v1.tga';matname='short_hair_kaitlyn_concept'
    texture=Node(texname);image=Image.open(ASSET).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS)
    for level in range(10):
        buffer=BytesIO();image.save(buffer,format='TGA');texture.children.append(Node('MIP'+str(level),buffer.getvalue()))
        image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.LANCZOS)
    child(root,'Texture library').children.append(texture)
    # Use the generated bitmap only on hair. Original face/eyes/teeth textures
    # remain byte-identical and cannot inherit the generated face in the atlas.
    material=child(child(root,'Material library'),'short_hair_br_kaitlyn_head01')
    material.name=matname;put(material,'Dt_name',(texname+'\0').encode())
    reports=[]
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        level=int(mesh.name[4:]);geo=child(mesh,'Geometry');groups=child(mesh,'Face_groups')
        target=next((g for g in groups.children if g.children and blob(g,'Material_name').startswith(b'short_hair_')),None)
        if target is None:continue
        put(target,'Material_name',(matname+'\0').encode())
        # The shortened cap exposes the inner nape triangles. Map those to
        # the existing neck skin, rather than the old brown hair underpainting.
        gp=arr(geo,'Points','<f4',3);gpi=arr(geo,'Point_indices','<u4').ravel()
        guv=arr(geo,'UV0','<f4',2);gui=arr(geo,'UV0_indices','<u4').ravel()
        atlas=np.asarray(Image.open(BytesIO(blob(child(child(root,'Texture library'),'br_kaitlyn_head01.tga'),'MIP0'))).convert('RGB'))/255.
        neckuv=[]
        for v in range(len(gpi)):
            pos=gp[gpi[v]];u,w=guv[gui[v]];c=atlas[int((1-w)%1*(len(atlas)-1)),int(u%1*(atlas.shape[1]-1))]
            if pos[1]<-.06 and pos[2]<0 and c.mean()>.48:neckuv.append(guv[gui[v]].copy())
        for group in groups.children:
            if not group.children or blob(group,'Material_name').rstrip(b'\0')!=b'br_kaitlyn_head01':continue
            for tri in triangles(group):
                pts=gp[gpi[tri]]
                if neckuv and max(pts[:,1])<.07 and max(pts[:,2])<0:
                    for v in tri:
                        u,w=guv[gui[v]];c=atlas[int((1-w)%1*(len(atlas)-1)),int(u%1*(atlas.shape[1]-1))]
                        if c.mean()<.43:guv[gui[v]]=np.mean(neckuv,axis=0)
        put(geo,'UV0',guv.astype('<f4').tobytes())
        p=arr(geo,'Points','<f4',3).tolist();n=arr(geo,'Vertex_normals','<f4',3).tolist();pi=arr(geo,'Point_indices','<u4').ravel().tolist()
        uv=arr(geo,'UV0','<f4',2).tolist();ui=arr(geo,'UV0_indices','<u4').ravel().tolist()
        has_uv1=any(v.name=='UV1' for v in geo.children)
        uv1=arr(geo,'UV1','<f4',2).tolist() if has_uv1 else [];ui1=arr(geo,'UV1_indices','<u4').ravel().tolist() if has_uv1 else []
        counts=arr(geo,'Point_bone_count','<u4').ravel();first=arr(geo,'Point_bone_first','<u4').ravel()
        ids=arr(geo,'Bone_id_chain','<u4').ravel();weights=arr(geo,'Bone_weight_chain','<f4').ravel()
        skin=[dict(zip(map(int,ids[f:f+c]),map(float,weights[f:f+c]))) for f,c in zip(first,counts)]
        # Trim the old hanging shell, including its protected neck seam.
        # Interpolate all vertex attributes at the cut rather than dragging
        # the shared ear/neck vertices up with the hair.
        old=[]
        def crossing(a,b):
            f=(.035-p[pi[a]][1])/(p[pi[b]][1]-p[pi[a]][1])
            ix=len(p);p.append(((1-f)*np.array(p[pi[a]])+f*np.array(p[pi[b]])).tolist())
            normal=(1-f)*np.array(n[pi[a]])+f*np.array(n[pi[b]])
            n.append((normal/max(np.linalg.norm(normal),1e-9)).tolist())
            influence={}
            for v,w in ((a,1-f),(b,f)):
                for bone,weight in skin[pi[v]].items():influence[bone]=influence.get(bone,0)+w*weight
            skin.append(influence);v=len(pi);pi.append(ix)
            ui.append(len(uv));uv.append(((1-f)*np.array(uv[ui[a]])+f*np.array(uv[ui[b]])).tolist())
            if has_uv1:
                ui1.append(len(uv1));uv1.append(((1-f)*np.array(uv1[ui1[a]])+f*np.array(uv1[ui1[b]])).tolist())
            return v
        for tri in triangles(target):
            poly=[]
            for a,b in zip(tri,tri[1:]+tri[:1]):
                ina=p[pi[a]][1]>=.035;inb=p[pi[b]][1]>=.035
                if ina:poly.append(a)
                if ina!=inb:poly.append(crossing(a,b))
            for k in range(1,len(poly)-1):old.append([poly[0],poly[k],poly[k+1]])
        # The retail mesh has no complete skull behind the long hair.
        # Close the exposed rear head/neck with a skinned opaque surface.
        facegroup=next(g for g in groups.children if g.children and blob(g,'Material_name').rstrip(b'\0')==b'br_kaitlyn_head01')
        face_tris=[]
        ring_start=len(pi);segments=20
        source_points=np.asarray(p).copy()
        for y,rx,rz in [(-.095,.038,.060),(-.065,.037,.059),(-.025,.044,.064),(.015,.057,.075),(.055,.063,.079)]:
            for j in range(segments+1):
                a=-np.pi/2+np.pi*j/segments
                pos=np.array([rx*np.sin(a),y,.025-rz*np.cos(a)])
                normal=np.array([np.sin(a)/rx,0,-np.cos(a)/rz]);normal/=np.linalg.norm(normal)
                nearest=int(np.argmin(np.linalg.norm(source_points-pos,axis=1)))
                ix=len(p);p.append(pos.tolist());n.append(normal.tolist());skin.append(dict(skin[nearest]));pi.append(ix)
                ui.append(len(uv));uv.append(np.mean(neckuv,axis=0).tolist() if neckuv else [.5,.15])
                if has_uv1:ui1.append(len(uv1));uv1.append(uv[-1])
        for row in range(4):
            for j in range(segments):
                a=ring_start+row*(segments+1)+j;b=a+1;c=a+segments+1;d=c+1
                for tri in ([a,b,c],[b,d,c]):
                    pts=np.asarray([p[pi[v]] for v in tri]);normal=np.asarray([n[pi[v]] for v in tri]).mean(axis=0)
                    if np.dot(np.cross(pts[1]-pts[0],pts[2]-pts[0]),normal)<0:tri.reverse()
                    face_tris.append(tri)
        faces(facegroup,face_tris)
        nape_patch=[t for t in face_tris if min(p[pi[v]][1] for v in t)>=.015]
        combined=list(old);pp=np.asarray(p);nn=np.asarray(n);candidates=[]
        for t in old:
            ix=[pi[v] for v in t];center=pp[ix].mean(axis=0)
            if center[1]<.045:continue
            normal=nn[ix].mean(axis=0);normal/=max(np.linalg.norm(normal),1e-9)
            candidates.append((center,normal,t))
        candidates.sort(key=lambda v:float(np.sin(np.dot(v[0],[1337,1777,2111]))))
        placed=[];limit=(36,20,10,0,0,0)[level];steps=(16,10,6,6,6,6)[level];sides=(10,8,6,6,6,6)[level]
        if not limit:candidates=[]
        for center,normal,t in candidates:
            if any(np.linalg.norm(center-c)<.030 for c in placed):continue
            placed.append(center)
            center=center.copy()
            if center[2]>.045 and center[1]>.11:
                # Let the front wave fall toward the forehead as in the art,
                # instead of retaining the original swept-back pompadour.
                center[1]-=.018;center[2]+=.006
            tangent=np.cross(normal,[0,1,0])
            if np.linalg.norm(tangent)<.1:tangent=np.cross(normal,[1,0,0])
            tangent/=np.linalg.norm(tangent);vertical=np.cross(tangent,normal)
            influence={}
            for v in t:
                for bone,w in skin[pi[v]].items():influence[bone]=influence.get(bone,0)+w/3
            baseuv=np.mean([uv[ui[v]] for v in t],axis=0)
            baseuv1=np.mean([uv1[ui1[v]] for v in t],axis=0) if has_uv1 else None
            start=len(pi);path=[]
            # Rounded C/S-shaped curls with tapered ends, anchored in the cap.
            for k in range(steps+1):
                f=k/steps;angle=-1.5+f*3.5;radius=.023*(1-.28*f)
                path.append(center+tangent*np.cos(angle)*radius+vertical*np.sin(angle)*radius+normal*(.002*np.sin(np.pi*f)-.008))
            for k,centerline in enumerate(path):
                direction=path[min(k+1,steps)]-path[max(k-1,0)];direction/=max(np.linalg.norm(direction),1e-9)
                axis=np.cross(direction,normal);axis/=max(np.linalg.norm(axis),1e-9);other=np.cross(axis,direction)
                f=k/steps;width=.010*(.08+.92*np.sin(np.pi*f)**.6)
                for j in range(sides):
                    a=j/sides*2*np.pi;radial=axis*np.cos(a)+other*np.sin(a)
                    offset=axis*np.cos(a)*width+other*np.sin(a)*width*.4
                    shading=axis*np.cos(a)*.4+other*np.sin(a);shading/=max(np.linalg.norm(shading),1e-9)
                    ix=len(p);p.append((centerline+offset-normal*.001).tolist());n.append(shading.tolist());skin.append(dict(influence))
                    pi.append(ix);ui.append(len(uv));uv.append((baseuv+np.array([(j/sides-.5)*.07,(f-.5)*.13])).tolist())
                    if has_uv1:ui1.append(len(uv1));uv1.append(baseuv1.tolist())
            for k in range(steps):
                for j in range(sides):
                    a=start+k*sides+j;b=start+k*sides+(j+1)%sides;c=start+(k+1)*sides+j;d=start+(k+1)*sides+(j+1)%sides
                    for tri in ([a,b,c],[b,d,c]):
                        ps=np.asarray([p[pi[v]] for v in tri]);ns=np.asarray([n[pi[v]] for v in tri])
                        if np.dot(np.cross(ps[1]-ps[0],ps[2]-ps[0]),ns.mean(axis=0))<0:tri.reverse()
                        combined.append(tri)
            if len(placed)>=limit:break
        # Rebuild the continuous face and ears from the prepared source. This
        # avoids cracks from independently selecting deformed ear triangles.
        _,original_roots=read_tree((OUT/'original/DATA'/REL).read_bytes())
        _,prepared_roots=read_tree((OUT/'original/DATA'/REL).read_bytes());prepare(prepared_roots[0])
        prepared_mesh=child(child(prepared_roots[0],'MultiLevel'),mesh.name)
        hair_source={tuple(t) for g in child(prepared_mesh,'Face_groups').children if g.children and blob(g,'Material_name').startswith(b'short_hair_') for t in triangles(g)}
        original_mesh=child(child(original_roots[0],'MultiLevel'),mesh.name);og=child(original_mesh,'Geometry')
        face_tris=list(nape_patch)
        op=arr(og,'Points','<f4',3);on=arr(og,'Vertex_normals','<f4',3);opi=arr(og,'Point_indices','<u4').ravel()
        ouv=arr(og,'UV0','<f4',2);oui=arr(og,'UV0_indices','<u4').ravel()
        of=arr(og,'Point_bone_first','<u4').ravel();oc=arr(og,'Point_bone_count','<u4').ravel()
        ob=arr(og,'Bone_id_chain','<u4').ravel();ow=arr(og,'Bone_weight_chain','<f4').ravel()
        neck_samples=[]
        for v in range(len(opi)):
            k=int(opi[v]);u,w=ouv[oui[v]];colour=atlas[int((1-w)%1*(len(atlas)-1)),int(u%1*(atlas.shape[1]-1))]
            if op[k,1]<.025 and op[k,2]<.04 and colour.mean()>.50:
                neck_samples.append((op[k].copy(),on[k].copy(),ouv[oui[v]].copy()))
        for group in child(original_mesh,'Face_groups').children:
            if not group.children or blob(group,'Material_name').rstrip(b'\0')!=b'br_kaitlyn_head01':continue
            for tri in triangles(group):
                pts=op[opi[tri]]
                ear=min(abs(pts[:,0]))>.045 and pts[:,2].mean()>.005 and min(pts[:,1])>-.02 and max(pts[:,1])<.08
                if tuple(tri) in hair_source and min(pts[:,1])>.035 and not ear:continue
                added=[]
                for v in tri:
                    k=int(opi[v]);ix=len(p);pos=face_shape(op[k]);normal=on[k].copy();tex=ouv[oui[v]].copy()
                    ear_vertex=abs(pos[0])>.05 and pos[2]>-.01 and pos[1]>-.02
                    if not ear_vertex and pos[2]<.018 and pos[1]<.065 and (abs(pos[0])>.045 or pos[2]<-.03):
                        u,w=tex;colour=atlas[int((1-w)%1*(len(atlas)-1)),int(u%1*(atlas.shape[1]-1))]
                        if neck_samples and (colour.mean()<.46 or abs(pos[0])>.060):
                            dest,normal,tex=min(neck_samples,key=lambda s:np.linalg.norm((s[0]-pos)*[1,2,1]))
                            pos=dest+normal*.0001
                    p.append(pos.tolist());n.append(normal.tolist())
                    f,c=of[k],oc[k];skin.append(dict(zip(map(int,ob[f:f+c]),map(float,ow[f:f+c]))))
                    added.append(len(pi));pi.append(ix);ui.append(len(uv));uv.append(tex.tolist())
                    if has_uv1:ui1.append(len(uv1));uv1.append(uv[-1])
                face_tris.append(added)
        faces(facegroup,face_tris)
        combined=[t for t in combined if not (min(abs(np.asarray([p[pi[v]] for v in t])[:,0]))>.055 and np.asarray([p[pi[v]] for v in t])[:,2].mean()>0 and np.asarray([p[pi[v]] for v in t])[:,1].mean()<.07)]
        faces(target,combined)
        for name,value,kind in [('Points',p,'<f4'),('Vertex_normals',n,'<f4'),('Point_indices',pi,'<u4'),('UV0',uv,'<f4'),('UV0_indices',ui,'<u4')]:put(geo,name,np.asarray(value,dtype=kind).tobytes())
        if has_uv1:put(geo,'UV1',np.asarray(uv1,dtype='<f4').tobytes());put(geo,'UV1_indices',np.asarray(ui1,dtype='<u4').tobytes())
        starts=[];counts=[];ids=[];weights=[]
        for influence in skin:
            assert abs(sum(influence.values())-1)<1e-4
            starts.append(len(ids));counts.append(len(influence));ids.extend(influence);weights.extend(influence.values())
        for name,value,kind in [('Point_bone_first',starts,'<u4'),('Point_bone_count',counts,'<u4'),('Bone_id_chain',ids,'<u4'),('Bone_weight_chain',weights,'<f4')]:put(geo,name,np.asarray(value,dtype=kind).tobytes())
        assert len(pi)<65536 and np.isfinite(p).all() and np.isfinite(n).all()
        reports.append(dict(lod=level,curls=len(placed),hair_triangles=len(combined)))
    data=write_tree(header,roots);stage.sync_data_file(REL,data);export(root,OUT/'concept.json')
    (OUT/'concept_manifest.json').write_text(json.dumps(dict(file=REL,sha256=hashlib.sha256(data).hexdigest(),lods=reports),indent=2))
    print(json.dumps(reports))

def build():
    OUT.mkdir(parents=True,exist_ok=True);baseline=DataFolder(root=OUT/'original')
    if not baseline.data_path(REL).exists():baseline.sync_data_file(REL,(GAME/'DATA'/SOURCE).read_bytes())
    darcy.OUT=OUT;darcy.REL=REL;darcy.HAIR_PREFIX=b'short_hair_br_kaitlyn'
    darcy.PREPARE=prepare;darcy.SCULPT=sculpt;darcy.FOLDED_LOCKS=False;darcy.SUBDIVISION_DEPTH=(2,1,0,0,0,0)
    darcy.build();finish()

if __name__=='__main__':build()
