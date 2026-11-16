"""Original Juni mesh, welded accidental hair UV offsets and a tangent normal map."""
import argparse,json,hashlib
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from build import ROOT,GAME,DataFolder,read_tree,write_tree,child,blob,arr,put,triangles,export
from repair_panel_normals import leaves
import darcy

OUT=ROOT/'out/juni_hair';REL='CHARACTERS/HEADS/pl_female4_head.dfm'
NORMAL=ROOT/'DATA_EXTRA/ROOM_MATERIALS/juni_hair_normal.png'
def sha(b):return hashlib.sha256(b).hexdigest()

def build():
    source=DataFolder(root=OUT/'original').data_path(REL).read_bytes()
    header,roots=read_tree(source);root=roots[0];report=[]
    for mesh in child(root,'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):continue
        geo=child(mesh,'Geometry');groups=child(mesh,'Face_groups')
        p=arr(geo,'Points','<f4',3);pi=arr(geo,'Point_indices','<u4').ravel()
        uv=arr(geo,'UV0','<f4',2);old=uv.copy();ui=arr(geo,'UV0_indices','<u4').ravel()
        hair=set();other=set()
        for group in groups.children:
            if not group.children:continue
            target=hair if blob(group,'Material_name').startswith(b'short_hair_pl_female4') else other
            target.update(v for t in triangles(group) for v in t)
        protected={int(ui[v]) for v in other};weld={}
        for v in hair:weld.setdefault(tuple(np.round(p[pi[v]],5)),set()).add(int(ui[v]))
        for indices in weld.values():
            indices=sorted(indices)
            if len(indices)<2 or any(i in protected for i in indices):continue
            samples=old[indices];spread=np.ptp(samples,axis=0)
            # Nearby copies are accidental splits inside one UV island.
            if np.linalg.norm(spread)<.035:
                uv[indices]=samples.mean(axis=0)
            # Keep the intentional wrap seam's U=0/1 split; align V only.
            elif samples[:,0].min()<.025 and samples[:,0].max()>.97 and spread[1]<.10:
                uv[indices,1]=samples[:,1].mean()
        assert np.array_equal(uv[sorted(protected)],old[sorted(protected)])
        put(geo,'UV0',uv.astype('<f4').tobytes())
        report.append(dict(lod=mesh.name,uv_fixed=int(np.any(uv!=old,axis=1).sum())))
    data=write_tree(header,roots)
    old={p:b for p,_,b in leaves(source)[1]};new={p:b for p,_,b in leaves(data)[1]}
    for path,value in old.items():
        if not path.endswith('/UV0'):assert new[path]==value,path
    # Texture-derived micro relief, separated from broad painted light and the
    # white streak's colour. RG stores tangent XY; B roughness, A profile mask.
    image=np.asarray(Image.open(BytesIO(blob(child(child(root,'Texture library'),'pl_female4_head03.TGA'),'MIP0'))).convert('RGB'),dtype=float)/255
    luminance=image@np.array([.299,.587,.114])
    height=gaussian_filter(luminance,.7)-gaussian_filter(luminance,4.0)
    dy,dx=np.gradient(height)
    yy,xx=np.indices(height.shape)
    # Fine straight fibres in UV space, modest compared to authored lock detail.
    dx=dx*12+.055*np.sin(xx*.75)
    dy=dy*12
    normal=np.stack([-dx,dy,np.ones_like(dx)],axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    packed=np.empty((*height.shape,4),dtype=np.uint8)
    packed[:,:,:2]=np.clip((normal[:,:,:2]*.5+.5)*255,0,255).astype(np.uint8)
    packed[:,:,2]=145;packed[:,:,3]=255
    NORMAL.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(packed).save(NORMAL)
    Image.fromarray(np.uint8(np.clip((normal*.5+.5)*255,0,255))).save(OUT/'normal_preview.png')
    assert np.isfinite(normal).all() and np.allclose(np.linalg.norm(normal,axis=-1),1)
    DataFolder(root=OUT/'stage').sync_data_file(REL,data)
    export(root,OUT/'after.json')
    previous=json.loads((OUT/'manifest.json').read_text())
    known=sorted(set(previous.get('known',[])+[previous['after']]))
    result=dict(before=sha(source),known=known,after=sha(data),normal_sha256=sha(NORMAL.read_bytes()),original_mesh=True,lods=report)
    (OUT/'manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    darcy.OUT=OUT;darcy.REL=REL
    darcy.install() if args.apply else build()
