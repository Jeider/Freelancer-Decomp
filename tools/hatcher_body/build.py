"""Offline Hatcher costume detail study: change Mesh0 only."""
from pathlib import Path
import sys,importlib.util,json,copy,hashlib
from io import BytesIO
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
# Reuse the checked triangulation/weight interpolation implementation only.
# All costume shaping and materials below are Hatcher-specific callbacks.
spec=importlib.util.spec_from_file_location('body_mesh_engine',ROOT/'tools/reichman_body/build_shape_rejected.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
from build import child,blob,put,export,read_tree,GAME
from repair_panel_normals import leaves
OUT=ROOT/'out/hatcher_body_test';REL='CHARACTERS/BODIES/li_hatcher_body.dfm'
smooth=engine.smooth

def masks(rgb):
    r,g,b=np.moveaxis(rgb,-1,0)
    leather=smooth(.025,.18,r-b)*smooth(.005,.10,g-b)
    brass=smooth(.12,.32,r-b)*smooth(.10,.28,g-b)*smooth(.25,.55,(r+g)*.5)
    return leather,brass

def preview_export(root,path):
    # DFM lookup is case-insensitive. Do not rewrite native material strings
    # merely because the generic preview exporter uses case-sensitive lookup.
    temp=copy.deepcopy(root);textures=child(temp,'Texture library')
    for mat in child(temp,'Material library').children:
        if not mat.children:continue
        name=blob(mat,'Dt_name').rstrip(b'\0').decode()
        actual=next(t.name for t in textures.children if t.name.lower()==name.lower())
        put(mat,'Dt_name',(actual+'\0').encode())
    export(temp,path)

def relief(p,n,uv,mat,atlas,lod):
    if lod!=0:return np.zeros(3)
    x,y,z=p;leather,brass=masks(engine.sample(atlas,uv))
    upper=smooth(.18,.27,y)*(1-smooth(.49,.56,y))
    torso=1-smooth(.145,.22,abs(x))
    # Existing collar and vest binding, not a larger shoulder silhouette.
    binding=.0055*leather*upper
    clasp=.004*brass*upper*torso
    belt=np.exp(-((y-.095)/.045)**2)*torso
    belt_relief=.0035*leather*belt
    cuff=np.exp(-((y-.12)/.085)**2)*smooth(.18,.25,abs(x))
    cuff_relief=.0035*leather*cuff
    boot_top=np.exp(-((y+.55)/.045)**2)
    boot_ankle=np.exp(-((y+.82)/.045)**2)
    boot_relief=leather*(.003*boot_top+.0015*boot_ankle)
    # Gently round the existing boot flap; avoid puffing up the blue fabric.
    flap=0.
    if mat=='hatcher_body_3' and y<-.45 and uv[0]<.64:
        flap=.002*leather*np.sin(np.pi*np.clip((uv[0]-.10)/.5,0,1))**2
    return n*(binding+clasp+belt_relief+cuff_relief+boot_relief+flap)

def surface_maps(root):
    maps={};atlases={};textures=child(root,'Texture library')
    for mat in child(root,'Material library').children:
        if not mat.children:continue
        name=blob(mat,'Dt_name').rstrip(b'\0').decode()
        tex=next(t for t in textures.children if t.name.lower()==name.lower())
        im=Image.open(BytesIO(blob(tex,'MIP0'))).convert('RGB')
        rgb=np.asarray(im,float)/255;leather,brass=masks(rgb)
        atlases[mat.name]=np.asarray(im.filter(ImageFilter.GaussianBlur(5)),float)/255
        luma=im.convert('L');blur=lambda radius:np.asarray(luma.filter(ImageFilter.GaussianBlur(radius)),float)/255
        # Medium leather grooves and seam relief; suppress textile grain.
        height=(blur(1.4)-blur(5.5))*(.5+leather*8+brass*2)
        dy,dx=np.gradient(height);normal=np.stack((-dx,dy,np.ones_like(dx)),-1);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
        normpath=OUT/(tex.name+'_normal.png');Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255)).save(normpath)
        rough=.82*(1-leather)+.56*leather-.12*brass
        material=np.stack((rough,.30*brass,np.zeros_like(rough)),-1)
        surfpath=OUT/(tex.name+'_surface.png');Image.fromarray(np.uint8(np.clip(material,0,1)*255)).save(surfpath)
        maps[mat.name]=dict(normal=str(normpath),surface=str(surfpath))
    return maps,atlases

def main():
    engine.OUT=OUT;engine.REL=REL;engine.ACTIVE_LODS=(0,)
    engine.relief=relief;engine.surface_maps=surface_maps;engine.export=preview_export
    engine.main()
    source=(GAME/'DATA'/REL).read_bytes();staged=(OUT/'stage/DATA'/REL).read_bytes()
    a={p:b for p,_,b in leaves(source)[1]};b={p:v for p,_,v in leaves(staged)[1]}
    changed=[p for p in set(a)|set(b) if a.get(p)!=b.get(p)]
    assert changed and all('/MultiLevel/Mesh0/' in p for p in changed),changed
    report=json.loads((OUT/'report.json').read_text());report['only_mesh0_changed']=True
    report['changed_nodes']=changed;(OUT/'report.json').write_text(json.dumps(report,indent=2))
    print('Verified: only Mesh0 changed. All other LODs, skeleton and textures are byte-identical.')
if __name__=='__main__':main()
