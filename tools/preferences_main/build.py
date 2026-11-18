"""Relink the installed client with only the cached preferences mode probe replaced."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/preferences_main_hitch'
OUT = TOPIC / 'build'
BASE = ROOT / 'out/audio_timescale/build'
TLOG = ROOT / 'out/base_neural/on/obj/freelancer/freelancer.tlog'
GAME = Path('D:/Games/FL_MOD/bin')
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = BASE / 'freelancer.exe'
    installed = digest(GAME / 'freelancer.exe')
    previous = OUT / 'build.json'
    valid = {digest(baseline)}
    if previous.exists():
        saved = json.loads(previous.read_text())
        valid.update((saved['client'], saved['installed_at_build']))
    assert installed in valid, 'Installed client differs from the known link baseline'
    evidence = json.loads((BASE / 'build.json').read_text())
    assert digest(baseline) == evidence['client'], 'Baseline client changed'
    link = (BASE / 'link.rsp').read_text(encoding='utf-8')
    for name, value in evidence['inputs'].items():
        if digest(Path(name)) == value:
            continue
        # The optional graphics build copies old root import libraries over its
        # output. Recover the exact baseline library, not a newly rebuilt Common.
        replacement = ROOT / 'src/obj/train_courier/rpg1/bin/Common.lib'
        assert Path(name).name.lower() == 'common.lib' and digest(replacement) == value, 'Baseline input changed: ' + name
        shutil.copy2(replacement, OUT / 'Common.lib')
        link, count = re.subn(r'(?<![\w\\/])COMMON\.LIB\b',
                             lambda m: '"' + str(OUT / 'Common.lib') + '"', link, flags=re.I)
        assert count == 1
    inputs = {Path(p) for p in re.findall(r'"([^"\n]+\.(?:obj|lib|res))"', link, flags=re.I)}
    assert all(p.is_absolute() and p.is_file() for p in inputs)
    assert all(p.stat().st_mtime <= baseline.stat().st_mtime for p in inputs), 'Baseline link inputs changed'
    fingerprints = {str(p): digest(p) for p in inputs}
    lines = (TLOG / 'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    commands = [lines[i+1] for i, line in enumerate(lines)
                if line.startswith('^') and line.upper().endswith('\\CLIENT\\NN_PREFERENCES.CPP')]
    assert len(commands) == 1
    command = commands[0]
    for option, name in [('Fo', 'nn_preferences.obj'), ('Fd', 'compile.pdb')]:
        command, count = re.subn('/' + option + r'"[^\"]+"',
                                 lambda m: '/' + option + '"' + str(OUT / name) + '"', command, flags=re.I)
        assert count == 1
    link, count = re.subn(r'"[^"\n]+[\\/]NN_PREFERENCES\.OBJ"',
                         lambda m: '"' + str(OUT / 'nn_preferences.obj') + '"', link, flags=re.I)
    assert count == 1
    for option, name in [('OUT', 'freelancer.exe'), ('PDB', 'freelancer.pdb'),
                         ('IMPLIB', 'freelancer.lib'), ('LTCGOUT', 'freelancer.iobj')]:
        link, count = re.subn('/' + option + r':"[^\"]+"',
                             lambda m: '/' + option + ':"' + str(OUT / name) + '"', link, flags=re.I)
        assert count == 1
    compiler, env = compiler_env()
    sdk_um = next(Path(p) for p in env['INCLUDE'].split(';') if Path(p).name == 'um')
    env['INCLUDE'] += ';' + str(sdk_um.parent / 'winrt')
    for name, tool, content in [('compile', 'cl.exe', command), ('link', 'link.exe', link)]:
        rsp, log = OUT / (name + '.rsp'), OUT / (name + '.log')
        rsp.write_text(content, encoding='utf-8')
        with log.open('wb') as stream:
            result = subprocess.run([str(compiler / tool), '@' + str(rsp)], cwd=ROOT / 'src/freelancer',
                                    env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text(encoding='utf-8', errors='replace')[-10000:])
        result.check_returncode()
    assert all(digest(Path(p)) == value for p, value in fingerprints.items()), 'Concurrent baseline change'
    previous.write_text(json.dumps(dict(baseline=digest(baseline), installed_at_build=installed,
                                        client=digest(OUT / 'freelancer.exe'), inputs=fingerprints), indent=2))
    print('PASS: only nn_preferences.obj replaced; installed feature profile and audio extension preserved')

if __name__ == '__main__':
    main()
