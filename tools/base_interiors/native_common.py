"""Native room integration helpers. Every DATA write uses DataFolder."""
import hashlib
import importlib.util
import json
import struct as S
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
REL='BASES/RHEINLAND/rh_bizmark_bar.cmp'
BASE=ROOT/'out/base_interiors/rh_biz_01_base/bar'
PROTO=BASE/'prototype_v8'
OUT=BASE/'integration_v8'
STAGE=OUT/'stage'
sys.path.insert(0,str(ROOT/'tools'))
if 'bpy' in sys.modules:
    from blender_workspace import configure as configure_blender_workspace
    configure_blender_workspace('base_interiors')
from generate_station_lods import Node,read_tree,write_tree,child,crc
spec=importlib.util.spec_from_file_location('base_interior_data_folder',GAME/'Assets/Pythonlancer/tools/data_folder.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
DataFolder=module.DataFolder

def sha(b):return hashlib.sha256(b).hexdigest()
def text(b):return b.split(b'\0',1)[0].decode('ascii')
def node(name,children):
    n=Node(name);n.children=children;return n
def leaves(n,path=''):
    path+='/'+n.name
    if n.blob is not None:yield path,n.blob
    for c in n.children:yield from leaves(c,path)
def mesh_ref(n):
    try:return child(child(n,'VMeshPart'),'VMeshRef')
    except StopIteration:return child(child(child(child(n,'MultiLevel'),'Level0'),'VMeshPart'),'VMeshRef')

def decode(blob,sv=0,sg=0,ng_select=None):
    flags,primitive,ng,ni,fvf,nv=S.unpack_from('<II4H',blob)
    assert flags==1 and primitive==4 and fvf in (0x12,0x112,0x212,0x312,0x412)
    stride=6+2*(fvf>>8)
    off=16+12*ng
    assert len(blob)>=off+2*ni+4*nv*stride
    indices=np.frombuffer(blob,'<u2',ni,off).astype(int)
    vertices=np.frombuffer(blob,'<f4',nv*stride,off+2*ni).reshape(nv,stride)
    groups=[];start=0
    for g in range(ng):
        mat,lo,hi,count,unused=S.unpack_from('<I4H',blob,16+12*g)
        assert count%3==0 and hi<nv and lo<=hi
        ids=indices[start:start+count]+lo;start+=count
        assert ids.min()>=lo and ids.max()<=hi
        if g<sg or (ng_select is not None and g>=sg+ng_select):continue
        ids+=sv
        assert ids.max()<nv
        groups.append(dict(material=mat,unused=unused,corners=vertices[ids].reshape(-1,3,stride).copy()))
    assert start==ni
    return groups

def get_parts(root):
    lib={crc(n.name):child(n,'VMeshData').blob for n in child(root,'VMeshLibrary').children}
    parts=[]
    for p in child(root,'Cmpnd').children:
        if p.name=='Cons':continue
        name=text(child(p,'Object name').blob);filename=text(child(p,'File name').blob)
        ref=mesh_ref(child(root,filename));size,key,sv,nv,si,ni,sg,ng=S.unpack_from('<II6H',ref.blob)
        assert size==60
        blob=lib[key]
        assert sum(S.unpack_from('<H',blob,16+12*g+8)[0] for g in range(sg))==si
        groups=decode(blob,sv,sg,ng);assert len(groups)==ng and sum(len(g['corners'])*3 for g in groups)==ni
        parts.append(dict(name=name,filename=filename,record=p,ref=ref,groups=groups))
    return parts

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
