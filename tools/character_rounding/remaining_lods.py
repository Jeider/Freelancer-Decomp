"""Opt remaining unchanged bodies into the existing native LOD quality pair."""
import gzip
import json
import struct
from pathlib import Path
from contours import ROOT,GAME,read_tree,write_tree,child,digest
from extra_lods import node_bytes,count,lods,reconstruct as base_reconstruct
from build import Node
import gloves

OUT=ROOT/'out/character_rounding/lods/remaining'
BODIES=['benchmarkfemalebody','benchmarkmalebody','pl_male3_peasant_body_hurt',
        'robot_body_a','robot_body_b','robot_body_c','robot_body_d','robot_body_e','worm']


def reconstruct(raw,patch):
    return gloves.rebuild(raw,patch) if patch.with_suffix('.json').exists() else base_reconstruct(raw,patch)


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'patches').mkdir(exist_ok=True);records=[]
    for name in BODIES:
        rel=f'CHARACTERS/BODIES/{name}.dfm';raw=(GAME/'DATA'/rel).read_bytes();header,roots=read_tree(raw);root=roots[0]
        ml=child(root,'MultiLevel');assert not any(n.name in ('Enhanced geometry','Geometry quality') for n in ml.children)
        assert 2<=len(lods(root))<=8
        ml.children.append(Node('Geometry quality',struct.pack('<I',1)))
        patch=OUT/'patches'/(name+'.utf.gz');patch.write_bytes(gzip.compress(node_bytes(header,ml),mtime=0))
        built=reconstruct(raw,patch);verify=read_tree(built)[1][0]
        child(verify,'MultiLevel').children=[n for n in child(verify,'MultiLevel').children if n.name!='Geometry quality']
        assert write_tree(header,[verify])==write_tree(header,read_tree(raw)[1]),name
        records.append(dict(name=name,relative_path=rel,before_sha256=digest(raw),after_sha256=digest(built),patch=str(patch),patch_sha256=digest(patch.read_bytes()),triangles=[count(m) for m in lods(root)]))
    records+=json.loads((gloves.OUT/'models.json').read_text())['files']
    modified={r['relative_path'].lower() for r in records}
    protected={p.relative_to(GAME/'DATA').as_posix():digest(p.read_bytes()) for p in (GAME/'DATA/CHARACTERS').rglob('*.dfm') if p.relative_to(GAME/'DATA').as_posix().lower() not in modified}
    (OUT/'models.json').write_text(json.dumps(dict(files=records,protected=protected),indent=2))
    print('Prepared',len(BODIES),'native pairs and',len(gloves.NAMES),'gloves;',len(protected),'DFMs protected')


def evidence():
    rows=json.loads((gloves.OUT/'models.json').read_text())['files']
    validation=json.loads((gloves.OUT/'validation.json').read_text())
    assert validation['valid']==len(gloves.NAMES)
    for r in validation['results']:assert digest((gloves.OUT/r['name']/'edited.json.gz').read_bytes())==r['edited_sha256']
    blends=json.loads((gloves.OUT/'blend_validation.json').read_text())['valid']
    assert {r['name'] for r in blends}==set(gloves.NAMES)
    for r in blends:assert digest((gloves.OUT/r['name']/'hand.blend').read_bytes())==r['blend_sha256']
    for r in rows:
        folder=gloves.OUT/r['name'];report=json.loads((folder/'validation.json').read_text())
        assert report['blender_native_skin_agrees'] and report['edited_sha256']==digest((folder/'edited.json.gz').read_bytes())
        assert digest(Path(r['patch']).with_suffix('.json').read_bytes())==r['recipe_sha256']
        assert digest(Path(r['material']).read_bytes())==r['material_sha256']
    result=ROOT/'out/character_rounding/lods/check_loader/result.txt'
    assert 'PASS production loader' in result.read_text()
    return dict(gloves=len(rows),blends=len(blends),native_pairs=len(BODIES),game_launched=False)


if __name__=='__main__':prepare()
