"""Install the validated room-cache runtime pair; never launch or stop the game."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/room_materials'
BUILD = OUT/'runtime'
GAME = Path('D:/Games/FL_MOD/bin')
FILES = ('RP9.dll', 'RP9.pdb', 'freelancer.exe', 'freelancer.pdb')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_remove(path):
    path = path.absolute()
    assert path.is_relative_to(OUT.absolute()) and path != OUT.absolute()
    for parent in (path, *path.parents):
        assert not parent.is_symlink() and not parent.is_junction(), str(parent)
        if parent == OUT.absolute(): break
    if not path.exists(): return
    for child in path.rglob('*'):
        assert not child.is_symlink() and not child.is_junction(), str(child)
    shutil.rmtree(path)


def check_imports():
    compiler = sorted(Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC').iterdir())[-1]/'bin/Hostx64/x86'
    def dump(option, path):
        return subprocess.check_output([str(compiler/'dumpbin.exe'), option, str(path)], text=True)
    result = {}
    for file in ('RP9.dll', 'freelancer.exe'):
        current = None
        for line in dump('/imports', BUILD/'bin'/file).splitlines():
            match = re.fullmatch(r'    (\S+\.dll)', line, re.I)
            if match:
                dependency = GAME/match[1]
                current = match[1] if dependency.exists() else None
                if current and current not in result:
                    names = set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)', dump('/exports', dependency), re.M))
                    result[current] = dict(sha256=digest(dependency), names=names, checked=0)
            elif current:
                match = re.fullmatch(r'\s+[0-9A-F]+ (\S+)', line)
                if match:
                    assert match[1] in result[current]['names'], (file, current, match[1])
                    result[current]['checked'] += 1
    assert result['Common.dll']['checked'] > 100
    return {name: {k:v for k,v in record.items() if k != 'names'} for name,record in result.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); args = ap.parse_args()
    manifest = OUT/'cache_install_manifest.json'
    if not args.apply:
        imports = check_imports()
        source = json.loads((BUILD/'imports/source.json').read_text())
        assert digest(GAME/'Common.dll') == source['sha256']
        records = {name: dict(before=digest(GAME/name), after=digest(BUILD/'bin'/name)) for name in FILES}
        manifest.write_text(json.dumps(dict(files=records, imports=imports), indent=2))
        print('Prepared and checked imports:', ', '.join(FILES)); return
    tasks = subprocess.run(['tasklist','/FO','CSV','/NH'], capture_output=True, check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in tasks for name in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')), 'Close game/server first; no files changed'
    data = json.loads(manifest.read_text()); records = data['files']; assert set(records) == set(FILES)
    for name, record in records.items():
        assert digest(GAME/name) == record['before'] and digest(BUILD/'bin'/name) == record['after'], name
    for name, record in data['imports'].items(): assert digest(GAME/name) == record['sha256'], name
    backup = OUT/'cache_transaction'
    assert not backup.exists(), 'Unfinished transaction must be reviewed'
    backup.mkdir()
    for name in FILES: shutil.copy2(GAME/name, backup/name)
    try:
        for name in FILES: shutil.copy2(BUILD/'bin'/name, GAME/name)
        for name, record in records.items(): assert digest(GAME/name) == record['after'], name
    except BaseException:
        for name in FILES: shutil.copy2(backup/name, GAME/name)
        for name, record in records.items(): assert digest(GAME/name) == record['before'], name
        safe_remove(backup)
        raise
    data.update(verified=True, game_launched=False, dlss5=True, rpg_world=True)
    (OUT/'cache_installed.json').write_text(json.dumps(data, indent=2))
    for name in ('RP9', 'freelancer'):
        shutil.copy2(BUILD/'obj'/name/'build.log', OUT/('cache_build_'+name+'.log'))
    safe_remove(backup)
    safe_remove(BUILD)
    print('Installed and verified: RP9/client + current symbols. Build copies and rollback removed.')


if __name__ == '__main__': main()
