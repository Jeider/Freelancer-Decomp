"""Read-only native RH pirate fighter UV evidence; authoring outputs only."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import rh_fighter_f14_form as model

OUT=model.TOPIC/'references/uv_native'


def main():
    f=model.f;OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((model.TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(model.SOURCE)==selection['source_sha256']
    mats=f.audit.material_table([model.MAT,model.ENV])
    _,nodes=f.mesh.read_tree(model.SOURCE.read_bytes())
    names=f.component_map(nodes);geo=f.local_geometry(nodes)
    trans,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    report={};native=[]
    for filename,groups in geo.items():
        world=f.base.world(groups,*trans[filename.lower()]);part=[]
        for g in world:
            a=np.array(g['corners']);p=a[:,:,:3];uv=a[:,:,6:8]
            mat=mats.get(g['material'],dict(name=hex(g['material']),texture='',image=None,kind='MISSING'))
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            x,y=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0];ua=abs(x[:,0]*y[:,1]-x[:,1]*y[:,0])/2
            good=(area>1e-7)&(ua>1e-9)
            part.append(dict(material=mat['name'],triangles=len(a),area=float(area.sum()),
                bounds=[p.min((0,1)),p.max((0,1))],
                uv_per_unit=np.percentile(np.sqrt(ua[good]/area[good]),[10,50,90]) if good.any() else []))
            native.append(dict(part=names[filename],material=mat['name'],material_crc=g['material'],corners=a))
            if mat['image'] is not None:
                image_path=OUT/(Path(mat['texture']).stem+'.png')
                if not image_path.exists():mat['image'].save(image_path)
                if names[filename].lower() in ('baydoor_lod1','port_wing3_lod1','starboard_wing3_lod1'):
                    im=mat['image'].convert('RGB').resize((768,768));dr=ImageDraw.Draw(im)
                    for tri in uv:
                        pts=[tuple(v*767) for v in tri];dr.line(pts+[pts[0]],fill=(0,255,220),width=2)
                    im.save(OUT/(names[filename]+'_'+mat['name']+'_uv.png'))
        report[names[filename]]=part
    model.dump(OUT/'native_geometry.json',native)
    model.dump(OUT/'native_usage.json',report)
    model.dump(OUT/'source.json',dict(source=str(model.SOURCE),source_sha256=f.digest(model.SOURCE),
        materials=str(model.MAT),materials_sha256=f.digest(model.MAT),pose='Sc_extend wing t=0'))
    print(json.dumps(report,indent=2,default=lambda a:a.tolist()))


if __name__=='__main__':main()
