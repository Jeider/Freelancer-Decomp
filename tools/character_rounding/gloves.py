"""Transfer approved ordinary-hand geometry only after exact native-family matching.

Separate MAT authoring libraries remain embedded in the runtime DFM: bodypart
records do not support accessory-style material_library declarations.
"""
import copy
import argparse
import gzip
import json
from pathlib import Path
import struct
import uuid
import numpy as np
import hands
from contours import ROOT,GAME,read_tree,write_tree,child,blob,put,arr,digest,save_json
from extra_lods import count,lods,node_bytes,edited_hand,reconstruct
from build import Node

OUT=ROOT/'out/character_rounding/gloves'
NAMES=[f'{f}_{s}_glove_{h}' for f in ('br','li','rh','yel') for s in ('male','female') for h in ('left','right')]
KEYS=('points','normals','point_indices','uv','uv_indices','skin','bones')


def load(path):return json.loads(gzip.decompress(path.read_bytes()))


def content(node):return (node.name,node.blob,tuple(content(c) for c in sorted(node.children,key=lambda n:n.name)))


def fix_texture_label(root,name):
    if name!='li_female_glove_left':return
    tex=child(root,'Texture library').children[0]
    reference=read_tree((GAME/'DATA/CHARACTERS/HANDS/li_male_glove_left.dfm').read_bytes())[1][0]
    expected=child(reference,'Texture library').children[0]
    assert [(n.name,n.blob) for n in tex.children]==[(n.name,n.blob) for n in expected.children]
    tex.name=expected.name


def audit():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'textures').mkdir(exist_ok=True)
    bases={n:load(hands.OUT/n/'source.json.gz') for n in hands.NAMES[:4]}
    records=[]
    for name in NAMES:
        path=GAME/'DATA/CHARACTERS/HANDS'/(name+'.dfm');raw=path.read_bytes();header,roots=read_tree(raw);root=roots[0]
        fix_texture_label(root,name)
        original_out=hands.OUT;hands.OUT=OUT
        try:data=hands.export(root)
        finally:hands.OUT=original_out
        matches=[n for n,d in bases.items() if all(data[k]==d[k] for k in KEYS) and [g['faces'] for g in data['groups']]==[g['faces'] for g in d['groups']]]
        # Bone labels alone are not enough: coordinates, topology, UV and weights must match.
        records.append(dict(name=name,matches=matches,sha256=digest(raw),triangles=[count(m) for m in lods(root)],materials=[g['name'] for g in data['groups']],root_nodes=[n.name for n in root.children if not n.name.endswith('.3db')]))
    (OUT/'audit.json').write_text(json.dumps(records,indent=2))
    print('Exact source matches:',len([r for r in records if len(r['matches'])==1]),'of',len(records))


def rebuild(raw,patch):
    recipe=json.loads(patch.with_suffix('.json').read_text())
    assert digest(patch.read_bytes())==recipe['patch_sha256']
    mat=Path(recipe['material']);assert digest(mat.read_bytes())==recipe['material_sha256']
    header,roots=read_tree(reconstruct(raw,patch));root=roots[0]
    libraries=read_tree(mat.read_bytes())[1][0]
    for replacement in libraries.children:
        root.children=[copy.deepcopy(replacement) if n.name==replacement.name else n for n in root.children]
    mapping=recipe['private_resources']
    for n in root.children:
        if n.name in mapping:n.name=mapping[n.name]
    for part in child(root,'Cmpnd').children:
        for n in part.children:
            if n.name=='File name':
                old=n.blob.rstrip(b'\0').decode();n.blob=(mapping[old]+'\0').encode()
    return write_tree(header,roots)


