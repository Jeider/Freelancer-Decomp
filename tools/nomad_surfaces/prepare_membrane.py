"""Pack three generated textures into existing UTF banks; verify every unrelated leaf."""
from pathlib import Path
import hashlib
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_station_lods as utf

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
STAGE=ROOT/'src/obj/nomad_membrane/install'
LIBRARIES=('beta_nomad_lair.mat','beta_nomad.mat','nomad_lair.mat','nomad.mat')
TEXTURES={'lair_rock_membrane.tga':'outer-v3',
          'lair_rckint_membrane.tgalair_op.tga':'inner-v2',
          'lair_energy2.tga':'energy-v1'}
SCOPE='Generated blue and gold Nomad membranes and red energy; native opacity and mirrored repetition; no shader changes'

def walk(nodes,prefix=''):
    for n in nodes:
        path=prefix+'/'+n.name
        yield path,n
        yield from walk(n.children,path)

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
    files=[];report=[]
    for name in LIBRARIES:
        relative='DATA/SOLAR/'+name
        raw=(GAME/relative).read_bytes();header,nodes=utf.read_tree(raw)
        before={p:n.blob for p,n in walk(nodes) if n.blob is not None}
        allowed=set();changed_textures=[];changed_materials=[]
        for path,n in list(walk(nodes)):
            if '/texture library/' in path.lower() and n.name in TEXTURES:
                leaves=[c for c in n.children if c.name in ('MIPS','MIP0')]
                assert len(leaves)==1,(name,n.name)
                leaf=leaves[0];leaf.blob=(ROOT/f'src/obj/nomad_membrane/{TEXTURES[n.name]}.dds').read_bytes()
                allowed.add(path+'/'+leaf.name);changed_textures.append(n.name)
            if '/material library/' in path.lower() and n.children:
                dt=next((c for c in n.children if c.name=='Dt_name'),None)
                if dt is None or dt.blob.rstrip(b'\0').decode('ascii') not in TEXTURES:continue
                flags=next(c for c in n.children if c.name=='Dt_flags')
                old=struct.unpack('<I',flags.blob)[0];flags.blob=struct.pack('<I',(old&~15)|5)
                allowed.add(path+'/Dt_flags');changed_materials.append(n.name)
                if dt.blob.rstrip(b'\0')==b'lair_rock_membrane.tga':
                    oc=next((c for c in n.children if c.name=='Oc'),None)
                    if oc is None:oc=utf.Node('Oc',struct.pack('<f',.6));n.children.append(oc)
                    else:oc.blob=struct.pack('<f',.6)
                    allowed.add(path+'/Oc')
        assert changed_textures and changed_materials,name
        prepared=utf.write_tree(header,nodes);_,verified=utf.read_tree(prepared)
        after={p:n.blob for p,n in walk(verified) if n.blob is not None}
        changed={p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}
        assert changed==allowed,(name,changed^allowed)
        assert all(after[p]==b for p,b in before.items() if p not in allowed)
        dest=STAGE/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(prepared)
        files.append(dict(relative=relative,original=digest(raw),prepared=digest(prepared)))
        report.append(dict(library=name,textures=changed_textures,materials=changed_materials,changed_leaves=sorted(changed),unchanged_leaves=len(before)-len(allowed&before.keys())))
    (STAGE/'manifest.json').write_text(json.dumps(dict(game=str(GAME),files=files,scope=SCOPE),indent=2))
    (STAGE/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print('PASS four UTF libraries rebuilt; every unrelated leaf byte-identical; game untouched.')

if __name__=='__main__':main()
