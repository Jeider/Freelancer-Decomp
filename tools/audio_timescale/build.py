"""Build the optional audio extension and client; never launch or install the game."""
from pathlib import Path
import os
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/train_courier/rpg1'
CLIENT_BASE = ROOT / 'out/base_neural/on'
PAYLOAD = ROOT / 'out/audio_timescale/build'
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_client():
    # Preserve the exact installed feature switches and unrelated compiled objects.
    baseline = CLIENT_BASE / 'bin/freelancer.exe'
    installed = Path('D:/Games/FL_MOD/bin/freelancer.exe')
    previous = PAYLOAD / 'build.json'
    valid = {digest(baseline)}
    if previous.exists():
        saved = json.loads(previous.read_text())
        valid.add(saved['client'])
        if 'installed_at_build' in saved:
            valid.add(saved['installed_at_build'])
    assert digest(installed) in valid, 'Installed client differs from the known link baseline'
    tlog = CLIENT_BASE / 'obj/freelancer/freelancer.tlog'
    compile_lines = (tlog / 'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    link_lines = (tlog / 'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    assert sum(line.startswith('^') for line in link_lines) == 1
    inputs = [Path(p) for p in link_lines[0][1:].split('|')]
    assert all(p.stat().st_mtime <= baseline.stat().st_mtime for p in inputs), 'Baseline objects changed'
    input_hashes = {str(p): digest(p) for p in inputs}
    compiler, env = compiler_env()
    # WRL's ComPtr lives in the Windows SDK's winrt headers (MSBuild adds this).
    sdk_um = next(Path(p) for p in env['INCLUDE'].split(';') if Path(p).name == 'um')
    env['INCLUDE'] += ';' + str(sdk_um.parent / 'winrt')
    def run(name, tool, command):
        rsp = PAYLOAD / (name + '.rsp')
        rsp.write_text(command, encoding='utf-8')
        log = PAYLOAD / (name + '.log')
        with log.open('wb') as stream:
            result = subprocess.run([str(compiler / tool), '@' + str(rsp)],
                                    cwd=ROOT / 'src/freelancer', env=env,
                                    stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text(encoding='utf-8', errors='replace')[-10000:])
        result.check_returncode()
    link = '\n'.join(link_lines[1:])
    for name in ('menu_sound_arch', 'dbg_console'):
        matches = [compile_lines[i+1] for i, line in enumerate(compile_lines)
                   if line.startswith('^') and line.upper().endswith('\\CLIENT\\' + name.upper() + '.CPP')]
        assert len(matches) == 1, name
        command = matches[0]
        assert 'FREELANCER_DBG_OPTIONS' in command
        for option, target in [('Fo', name + '.obj'), ('Fd', 'compile.pdb')]:
            command, count = re.subn('/' + option + r'"[^\"]+"',
                                     lambda m: '/' + option + '"' + str(PAYLOAD / target) + '"', command, flags=re.I)
            assert count == 1, option
        run(name, 'cl.exe', command)
        link, count = re.subn(r'"[^"\n]+[\\/]' + name + r'\.OBJ"',
                             lambda m: '"' + str(PAYLOAD / (name + '.obj')) + '"', link, flags=re.I)
        assert count == 1, name
    for option, target in [('OUT', 'freelancer.exe'), ('PDB', 'freelancer.pdb'),
                           ('IMPLIB', 'freelancer.lib'), ('LTCGOUT', 'freelancer.iobj')]:
        link, count = re.subn('/' + option + r':"[^\"]+"',
                             lambda m: '/' + option + ':"' + str(PAYLOAD / target) + '"', link, flags=re.I)
        assert count == 1, option
    run('link', 'link.exe', link)
    assert all(digest(Path(p)) == value for p, value in input_hashes.items()), 'Concurrent baseline change'
    previous.write_text(json.dumps(dict(baseline=digest(baseline), client=digest(PAYLOAD / 'freelancer.exe'),
                                        installed_at_build=digest(installed),
                                        inputs=input_hashes), indent=2))
    print('PASS: client; only menu_sound_arch.obj and dbg_console.obj replaced', flush=True)

def main():
    PAYLOAD.mkdir(parents=True, exist_ok=True)
    binary = OUT / 'bin'
    binary.mkdir(parents=True, exist_ok=True)
    for lib in (ROOT / 'bin').glob('*.lib'):
        if not (binary / lib.name).exists():
            shutil.copy2(lib, binary / lib.name)
    env = os.environ.copy()
    env['LIB'] = str(binary) + ';' + env.get('LIB', '')
    for project in ('SoundManager', 'SoundStreamer'):
        build_audio(project, binary, env)
    build_client()

def build_audio(project, binary, env):
    obj = OUT / project
    obj.mkdir(parents=True, exist_ok=True)
    command = [
        'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
        str(ROOT / 'src' / project / (project + '.vcxproj')), '/t:Build',
        '/p:Configuration=Release', '/p:Platform=Win32', '/p:PlatformToolset=v145',
        '/p:FreelancerRp9=1', '/p:Dx8SdkDir=C:/DXSDK', '/p:Dx9SdkDir=C:/DXSDK_Jun10',
        '/p:BuildProjectReferences=false', '/p:FreelancerRpgWorld=1',
        '/p:FreelancerProduction=0', '/p:FlASanOutDir=' + str(binary),
        '/p:OutDir=' + str(binary) + '/', '/p:IntDir=' + str(obj) + '/',
        '/m:4', '/nr:false', '/v:minimal', '/nologo',
    ]
    log = obj / 'build.log'
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(encoding='utf-8', errors='replace')[-14000:])
    result.check_returncode()
    print('PASS:', project, flush=True)
    for name in (project + '.dll', project + '.pdb'):
        shutil.copy2(binary / name, PAYLOAD / name)

if __name__ == '__main__':
    main()