def prepare():
    audit();(OUT/'materials').mkdir(exist_ok=True)
    records=[]
    for row in json.loads((OUT/'audit.json').read_text()):
        name=row['name'];assert len(row['matches'])==1,name;base=row['matches'][0]
        folder=OUT/name;folder.mkdir(exist_ok=True)
        rel=f'CHARACTERS/HANDS/{name}.dfm';raw=(GAME/'DATA'/rel).read_bytes()
        assert digest(raw)==row['sha256'];header,roots=read_tree(raw);root=roots[0]
        assert not any(n.name=='Enhanced geometry' for n in child(root,'MultiLevel').children)
        fix_texture_label(root,name)
        oldout=hands.OUT;hands.OUT=OUT
        try:source=hands.export(root)
        finally:hands.OUT=oldout
        source.update(source=str(GAME/'DATA'/rel),sha256=digest(raw),geometry_family=base)
        edited=load(hands.OUT/base/'edited.json.gz')
        assert source['bones']==edited['bones']
        edited.update(source=source['source'],sha256=source['sha256'],geometry_family=base)
        for g,s in zip(edited['groups'],source['groups']):g.update(name=s['name'],texture=s['texture'])
        edited['authoring']['glove_geometry_source']=base
        save_json(folder/'source.json.gz',source);save_json(folder/'edited.json.gz',edited)
        # Keep authenticated source for re-export; no textures duplicated per LOD.
        (folder/'original.dfm.gz').write_bytes(gzip.compress(raw,mtime=0))
        mat=OUT/'materials'/(name.split('_')[0]+'_gloves.mat')
        matroot=Node(root.name);matroot.children=[copy.deepcopy(child(root,n)) for n in ('Material library','Texture library')]
        payload=write_tree(header,[matroot])
        if mat.exists():
            matroot=read_tree(mat.read_bytes())[1][0]
            assert all(content(child(matroot,n))==content(child(root,n)) for n in ('Material library','Texture library')),'Shared family has different material data'
        else:mat.write_bytes(payload)
        ml=child(root,'MultiLevel');levels=lods(root);native=[copy.deepcopy(m) for m in levels]
        assert 1<=len(levels)<8
        new=copy.deepcopy(levels[0]);edited_hand(new,edited)
        for i,m in enumerate(levels):m.name=f'Mesh{i+1}'
        ml.children.insert(ml.children.index(levels[0]),new)
        put(ml,'Fractions',np.r_[np.float32(1),arr(ml,'Fractions','<f4').ravel()].astype('<f4').tobytes())
        ml.children.append(Node('Enhanced geometry',struct.pack('<I',1)))
        patch=folder/'lods.utf.gz';patch.write_bytes(gzip.compress(node_bytes(header,ml),mtime=0))
        salt=str(uuid.uuid4().int%10**12).zfill(12)
        import re
        mapping={n.name:re.sub(r'\d{12}\.3db$',salt+'.3db',n.name) for n in root.children if n.name.lower().endswith('.3db')}
        assert all(k!=v for k,v in mapping.items())
        recipe=dict(name=name,material=str(mat),material_sha256=digest(mat.read_bytes()),patch_sha256=digest(patch.read_bytes()),export_salt=salt,private_resources=mapping)
        patch.with_suffix('.json').write_text(json.dumps(recipe,indent=2))
        output=rebuild(raw,patch);check=read_tree(output)[1][0]
        for i,old in enumerate(native,1):
            test=copy.deepcopy(lods(check)[i]);test.name=old.name
            assert node_bytes(header,test)==node_bytes(header,old)
        assert hands.skeleton(check)==source['bones']
        for lib in ('Material library','Texture library'):assert node_bytes(header,child(check,lib))==node_bytes(header,child(matroot,lib))
        records.append(dict(name=name,relative_path=rel,before_sha256=digest(raw),after_sha256=digest(output),patch=str(patch),patch_sha256=digest(patch.read_bytes()),recipe_sha256=digest(patch.with_suffix('.json').read_bytes()),triangles=[count(m) for m in lods(check)],geometry_family=base,**{k:v for k,v in recipe.items() if k not in ('name','patch_sha256')}))
    (OUT/'models.json').write_text(json.dumps(dict(files=records),indent=2))
    print('Prepared',len(records),'gloves; 4 separate MAT sources, native LODs preserved')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');args=p.parse_args()
    prepare() if args.prepare else audit()
