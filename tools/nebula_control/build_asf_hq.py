"""Recompile cli_asteroid only, relink the last built client into an isolated directory.

Retains the last build's feature switches and other objects: unrelated in-progress
source changes in this shared checkout must not enter this installation.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/asf_hq'
BASE = ROOT / 'src/obj/rpg_contacts/build_Release_1_client'
TLOG = BASE / 'obj/freelancer.tlog'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compiler_env():
    vc = sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Tools/MSVC/*'))[-1]
    sdk = Path('C:/Program Files (x86)/Windows Kits/10')
    ver = sorted(p.name for p in (sdk / 'Include').iterdir() if (p / 'um/Windows.h').exists())[-1]
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(map(str, [vc/'include', sdk/f'Include/{ver}/ucrt', sdk/f'Include/{ver}/shared', sdk/f'Include/{ver}/um', Path('C:/DXSDK/include')]))
    env['LIB'] = ';'.join(map(str, [vc/'lib/x86', sdk/f'Lib/{ver}/ucrt/x86', sdk/f'Lib/{ver}/um/x86']))
    env['PATH'] = str(sdk/f'bin/{ver}/x86')+';'+str(vc/'bin/Hostx64/x86')+';'+env['PATH']
    return vc / 'bin/Hostx64/x86', env


def main(previous=None):
    OUT.mkdir(parents=True, exist_ok=True)
    client = BASE / 'bin/freelancer.exe'
    installed = digest(Path('D:/games/FL_MOD/bin/freelancer.exe'))
    assert installed == (previous['client'] if previous else digest(client)), 'Baseline differs from installed client'
    if previous:
        assert digest(client) == previous['baseline_client'], 'Original link baseline changed'
    lines = (TLOG / 'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    matches = [lines[i+1] for i, line in enumerate(lines) if line.startswith('^') and line.upper().endswith('\\CLIENT\\CLI_ASTEROID.CPP')]
    assert len(matches) == 1
    command = matches[0]
    command = re.sub(r'/Fo"[^"]+"', lambda m: f'/Fo"{OUT / "cli_asteroid.obj"}"', command, flags=re.I)
    command = re.sub(r'/Fd"[^"]+"', lambda m: f'/Fd"{OUT / "compile.pdb"}"', command, flags=re.I)
    assert '/D FREELANCER_RP9 ' in command
    compiler, env = compiler_env()

    link_lines = (TLOG / 'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    assert sum(line.startswith('^') for line in link_lines) == 1
    # Refuse a mixed baseline or concurrent edits to existing compiled dependencies.
    inputs = [Path(p) for p in link_lines[0][1:].split('|')]
    assert all(p.stat().st_mtime <= client.stat().st_mtime for p in inputs), 'Link inputs newer than baseline'
    baseline = {str(p): digest(p) for p in inputs}
    if previous:
        assert baseline == previous['inputs'], 'Previously linked inputs changed'
    link = '\n'.join(link_lines[1:])
    for key, name in [('OUT', 'freelancer.exe'), ('PDB', 'freelancer.pdb'), ('IMPLIB', 'freelancer.lib'), ('LTCGOUT', 'freelancer.iobj')]:
        link, count = re.subn(rf'/{key}:"[^"]+"', lambda m: f'/{key}:"{OUT / name}"', link, flags=re.I)
        assert count == 1, key
    link, count = re.subn(r'"[^"\n]+[\\/]CLI_ASTEROID\.OBJ"', lambda m: f'"{OUT / "cli_asteroid.obj"}"', link, flags=re.I)
    assert count == 1
    for name, tool, content in [('compile', 'cl.exe', command), ('link', 'link.exe', link)]:
        rsp = OUT / f'{name}.rsp'
        rsp.write_text(content, encoding='utf-8')
        with (OUT / f'{name}.log').open('wb') as log:
            result = subprocess.run([str(compiler/tool), '@'+str(rsp)], cwd=ROOT/'src/freelancer', env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((OUT / f'{name}.log').read_text(errors='replace')[-8000:])
        result.check_returncode()
        print('PASS:', name, flush=True)
    assert all(digest(Path(p)) == h for p, h in baseline.items()), 'Concurrent change to link inputs'
    evidence = {'baseline_client': installed, 'link_baseline_client': digest(client), 'inputs': baseline,
                'source': digest(ROOT/'src/freelancer/Client/cli_asteroid.cpp'),
                'client': digest(OUT/'freelancer.exe')}
    (OUT/'build.json').write_text(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fields', action='store_true', help='Continue the installed ASF fix, preserving its original link inputs')
    args = parser.parse_args()
    previous = json.loads((OUT/'build.json').read_text()) if args.fields else None
    if args.fields:
        OUT = ROOT/'src/obj/field_fog'
    main(previous)
