"""Pack photographed orthographic views, dilate gutters, write external MAT."""
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import rh_b_projection_prepare as p
f,OUT=p.f,p.OUT
NAME='rh_b_projection_lod'


def main():
    projectors=json.loads((OUT/'projectors.json').read_text())
    raw=Image.new('RGBA',(4096,4096));padded=Image.new('RGB',(4096,4096),(100,95,85))
    for views in projectors.values():
        for view in views:
            im=Image.open(OUT/view['image']).convert('RGBA');arr=np.array(im)
            valid=arr[:,:,3]>127;assert valid.any(),view['image']
            nearest=distance_transform_edt(~valid,return_distances=False,return_indices=True)
            filled=arr[nearest[0],nearest[1],:3]
            xy=tuple(k*512 for k in view['tile']);raw.paste(im,xy);padded.paste(Image.fromarray(filled),xy)
    raw.resize((2048,2048),Image.Resampling.LANCZOS).save(OUT/'photographs_atlas.png')
    padded.resize((2048,2048),Image.Resampling.LANCZOS).save(OUT/(NAME+'.png'))
    root=Path(__file__).resolve().parents[2];cache=root/'out/ship_design/tool_cache/lod_materials'
    command=cache/'build.cmd';exe=cache/'lod_dds.exe'
    if not exe.exists():subprocess.run(['cmd','/c',str(command)],cwd=root,check=True)
    dds=OUT/(NAME+'.dds')
    result=subprocess.run([str(exe),str(OUT/(NAME+'.png')),str(dds)],cwd=root,capture_output=True,text=True)
    print(result.stdout,flush=True);print(result.stderr,flush=True);result.check_returncode()
    before=f.digest(f.SHARED_MAT);header,nodes=f.mesh.read_tree(f.SHARED_MAT.read_bytes())
    texture=NAME+'.tga';mat=f.folder(NAME,f.textnode('Type','DcDt'),f.mesh.Node('Dc',np.ones(3,'<f4').tobytes()),f.textnode('Dt_name',texture))
    tex=f.folder(texture,f.mesh.Node('MIPS',dds.read_bytes()))
    nodes[0].children=[f.folder('Material library',mat),f.folder('Texture library',tex)]
    dest=OUT/'rh_concept_b_lods.mat';dest.write_bytes(f.mesh.write_tree(header,nodes))
    assert f.digest(f.SHARED_MAT)==before
    p.dump('atlas.json',dict(material=NAME,material_crc=f.mesh.crc(NAME),size=2048,
        texture=texture,mat_sha256=f.digest(dest),dds_sha256=f.digest(dds),mips=12,format='DXT1',
        mat_bytes=dest.stat().st_size,shared_mat_unchanged=True,gpu_check=result.stdout.strip()))
    print('EXTERNAL ATLAS MAT',dest,flush=True)


if __name__=='__main__':main()
