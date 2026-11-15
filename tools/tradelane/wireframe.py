"""Feature-edge wireframe: omit coplanar triangulation and texture seams."""
import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import struct as S
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import generate_station_lods as utf
from generate_industrial_lods import geometry


def mesh_edges(blob):
    _,primitive,groups,count,fvf,nv=S.unpack_from('<II4H',blob)
    assert primitive==4 and fvf==0x112
    offset=16+12*groups;voff=offset+2*count
    points=np.frombuffer(blob,dtype='<f4',offset=voff,count=nv*8).reshape(-1,8)[:,:3]
    # UV/material/normal seams often duplicate vertices on the same surface.
    keys=[tuple(p.round(3)) for p in points];representative={}
    for i,key in enumerate(keys):representative.setdefault(key,i)
    edges={}
    for g in range(groups):
        _,base,_,n,_=S.unpack_from('<I4H',blob,16+g*12)
        ids=np.frombuffer(blob,dtype='<u2',count=n,offset=offset).astype(int)+base;offset+=2*n
        for a,b,c in ids.reshape(-1,3):
            normal=np.cross(points[b]-points[a],points[c]-points[a]);length=np.linalg.norm(normal)
            if length<1e-8:continue
            normal=normal/length
            for x,y in ((a,b),(b,c),(c,a)):
                x=representative[keys[x]];y=representative[keys[y]]
                if x!=y:edges.setdefault(tuple(sorted((x,y))),[]).append(normal)
    return points,edges


def feature_wire(blob,mesh_crc,angle=25):
    points,edges=mesh_edges(blob);kept=[];threshold=math.cos(math.radians(angle))
    for edge,normals in edges.items():
        # An open boundary, or a genuine change in surface direction. Opposite
        # winding on a coplanar/back-to-back face is not a feature edge.
        if len(normals)==1 or any(abs(float(a@b))<threshold for i,a in enumerate(normals) for b in normals[i+1:]):
            kept.append(edge)
    flat=[i for edge in sorted(kept) for i in edge]
    assert flat and len(flat)<65536 and max(flat)<len(points)
    return S.pack('<II4H',16,mesh_crc,0,len(set(flat)),len(flat),len(points))+S.pack('<%dH'%len(flat),*flat)


def preview(blob,old,new,path):
    points,_=mesh_edges(blob)
    im=Image.new('RGB',(1100,650),'#111e2a');draw=ImageDraw.Draw(im)
    # Slightly oblique orthographic view exposes side walls and planar diagonals.
    xy=np.column_stack((points[:,0]+points[:,2]*.65,points[:,1]+points[:,2]*.3))
    lo=xy.min(0);hi=xy.max(0);scale=min(460/(hi[0]-lo[0]),540/(hi[1]-lo[1]));center=(lo+hi)/2
    for panel,(wire,title) in enumerate(((old,'BEFORE'),(new,'FEATURE EDGES'))):
        _,_,base,unique,n,maximum=S.unpack_from('<II4H',wire)
        ids=np.frombuffer(wire,dtype='<u2',offset=16,count=n).astype(int)+base
        draw.text((panel*550+20,20),f'{title}: {n//2} lines',fill='white')
        for a,b in ids.reshape(-1,2):
            p=(xy[[a,b]]-center)*scale
            draw.line([(panel*550+275+float(x),345-float(y)) for x,y in p],fill='#a2e9f4',width=1)
    im.save(path)


def main():
    from physical_model import DataFolder,GAME,MODEL,digest,leaves
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    out=ROOT/'out/tradelane_wireframe';out.mkdir(parents=True,exist_ok=True)
    live=DataFolder(root=GAME);stage=DataFolder(root=out/'stage')
    if not args.apply:
        source=live.data_path(MODEL).read_bytes();header,roots=utf.read_tree(source);root=roots[0]
        part=utf.child(root,'platform_lod1.3db');wire=utf.child(utf.child(part,'VMeshWire'),'VWireData')
        old=wire.blob;mesh_id=S.unpack_from('<I',old,4)[0]
        mesh=next(n for n in utf.child(root,'VMeshLibrary').children if utf.crc(n.name)==mesh_id)
        blob=geometry(utf.child(mesh,'VMeshData').blob)
        wire.blob=feature_wire(blob,mesh_id)
        packed=utf.write_tree(header,roots)
        before=dict(leaves(utf.read_tree(source)[1]));after=dict(leaves(utf.read_tree(packed)[1]))
        changed=[p for p,b in before.items() if after[p]!=b]
        assert set(before)==set(after) and changed==['/\\/platform_lod1.3db/VMeshWire/VWireData'],changed
        stage.sync_data_file(MODEL,packed)
        preview(blob,old,wire.blob,out/'comparison.png')
        manifest={'file':MODEL,'before':digest(source),'after':digest(packed),
                  'old_lines':S.unpack_from('<H',old,12)[0]//2,'new_lines':S.unpack_from('<H',wire.blob,12)[0]//2}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest));return
    m=json.loads((out/'manifest.json').read_text());assert m['file']==MODEL
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+n+b'"' in processes for n in (b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'flserver.exe')),'Close game/server before installation'
    old=live.data_path(MODEL).read_bytes();new=stage.data_path(MODEL).read_bytes()
    assert digest(old)==m['before'],'Live model changed; prepare again'
    assert digest(new)==m['after'],'Prepared model changed'
    backup=out/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S');saved=DataFolder(root=backup)
    saved.sync_data_file(MODEL,old);assert digest(saved.data_path(MODEL).read_bytes())==m['before']
    try:
        live.sync_data_file(MODEL,new);assert digest(live.data_path(MODEL).read_bytes())==m['after']
    except BaseException:
        live.sync_data_file(MODEL,old);raise
    print('Installed wireframe only. Backup:',backup)


if __name__=='__main__':main()
