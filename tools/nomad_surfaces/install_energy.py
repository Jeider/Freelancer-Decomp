"""Restore original Nomad artwork and install the additive runtime energy effect.
No arguments prepares a verified stage; --apply installs with backup and warms shaders.
"""
import json
import sys
import struct
from pathlib import Path
import install
sys.path.insert(0,str(install.REPO/'tools'))
import generate_station_lods as utf

BACKUP=Path('D:/games/FL_MOD/BACKUP/codex_nomad_surfaces_20261030_004735_658987')
install.STAGE=install.REPO/'src/obj/nomad_energy/install'
CODE=('bin/RP9.dll','bin/RP9.pdb','bin/Shading.dll','bin/Shading.pdb','DATA_EXTRA/SHADERS/nomad_energy.hlsl')
ART=tuple('DATA/SOLAR/'+n for n in ('beta_nomad_lair.mat','beta_nomad.mat','nomad_lair.mat','nomad.mat'))
install.PAYLOAD=CODE+ART
install.SCOPE='Original Nomad artwork; stationary membranes with Oc 0.28 and fibre sheen; energy organic coat follows MaterialAnim'

def leaves(nodes,prefix=''):
    for node in nodes:
        path=prefix+'/'+node.name
        if node.blob is not None:yield path,node.blob
        yield from leaves(node.children,path)

def web_materials(raw):
    header,nodes=utf.read_tree(raw)
    before=dict(leaves(nodes));allowed=set()
    def visit(group,prefix=''):
        for node in group:
            path=prefix+'/'+node.name
            if '/material library/' in path.lower() and node.name in ('lair_rock_mbrn_2side','lair_rckint_mem_2side'):
                opacity=next((c for c in node.children if c.name=='Oc'),None)
                if opacity is None:
                    opacity=utf.Node('Oc',struct.pack('<f',.28));node.children.append(opacity)
                else:opacity.blob=struct.pack('<f',.28)
                allowed.add(path+'/Oc')
            visit(node.children,path)
    visit(nodes)
    assert allowed,'Missing membrane material'
    result=utf.write_tree(header,nodes)
    _,verified=utf.read_tree(result);after=dict(leaves(verified))
    assert {p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)}==allowed
    return result

def prepare():
    game=Path('D:/games/FL_MOD').resolve(strict=True)
    original=json.loads((BACKUP/'manifest.json').read_text())
    assert Path(original['game']).resolve()==game
    originals={i['relative']:i for i in original['files']}
    assert set(originals)==set(ART)
    files=[]
    previous_path=install.STAGE/'manifest.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else {'files':[]}
    previous_hashes={i['relative']:i['prepared'] for i in previous['files']}
    for rel in install.PAYLOAD:
        source=install.safe(BACKUP if rel in ART else install.REPO,rel)
        target=install.safe(game,rel)
        before,after=install.digest(target),install.digest(source)
        if rel in ART:
            assert after==originals[rel]['original'],f'Backup changed: {rel}'
            assert before in (originals[rel]['prepared'],after,previous_hashes.get(rel)),f'Game asset edited since preparation: {rel}'
        staged=install.safe(install.STAGE,rel)
        if rel in ART:
            staged.parent.mkdir(parents=True,exist_ok=True)
            staged.write_bytes(web_materials(source.read_bytes()))
            after=install.digest(staged)
        else:install.copy(source,staged)
        if before!=after:files.append(dict(relative=rel,original=before,prepared=after))
    (install.STAGE/'manifest.json').write_text(json.dumps(dict(game=str(game),files=files,scope=install.SCOPE),indent=2))
    print(f'Prepared {len(files)} files; original texture bytes unchanged in all four banks; only membrane Oc set to 0.28. Game untouched.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:install.main()
