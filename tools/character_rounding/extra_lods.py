"""Build compact additive DFM LOD patches; preserve native geometry exactly."""
import copy
import gzip
import json
import struct
from pathlib import Path
import numpy as np
from contours import ROOT,GAME,read_tree,write_tree,child,blob,arr,put,triangles,original,write_mesh,digest
from policy import excluded_name
from hands import NAMES,OUT as HANDS
from build import Node

OUT=ROOT/'out/character_rounding/lods'


def lods(root):return [n for n in child(root,'MultiLevel').children if n.name.startswith('Mesh')]
def count(mesh):return sum(len(triangles(g)) for g in child(mesh,'Face_groups').children if g.children)
def node_bytes(header,node):return write_tree(header,[node])


def edited_hand(mesh,data):
    groups=[n for n in child(mesh,'Face_groups').children if n.children]
    records=[]
    for p,u in zip(data['point_indices'],data['uv_indices']):
        records.append(dict(p=data['points'][p],n=data['normals'][p],uv=data['uv'][u],uv1=data['uv'][u],skin={int(b):w for b,w in data['skin'][p].items()}))
    write_mesh(mesh,records,groups,[g['faces'] for g in data['groups']])


def reconstruct(raw,patch):
    header,roots=read_tree(raw);root=roots[0]
    replacement=read_tree(gzip.decompress(patch.read_bytes()))[1][0]
    was_enhanced=any(n.name=='Enhanced geometry' for n in child(root,'MultiLevel').children)
    is_enhanced=any(n.name=='Enhanced geometry' for n in replacement.children)
    assert not was_enhanced or is_enhanced,'Removing an extra LOD requires a dedicated rollback'
    root.children=[replacement if n.name=='MultiLevel' else n for n in root.children]
    for n in root.children:
        if is_enhanced and not was_enhanced and n.name.lower().endswith('.3db'):
            for leaf in n.children:
                if leaf.name=='Lod Bits':
                    leaf.blob=bytes(((v<<1)|(v&1))&255 for v in leaf.blob)
    return write_tree(header,roots)


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'patches').mkdir(exist_ok=True)
    candidates=[('BODIES',p.name) for p in sorted((ROOT/'out/character_rounding/contours_2k').iterdir()) if (p/'report.json').exists() and not excluded_name(p.name)]
    candidates += [('HANDS',n) for n in NAMES]
    records=[];unchanged=[]
    for category,name in candidates:
        rel=f'CHARACTERS/{category}/{name}.dfm';raw=(GAME/'DATA'/rel).read_bytes();header,roots=read_tree(raw);root=roots[0]
        ml=child(root,'MultiLevel');levels=lods(root)
        assert not any(n.name=='Enhanced geometry' for n in ml.children),'Already converted: '+name
        assert 1<=len(levels)<8,(name,len(levels))
        source=copy.deepcopy(levels[0])
        if category=='BODIES':
            _,native=original(name);native_root=read_tree(native)[1][0];source=copy.deepcopy(lods(native_root)[0])
            # Skip unchanged technical/robot models: there is no upgrade to gate.
            if node_bytes(header,source)==node_bytes(header,levels[0]):unchanged.append(rel);continue
        else:
            data=json.loads(gzip.decompress((HANDS/name/'edited.json.gz').read_bytes()))
            assert data['sha256']==digest(raw)
            edited_hand(levels[0],data)
        current_count=count(levels[0]);original_count=count(source)
        original_lods=[copy.deepcopy(n) for n in lods(read_tree(raw)[1][0])]
        for i,n in reversed(list(enumerate(levels[1:],1))):n.name=f'Mesh{i+1}'
        source.name='Mesh1'
        ml.children.insert(ml.children.index(levels[0])+1,source)
        put(ml,'Fractions',np.r_[np.float32(1),arr(ml,'Fractions','<f4').ravel()].astype('<f4').tobytes())
        ml.children.append(Node('Enhanced geometry',struct.pack('<I',1)))
        patch=OUT/'patches'/(name+'.utf.gz');patch.write_bytes(gzip.compress(node_bytes(header,ml),mtime=0))
        output=reconstruct(raw,patch);check=read_tree(output)[1][0];new=lods(check)
        assert [n.name for n in new]==[f'Mesh{i}' for i in range(len(new))]
        for i,old in enumerate(original_lods[1:],2):
            test=copy.deepcopy(new[i]);test.name=old.name
            assert node_bytes(header,test)==node_bytes(header,old),(name,i)
        test=copy.deepcopy(new[1]);test.name='Mesh0'
        expected=copy.deepcopy(source);expected.name='Mesh0'
        assert node_bytes(header,test)==node_bytes(header,expected)
        # No material/texture/attachment changes. Only bone LOD masks shift.
        before={n.name:n for n in roots[0].children}
        for n in check.children:
            if n.name=='MultiLevel' or n.name.lower().endswith('.3db'):continue
            assert node_bytes(header,n)==node_bytes(header,before[n.name]),name
        record=dict(name=name,relative_path=rel,before_sha256=digest(raw),after_sha256=digest(output),
            patch=str(patch),patch_sha256=digest(patch.read_bytes()),triangles=[count(n) for n in new],
            enhanced_triangles=current_count,original_triangles=original_count)
        records.append(record)
    protected={str(p.relative_to(GAME/'DATA')).replace('\\','/'):digest(p.read_bytes()) for category in ('BODIES','HANDS','HEADS') for p in (GAME/'DATA/CHARACTERS'/category).glob('*.dfm') if str(p.relative_to(GAME/'DATA')).replace('\\','/') not in {r['relative_path'] for r in records}}
    (OUT/'models.json').write_text(json.dumps(dict(files=records,protected=protected,unchanged=unchanged),indent=2))
    print('Prepared additive LODs:',len(records),'unchanged:',len(unchanged),'protected:',len(protected))
    for r in records:
        if '/HANDS/' in r['relative_path'] or r['name'] in ('li_hatcher_body','pl_trent_body','pl_male2_journeyman_body'):print(r['name'],r['triangles'])


if __name__=='__main__':prepare()
