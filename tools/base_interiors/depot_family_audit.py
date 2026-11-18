"""Inventory each depot's actual installed geometry, artwork and UV placements."""
import argparse,io,json,re,shutil
from pathlib import Path
import numpy as np
from native_common import ROOT,GAME,read_tree,child,leaves,crc,text,sha,get_parts,dump
from rheinland_audit import transforms

FAMILY=ROOT/'out/base_interiors/depot_family'
REGIONS={'li':'LIBERTY','br':'BRETONIA','ku':'KUSARI'}


def paths(region):
    relative=f'BASES/{REGIONS[region]}/{region}_depot_deck.cmp'
    return FAMILY/(region+'_depot_deck'),GAME/'DATA'/relative,Path('D:/Games/FL_ND/FL_ND/DATA')/relative,relative


def audit(region):
    from PIL import Image,ImageDraw
    out,live,original,relative=paths(region)
    out.mkdir(parents=True,exist_ok=True);(out/'textures').mkdir(exist_ok=True);(out/'modeled').mkdir(exist_ok=True)
    raw=live.read_bytes();baseline=original.read_bytes()
    root=read_tree(raw)[1][0];orig=read_tree(baseline)[1][0]
    same=dict(leaves(child(root,'VMeshLibrary')))==dict(leaves(child(orig,'VMeshLibrary')))
    assert same,'Existing geometry differs from retail: review upgrades before processing '+region
    parts=get_parts(root);trans,kinds=transforms(root)
    needed={g['material'] for p in parts for g in p['groups']}
    textures={n.name.lower():n for n in child(root,'Texture library').children}
    mats={};tiles=[]
    for m in child(root,'Material library').children:
        if crc(m.name) not in needed:continue
        number=re.search(r'(?:room-|R_D_R )(\d+)',m.name,re.I)
        props={n.name:text(n.blob) for n in m.children if n.name=='Type' or n.name.endswith('_name')}
        info=dict(name=m.name,number=number.group(1) if number else m.name,type=props.get('Type',''),textures={})
        for key,name in props.items():
            if not key.endswith('_name') or name.lower() not in textures:continue
            node=textures[name.lower()];data=next((n.blob for n in node.children if n.name in ('MIPS','MIP0')),None)
            if not data:continue
            im=Image.open(io.BytesIO(data));dest='textures/'+sha(name.encode())[:12]+'.png'
            if not (out/dest).exists():im.save(out/dest)
            info['textures'][key]=dict(name=name,path=dest,sha256=sha(data),size=list(im.size))
            if key=='Dt_name' and number:
                pixels=np.asarray(im.convert('RGB').resize((768,768)),dtype=float)/255
                review=Image.fromarray(np.uint8(np.clip(pixels**.55*255,0,255)))
                review.save(out/f'textures/review_{number.group(1)}.jpg',quality=94)
                tiles.append((number.group(1),review))
        mats[str(crc(m.name))]=info
    arrays={};groups=[]
    for p in parts:
        rotation,position=trans[p['name']]
        for i,g in enumerate(p['groups']):
            key=f'{p["name"]}_{i:02d}';t=g['corners'].copy()
            t[:,:,:3]=t[:,:,:3]@rotation+position;t[:,:,3:6]=t[:,:,3:6]@rotation
            arrays[key]=t
            groups.append(dict(key=key,part=p['name'],group=i,material=str(g['material']),triangles=len(t),
                joint=kinds.get(p['name'],'Root'),shape=list(t.shape),
                bounds=[t[:,:,:3].reshape(-1,3).min(0).tolist(),t[:,:,:3].reshape(-1,3).max(0).tolist()],
                invalid_values=int(np.count_nonzero(~np.isfinite(t)))))
    np.savez_compressed(out/'original_geometry.npz',**arrays)
    dump(out/'surfaces.json',dict(groups=groups,materials=mats))
    dump(out/'sources.json',dict(region=region,relative=relative,installed=str(live),installed_sha256=sha(raw),
        original=str(original),original_sha256=sha(baseline),geometry_matches_fl_nd=True,
        source_triangles=sum(len(v) for v in arrays.values()),source='Installed regional CMP, all current materials/textures retained'))
    tiles.sort(key=lambda pair:pair[0]);sheet=Image.new('RGB',(1200,((len(tiles)+4)//5)*266),(20,27,34));draw=ImageDraw.Draw(sheet)
    for i,(number,im) in enumerate(tiles):
        x=i%5*240;y=i//5*266;im=im.resize((236,236));sheet.paste(im,(x,y));draw.text((x+6,y+240),region.upper()+' '+number,fill='white')
    sheet.save(out/'material_sheet.jpg',quality=94)
    assert live.read_bytes()==raw
    print(region,'triangles',sum(len(v) for v in arrays.values()),'materials',len(tiles),'nonfinite',sum(g['invalid_values'] for g in groups))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('regions',nargs='*',choices=list(REGIONS));args=ap.parse_args()
    assert shutil.disk_usage(ROOT).free>2*1024**3,'Insufficient D: space'
    for region in args.regions or REGIONS:audit(region)
