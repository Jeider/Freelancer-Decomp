"""Stage/install high-contrast cobweb and root membranes; energy leaves untouched."""
import json
import struct
import sys
from pathlib import Path
import install
sys.path.insert(0,str(install.REPO/'tools'))
import generate_station_lods as utf

install.STAGE=install.REPO/'src/obj/nomad_web/install'
install.PAYLOAD=tuple('DATA/SOLAR/'+n for n in ('beta_nomad_lair.mat','beta_nomad.mat','nomad_lair.mat','nomad.mat'))
install.SCOPE='High-contrast stationary cobweb/root membranes with open alpha holes and Oc 0.8; energy and other surfaces unchanged'
TEXTURES={'lair_rock_membrane.tga':'web-outer-v1','lair_rckint_membrane.tgalair_op.tga':'web-inner-v1'}
MATERIALS={'lair_rock_mbrn_2side','lair_rckint_mem_2side'}

def walk(nodes,prefix=''):
    for node in nodes:
        path=prefix+'/'+node.name
        yield path,node
        yield from walk(node.children,path)

def prepare():
    game=Path('D:/games/FL_MOD').resolve(strict=True)
    items=[];report=[]
    for rel in install.PAYLOAD:
        target=install.safe(game,rel);raw=target.read_bytes()
        header,nodes=utf.read_tree(raw)
        before={p:n.blob for p,n in walk(nodes) if n.blob is not None}
        allowed=set();textures=0;materials=0
        for path,node in list(walk(nodes)):
            if '/texture library/' in path.lower() and node.name in TEXTURES:
                payload=[c for c in node.children if c.name in ('MIPS','MIP0')]
                assert len(payload)==1,(rel,path)
                payload[0].blob=(install.REPO/f'src/obj/nomad_membrane/{TEXTURES[node.name]}.dds').read_bytes()
                assert payload[0].blob[:4]==b'DDS '
                allowed.add(path+'/'+payload[0].name);textures+=1
            if '/material library/' in path.lower() and node.name in MATERIALS:
                fields={c.name:c for c in node.children}
                assert fields['Dt_name'].blob.rstrip(b'\0').decode() in TEXTURES
                assert struct.unpack('<I',fields['Dt_flags'].blob)[0]&15==0,'Expected normal WRAP addressing'
                assert 'Oc' in fields,'Expected previous membrane opacity adjustment'
                fields['Oc'].blob=struct.pack('<f',.8)
                allowed.add(path+'/Oc');materials+=1
        assert textures==materials==1,(rel,textures,materials)
        result=utf.write_tree(header,nodes)
        _,verified=utf.read_tree(result)
        after={p:n.blob for p,n in walk(verified) if n.blob is not None}
        changed={p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}
        assert changed<=allowed,(rel,changed-allowed)
        staged=install.safe(install.STAGE,rel);staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(result)
        old,new=install.digest(target),install.digest(staged)
        if old!=new:items.append(dict(relative=rel,original=old,prepared=new))
        report.append(dict(file=rel,changed=sorted(changed),unchanged_leaves=len(before)-len(changed)))
    (install.STAGE/'manifest.json').write_text(json.dumps(dict(game=str(game),files=items,scope=install.SCOPE),indent=2))
    (install.STAGE/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print(f'Prepared {len(items)} MAT banks; energy, animation, addressing and all unrelated leaves byte-identical. Game untouched.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:install.main()
