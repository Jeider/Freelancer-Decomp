"""Refine relief from prototype 1, without the rejected silhouette changes."""
from pathlib import Path
from io import BytesIO
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder,read_tree,write_tree,child,blob,arr,put,triangles,export
BASE=ROOT/'out/reichman_body_test';OUT=ROOT/'out/reichman_body_test_v3';REL='CHARACTERS/BODIES/rh_reichman_body.dfm'
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    live=(GAME/'DATA'/REL).read_bytes();source=(BASE/'stage/DATA'/REL).read_bytes()
    DataFolder(root=OUT/'original').sync_data_file(REL,live)
    header,roots=read_tree(source);root=roots[0]
    _,original=read_tree(live);export(original[0],OUT/'before.json')
    maps={};heights={}
    for mat in child(root,'Material library').children:
        if not mat.children:continue
        tex=blob(mat,'Dt_name').rstrip(b'\0').decode()
        im=Image.open(BytesIO(blob(child(child(root,'Texture library'),tex),'MIP0'))).convert('RGB')
        rgb=np.asarray(im,dtype=float)/255;r,g,b=np.moveaxis(rgb,-1,0)
        red=smooth(.10,.35,r-g)*smooth(.08,.3,r-b)
        gold=smooth(.06,.24,r-b)*smooth(.03,.18,g-b)*(1-red)
        lum=im.convert('L')
        blur=lambda radius:np.asarray(lum.filter(ImageFilter.GaussianBlur(radius)),float)/255
        fine=blur(.7)-blur(2.3);medium=blur(1.5)-blur(6)
        # Band-limited ornament relief. Broad painted illumination is excluded.
        dy,dx=np.gradient(fine*(2+gold*7+red*.5)+medium*(gold*18+red*4))
        normal=np.stack((-dx,dy,np.ones_like(dx)),-1);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
        normalpath=OUT/(tex+'_normal.png');Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255)).save(normalpath)
        maps[mat.name]=dict(normal=str(normalpath),surface=str(BASE/(tex+'_surface.png')))
        heights[mat.name]=np.clip((blur(3)-blur(12))*gold*.012,-.0015,.0015)
    reports=[]
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        lod=int(mesh.name[4:]);geo=child(mesh,'Geometry');p=arr(geo,'Points','<f4',3);n=arr(geo,'Vertex_normals','<f4',3)
        if lod>1:continue
        pi=arr(geo,'Point_indices','<u4').ravel();uv=arr(geo,'UV0','<f4',2);ui=arr(geo,'UV0_indices','<u4').ravel()
        values={};edges={};keys=[tuple(np.round(x,6)) for x in p]
        for group in child(mesh,'Face_groups').children:
            if not group.children:continue
            name=blob(group,'Material_name').rstrip(b'\0').decode();height=heights[name]
            for tri in triangles(group):
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    edge=tuple(sorted((keys[pi[a]],keys[pi[b]])));edges[edge]=edges.get(edge,0)+1
                for v in tri:
                    i=pi[v];x,y,z=p[i];u,w=uv[ui[v]]
                    # Only raised gold trim, away from arm joints and seams.
                    focus=(y>.49 and abs(x)>.14) or (.27<y<.49 and abs(x)<.16)
                    h=height[int(np.clip(1-w,0,1)*(len(height)-1)),int(np.clip(u,0,1)*(height.shape[1]-1))] if focus else 0.
                    values.setdefault(keys[i],[]).append(h)
        boundary={v for edge,count in edges.items() if count==1 for v in edge}
        buckets={}
        for i,key in enumerate(keys):buckets.setdefault(key,[]).append(i)
        q=p.copy()
        for key,indices in buckets.items():
            if key in boundary or key not in values:continue
            height=float(np.mean(values[key]))*(1 if lod==0 else .5)
            direction=n[indices].mean(axis=0);direction/=max(np.linalg.norm(direction),1e-9)
            q[indices]+=direction*height
        put(geo,'Points',q.astype('<f4').tobytes())
        reports.append(dict(lod=lod,max_delta_from_v1_m=float(np.linalg.norm(q-p,axis=1).max()),boundary_vertices_fixed=True))
    data=write_tree(header,roots);DataFolder(root=OUT/'stage').sync_data_file(REL,data);export(root,OUT/'after.json')
    (OUT/'preview_materials.json').write_text(json.dumps(maps,indent=2))
    report=dict(source_sha256=hashlib.sha256(live).hexdigest(),prototype_sha256=hashlib.sha256(data).hexdigest(),base='first prototype',base_sha256=hashlib.sha256(source).hexdigest(),local_refinement=reports)
    (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    assert (GAME/'DATA'/REL).read_bytes()==live
if __name__=='__main__':main()
