"""Isolated Common relink: reuse existing objects and verify the installed baseline."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env, digest

OUT = ROOT/'src/obj/train_consist'
TLOG = ROOT/'src/obj/Common/Release/Common.tlog'


def run(tool, name, content, compiler, env):
    rsp = OUT/f'{name}.rsp'
    rsp.write_text(content, encoding='utf-8')
    log = OUT/f'{name}.log'
    with log.open('wb') as f:
        result = subprocess.run([str(compiler/tool), '@'+str(rsp)], cwd=ROOT/'src/Common',
                                env=env, stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(errors='replace')[-10000:])
    result.check_returncode()
    print('PASS:', name, flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler, env = compiler_env()
    lines = (TLOG/'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    commands = {Path(line[1:]).stem.lower(): lines[i+1] for i, line in enumerate(lines) if line.startswith('^')}
    link_lines = (TLOG/'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    starts = [i for i,l in enumerate(link_lines) if l.startswith('^')]+[len(link_lines)]
    blocks = [link_lines[a:b] for a,b in zip(starts,starts[1:])]
    blocks = [b for b in blocks if Path(re.search(r'/OUT:"([^"]+)"',b[1],re.I)[1]).resolve()==(ROOT/'bin/Common.dll').resolve()]
    assert len(blocks)==1,'Need the bin/Common.dll link record'
    link_lines = blocks[0]
    inputs = [Path(p) for p in link_lines[0][1:].split('|')]
    baseline = {str(p): digest(p) for p in inputs}
    assert all(p.stat().st_mtime <= (ROOT/'bin/Common.dll').stat().st_mtime for p in inputs), 'Newer link inputs'
    installed=digest(Path('D:/games/FL_MOD/bin/Common.dll'))
    previous=json.loads((OUT/'build.json').read_text())['dll'] if (OUT/'build.json').exists() else None
    approved=[digest(ROOT/'bin/Common.dll'),previous]
    installed_records=list((ROOT/'out/train_consist').glob('*/installed.json'))
    if (ROOT/'out/train_yard/installed.json').exists():installed_records.append(ROOT/'out/train_yard/installed.json')
    for path in installed_records:
        record=json.loads(path.read_text())['files'].get('bin/Common.dll')
        if record:approved.append(record['installed'])
    assert installed in approved, 'Installed Common changed independently'
    link = '\n'.join(link_lines[1:])
    for key, name in [('OUT','Common.dll'),('PDB','Common.pdb'),('IMPLIB','Common.lib'),('LTCGOUT','Common.iobj')]:
        link, n = re.subn(rf'/{key}:"[^"]+"', lambda m:f'/{key}:"{OUT/name}"', link, flags=re.I)
        assert n==1, key
    # Establish reproducibility before using these objects as a baseline.
    if '--baseline' in sys.argv:
        run('link.exe','baseline',link,compiler,env)
        def code(path):
            b=path.read_bytes(); pe=struct.unpack_from('<I',b,60)[0]
            count=struct.unpack_from('<H',b,pe+6)[0]; opt=struct.unpack_from('<H',b,pe+20)[0]
            for i in range(count):
                off=pe+24+opt+40*i
                if b[off:off+8].startswith(b'.text'):
                    size,ptr=struct.unpack_from('<II',b,off+16)
                    return b[ptr:ptr+size]
            raise AssertionError('Missing code')
        # Fresh LTCG can reorder/re-optimize code compared with an incremental link.
        identical=code(OUT/'Common.dll')==code(ROOT/'bin/Common.dll')
        (OUT/'baseline_verified.json').write_text(json.dumps(baseline,indent=2))
        print('Baseline relinked from recorded inputs; identical .text:',identical)
        return
    assert json.loads((OUT/'baseline_verified.json').read_text())==baseline,'Baseline must be verified first'
    for name in ['common_cship','common_physys_build','common_physys_query','common_engineobject','common_train','common_splinemoveidea','common_remotephysics','common_archetype_ships','common_archetypeloader']:
        original = name if name in commands else 'common_physys_build'
        command = commands[original]
        command = re.sub(r'/Fo"[^"]+"',lambda m:f'/Fo"{OUT/(name+".obj")}"',command,flags=re.I)
        command = re.sub(r'/Fd"[^"]+"',lambda m:f'/Fd"{OUT/"compile.pdb"}"',command,flags=re.I)
        if name != original:
            command,n = re.subn(rf'(?:"[^"\n]+{original}\.CPP"|[^\s"]+{original}\.CPP)\s*$',lambda m:f'"{ROOT/"src/Common"/(name+".cpp")}"',command,flags=re.I)
            assert n==1,original
        run('cl.exe',name,command,compiler,env)
        link,n = re.subn(rf'"[^"\n]+[\\/]{name}\.OBJ"',lambda m:f'"{OUT/(name+".obj")}"',link,flags=re.I)
        if name=='common_train' and n==0:
            link += f'\n"{OUT/(name+".obj")}"\n'
        else:
            assert n==1,name
    run('link.exe','link',link,compiler,env)
    assert all(digest(Path(p))==h for p,h in baseline.items()), 'Concurrent dependency change'
    (OUT/'build.json').write_text(json.dumps({'baseline':digest(ROOT/'bin/Common.dll'),
        'inputs':baseline,'dll':digest(OUT/'Common.dll')},indent=2))


if __name__=='__main__':
    main()
