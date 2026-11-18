"""Pin the actual li_for_01_base bar and inspect counter material placements."""
import io,json,shutil,subprocess
from pathlib import Path
import numpy as np
from native_common import ROOT,GAME,child,crc,dump,get_parts,leaves,read_tree,sha,text
from rheinland_audit import transforms

OUT=ROOT/'out/base_interiors/li_for_01_base/bar/counter_rework'
RELATIVE='BASES/LIBERTY/li_columbia_bar.cmp'
SOURCE=GAME/'DATA'/RELATIVE
RETAIL=Path('D:/Games/FL_ND/FL_ND/DATA')/RELATIVE


def audit():
    from PIL import Image,ImageDraw
    assert shutil.disk_usage(ROOT).free>2*1024**3
    (OUT/'textures').mkdir(parents=True,exist_ok=True);(OUT/'modeled').mkdir(exist_ok=True)
    routes={}
    for name in ('Li_03_Bar_hardpoint_01','Li_03_Bar_ambi_int_01'):
        source=GAME/'DATA/SCRIPTS/BASES'/(name+'.thn')
        run=subprocess.run([str(ROOT/'out/base_interiors/tool_cache/scene_read.exe'),str(source)],capture_output=True)
        assert run.returncode==0,run.stderr
        scene=json.loads(run.stdout);dump(OUT/(name+'.json'),scene)
        routes[name]=dict(path=str(source),sha256=sha(source.read_bytes()),entities=len(scene['entities']))
    raw=SOURCE.read_bytes();root=read_tree(raw)[1][0]
    textures={n.name.lower():n for n in child(root,'Texture library').children}
    materials={};tiles=[]
    for m in child(root,'Material library').children:
        props={n.name:text(n.blob) for n in m.children if n.name=='Type' or n.name.endswith('_name')}
        info=dict(name=m.name,number=m.name,type=props.get('Type',''),textures={})
        for key,name in props.items():
            if not key.endswith('_name') or name.lower() not in textures:continue
            data=next((n.blob for n in textures[name.lower()].children if n.name in ('MIPS','MIP0')),None)
            if not data:continue
            im=Image.open(io.BytesIO(data));dest='textures/'+sha(name.encode())[:12]+'.png';im.save(OUT/dest)
            info['textures'][key]=dict(name=name,path=dest,sha256=sha(data),size=list(im.size))
            if key=='Dt_name':
                pix=np.asarray(im.convert('RGB').resize((768,768)),dtype=float)/255
                review=Image.fromarray(np.uint8(np.clip(pix**.65*255,0,255)))
                review.save(OUT/f'textures/review_{crc(m.name)}.jpg',quality=94);tiles.append((m.name,review))
        materials[str(crc(m.name))]=info
    trans,kinds=transforms(root);arrays={};groups=[];parts=get_parts(root)
    for part in parts:
        r,p=trans[part['name']]
        for i,g in enumerate(part['groups']):
            t=g['corners'].copy();t[:,:,:3]=t[:,:,:3]@r+p;t[:,:,3:6]=t[:,:,3:6]@r
            key=f'{part["name"]}_{i:02d}';arrays[key]=t
            groups.append(dict(key=key,part=part['name'],group=i,material=str(g['material']),triangles=len(t),
                joint=kinds.get(part['name'],'Root'),shape=list(t.shape),bounds=[t[:,:,:3].min((0,1)).tolist(),t[:,:,:3].max((0,1)).tolist()],
                invalid_values=int(np.count_nonzero(~np.isfinite(t)))))
    np.savez_compressed(OUT/'original_geometry.npz',**arrays)
    dump(OUT/'surfaces.json',dict(groups=groups,materials=materials))
    retail=read_tree(RETAIL.read_bytes())[1][0]
    dump(OUT/'sources.json',dict(installed=str(SOURCE),installed_sha256=sha(raw),original=str(RETAIL),
        original_sha256=sha(RETAIL.read_bytes()),relative=RELATIVE,source_triangles=sum(len(v) for v in arrays.values()),
        native_geometry_matches_retail=dict(leaves(child(root,'VMeshLibrary')))==dict(leaves(child(retail,'VMeshLibrary'))),
        actual_room_ini='UNIVERSE/SYSTEMS_MOD/LI_FORBES/ROOM/li_for_01_bar.ini',scripts=routes,
        scope='Counter front/side fascia first; rear bartender counter second. Current installed geometry and artwork are the baseline.'))
    sheet=Image.new('RGB',(1200,((len(tiles)+3)//4)*320),(20,27,34));draw=ImageDraw.Draw(sheet)
    for i,(name,im) in enumerate(tiles):
        x=i%4*300;y=i//4*320;sheet.paste(im.resize((296,296)),(x,y));draw.text((x+4,y+299),name[:42],fill='white')
    sheet.save(OUT/'material_sheet.jpg',quality=94)
    print('SOURCE',SOURCE,'triangles',sum(len(v) for v in arrays.values()),'materials',len(materials),'D free GiB',round(shutil.disk_usage(ROOT).free/1024**3,2))
    for part in parts:
        gs=[g for g in groups if g['part']==part['name']]
        print(part['name'],sum(g['triangles'] for g in gs),'triangles',[(g['group'],materials[g['material']]['name']) for g in gs])


if __name__=='__main__':audit()
