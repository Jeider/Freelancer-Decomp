"""Read-only rh_pir atlas / native UV evidence for Q13 remapping."""
import collections
import json
import numpy as np
from PIL import Image,ImageDraw
import rh_freighter_q13 as q

f=q.f
OUT=q.OUT.parents[1]/'references/uv_native'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mats=f.audit.material_table([q.MAT,q.SOURCE.parents[3]/'fx/envmapbasic.mat'])
    _,nodes=f.mesh.read_tree(q.SOURCE.read_bytes())
    names=f.component_map(nodes);geom=f.local_geometry(nodes);trans,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    report={};pictures={}
    for m in mats.values():
        if m['image'] is not None and ('pir_r_' in m['name'].lower() or 'r_panel03' in m['texture'].lower()):
            texture=m['texture'].rsplit('.',1)[0]
            if texture not in pictures:
                im=m['image'].convert('RGB');im.save(OUT/(texture+'.png'));pictures[texture]=im
    native=[]
    for file,gs in geom.items():
        world=f.base.world(gs,*trans[file.lower()]);part=[]
        for g in world:
            a=np.array(g['corners']);uv=a[:,:,6:8];xyz=a[:,:,:3]
            area=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
            du=uv[:,1]-uv[:,0];dv=uv[:,2]-uv[:,0]
            au=np.abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])/2
            keep=(area>1e-6)&(au>1e-9);density=np.sqrt(au[keep]/area[keep])
            m=mats[g['material']];texture=m['texture'].rsplit('.',1)[0]
            part.append(dict(material=m['name'],texture=m['texture'],triangles=len(a),area=float(area.sum()),
                uv_min=uv.min((0,1)).tolist(),uv_max=uv.max((0,1)).tolist(),
                uv_per_unit_percentiles=np.percentile(density,[10,50,90]).tolist() if len(density) else []))
            native.append(dict(part=names[file],material=m['name'],corners=a.tolist()))
            if names[file]=='Baydoor_lod1' and m['image'] is not None:
                im=m['image'].convert('RGB').resize((900,900));draw=ImageDraw.Draw(im)
                for tri in uv:
                    p=[tuple(v*900) for v in tri];draw.line(p+[p[0]],fill=(20,240,240),width=2)
                im.save(OUT/('baydoor_uv_'+m['name']+'.png'))
        report[names[file]]=part
    (OUT/'native_usage.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (OUT/'native_geometry.json').write_text(json.dumps(native),encoding='utf8')
    (OUT/'materials.json').write_text(json.dumps({m['name']:{k:v for k,v in m.items() if k!='image'} for m in mats.values() if 'pir_r_' in m['name'].lower()},indent=2,default=lambda v:v.tolist()),encoding='utf8')
    cols=3;sz=480;sheet=Image.new('RGB',(cols*sz,((len(pictures)+cols-1)//cols)*(sz+28)),(32,36,40));draw=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(sorted(pictures.items())):
        x=(i%cols)*sz;y=(i//cols)*(sz+28);im.thumbnail((sz,sz));sheet.paste(im,(x,y+28));draw.text((x+8,y+6),name,fill='white')
    sheet.save(OUT/'rh_pir_atlases.jpg',quality=94)
    print('Atlases:',list(pictures));print('Baydoor:',json.dumps(report['Baydoor_lod1']));print(OUT)

if __name__=='__main__':main()
