"""Build Common from the verified train baseline, then client/server with its ABI."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.stdout.reconfigure(errors='replace')

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/base_interiors'
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env, digest


def common():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler, env = compiler_env()
    baseline = ROOT/'src/obj/train_consist'
    record = json.loads((baseline/'build.json').read_text())
    assert digest(baseline/'Common.dll') == record['dll']
    assert all(digest(Path(p)) == h for p, h in record['inputs'].items())
    rows = (ROOT/'src/obj/Common/Release/Common.tlog/CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    commands = {Path(line[1:]).stem.lower(): rows[i+1] for i, line in enumerate(rows) if line.startswith('^')}
    link = (baseline/'link.rsp').read_text()
    def run(tool, name, command):
        rsp = OUT/(name+'.rsp')
        rsp.write_text(command)
        log = OUT/(name+'.log')
        with log.open('wb') as stream:
            result = subprocess.run([str(compiler/tool), '@'+str(rsp)], cwd=ROOT/'src/Common',
                                    env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text(errors='replace')[-12000:])
        result.check_returncode()
        print('PASS:', name, flush=True)
    for key, name in [('OUT','Common.dll'),('PDB','Common.pdb'),('IMPLIB','Common.lib'),('LTCGOUT','Common.iobj')]:
        link, n = re.subn(rf'/{key}:"[^"]+"', lambda m:f'/{key}:"{OUT/name}"', link, flags=re.I)
        assert n == 1, key
    for name in ['common_basedata','common_roomdata','common_roominfo','common_interior_profiles']:
        original = name if name in commands else 'common_basedata'
        command = commands[original]
        command = re.sub(r'/Fo"[^"]+"', lambda m:f'/Fo"{OUT/(name+".obj")}"', command, flags=re.I)
        command = re.sub(r'/Fd"[^"]+"', lambda m:f'/Fd"{OUT/"compile.pdb"}"', command, flags=re.I)
        if name != original:
            command,n = re.subn(rf'(?:"[^"\n]+{original}\.CPP"|[^\s"]+{original}\.CPP)\s*$',
                                lambda m:f'"{ROOT/"src/Common"/(name+".cpp")}"',command,flags=re.I)
            assert n == 1
        run('cl.exe', name, command)
        link,n = re.subn(rf'"[^"\n]+[\\/]{name}\.OBJ"', lambda m:f'"{OUT/(name+".obj")}"',link,flags=re.I)
        if name == 'common_interior_profiles' and n == 0:
            link += f'\n"{OUT/(name+".obj")}"\n'
        else:
            assert n == 1, name
    run('link.exe', 'link', link)
    (OUT/'build.json').write_text(json.dumps({'baseline':record['dll'],'dll':digest(OUT/'Common.dll')},indent=2))


def project(name):
    # Reuse the existing isolated RPG object directories; MSBuild tracks edits.
    out = ROOT/'src/obj/train_yard'/name
    binary, obj = out/'bin', out/'obj'
    binary.mkdir(parents=True,exist_ok=True)
    obj.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'bin').glob('*.lib'):
        shutil.copy2(path,binary/path.name)
    shutil.copy2(OUT/'Common.lib',binary/'Common.lib')
    env = os.environ.copy()
    env['LIB'] = str(binary)+';'+env.get('LIB','')
    cmd = ['C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
           str(ROOT/'src'/name/(name+'.vcxproj')), '/t:Build','/p:Configuration=Release',
           '/p:Platform=Win32','/p:PlatformToolset=v145','/p:FreelancerRp9=1','/p:Dx8SdkDir=C:/DXSDK',
           '/p:Dx9SdkDir=C:/DXSDK_Jun10','/p:BuildProjectReferences=false','/p:FreelancerRpgWorld=1',
           '/p:FlASanOutDir='+str(binary),'/p:OutDir='+str(binary)+'/', '/p:IntDir='+str(obj)+'/',
           '/m:4','/nr:false','/v:minimal','/nologo']
    with (out/'build.log').open('wb') as log:
        result = subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print((out/'build.log').read_text(errors='replace')[-14000:])
    result.check_returncode()
    print('PASS:',name,'Release Win32 RPG=1',flush=True)


if __name__ == '__main__':
    if Path(__file__).with_name('ARCHIVED').exists():
        raise SystemExit('Capital interiors are archived; experimental builds are disabled. See README.txt.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',choices=['Common','Server','freelancer'])
    args = parser.parse_args()
    common() if args.project == 'Common' else project(args.project)
