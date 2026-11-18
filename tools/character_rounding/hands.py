"""Ordinary hand authoring inputs. Native assets are read only; no game writes."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import numpy as np
from PIL import Image

from contours import ROOT, GAME, read_tree, child, blob, arr, triangles, save_json

OUT = ROOT/'out/character_rounding/hands'
NAMES = [f'benchmark{sex}hand{side}' for sex in ('male','female') for side in ('left','right')]
NAMES += [f'{sex}hand{side}_black' for sex in ('male','female') for side in ('left','right')]


def skeleton(root):
    cmp = child(root,'Cmpnd')
    names = {blob(n,'File name').rstrip(b'\0').decode():blob(n,'Object name').rstrip(b'\0').decode()
             for n in cmp.children if any(x.name=='File name' for x in n.children)}
    parents={}
    sphere=blob(child(cmp,'Cons'),'Sphere')
    assert len(sphere)%212==0
    for at in range(0,len(sphere),212):
        parent=sphere[at:at+64].split(b'\0')[0].decode()
        name=sphere[at+64:at+128].split(b'\0')[0].decode()
        parents[name]=parent
    bones=[]
    # Deformable2 indexes the ordered *.3db children, NOT Cmpnd entries:
    # the wrist has a skin index although it is absent from Cmpnd.
    for n in root.children:
        if not n.name.lower().endswith('.3db'):continue
        name=names.get(n.name,re.sub(r'\d{12}\.3db$','',n.name))
        bind=arr(n,'Bone to root','<f4').ravel().tolist()
        bones.append(dict(name=name,parent=parents.get(name),native_bind=bind))
    return bones


def export(root):
    mesh=child(child(root,'MultiLevel'),'Mesh0');g=child(mesh,'Geometry')
    data={k:arr(g,n,t,w).tolist() for k,n,t,w in [('points','Points','<f4',3),('normals','Vertex_normals','<f4',3),('uv','UV0','<f4',2)]}
    data['point_indices']=arr(g,'Point_indices','<u4').ravel().tolist()
    data['uv_indices']=arr(g,'UV0_indices','<u4').ravel().tolist()
    first=arr(g,'Point_bone_first','<u4').ravel();counts=arr(g,'Point_bone_count','<u4').ravel()
    ids=arr(g,'Bone_id_chain','<u4').ravel();weights=arr(g,'Bone_weight_chain','<f4').ravel()
    data['skin']=[{str(int(b)):float(w) for b,w in zip(ids[f:f+n],weights[f:f+n])} for f,n in zip(first,counts)]
    data['bones']=skeleton(root);data['groups']=[]
    for group in child(mesh,'Face_groups').children:
        if not group.children:continue
        name=blob(group,'Material_name').rstrip(b'\0').decode()
        mat=next(n for n in child(root,'Material library').children if n.name.lower()==name.lower())
        tn=blob(mat,'Dt_name').rstrip(b'\0').decode()
        tex=next(n for n in child(root,'Texture library').children if n.name.lower()==tn.lower())
        payload=next(n.blob for n in tex.children if n.name in ('MIP0','MIPS'))
        path=OUT/'textures'/(hashlib.sha256(payload).hexdigest()[:16]+'.png')
        if not path.exists():Image.open(io.BytesIO(payload)).save(path)
        data['groups'].append(dict(name=name,texture=str(path),faces=triangles(group)))
    return data


def prepare():
    (OUT/'textures').mkdir(parents=True,exist_ok=True)
    inventory=[]
    for name in NAMES:
        folder=OUT/name;folder.mkdir(exist_ok=True)
        path=GAME/'DATA/CHARACTERS/HANDS'/(name+'.dfm');raw=path.read_bytes()
        root=read_tree(raw)[1][0]
        assert not any(n.name=='Enhanced geometry' for n in child(root,'MultiLevel').children),'Use saved original after installation'
        data=export(root);data['source']=str(path);data['sha256']=hashlib.sha256(raw).hexdigest()
        save_json(folder/'source.json.gz',data)
        inventory.append(dict(name=name,source_sha256=data['sha256'],triangles=sum(len(g['faces']) for g in data['groups']),bones=len(data['bones'])))
    (OUT/'inventory.json').write_text(json.dumps(inventory,indent=2))
    print(json.dumps(inventory,indent=2))


if __name__=='__main__':
    prepare()
