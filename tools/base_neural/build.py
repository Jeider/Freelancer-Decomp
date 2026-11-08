"""Build optional base NR integration in isolated on/off output trees."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MSBUILD = Path('C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--enabled', choices=['0', '1'], default='1')
    ap.add_argument('--projects', nargs='+', default=['RP9', 'freelancer'], choices=['RP9', 'freelancer'])
    a = ap.parse_args()
    out = ROOT/'out/base_neural'/('on' if a.enabled == '1' else 'off')
    binary = out/'bin'
    binary.mkdir(parents=True, exist_ok=True)
    for lib in (ROOT/'bin').glob('*.lib'):
        shutil.copy2(lib, binary/lib.name)
    env = os.environ.copy()
    env['LIB'] = str(binary)+';'+env.get('LIB', '')
    for project in a.projects:
        obj = out/'obj'/project
        obj.mkdir(parents=True, exist_ok=True)
        cmd = [str(MSBUILD), str(ROOT/'src'/project/(project+'.vcxproj')), '/t:Build',
               '/p:Configuration=Release', '/p:Platform=Win32', '/p:PlatformToolset=v145',
               '/p:FreelancerRp9=1', '/p:FreelancerDlss5='+a.enabled,
               '/p:Dx8SdkDir=C:/DXSDK', '/p:Dx9SdkDir=C:/DXSDK_Jun10',
               '/p:BuildProjectReferences=false', '/p:FreelancerRpgWorld=1',
               '/p:FlASanOutDir='+str(binary), '/p:OutDir='+str(binary)+'/',
               '/p:IntDir='+str(obj)+'/', '/m:4', '/nr:false', '/v:minimal', '/nologo']
        log = obj/'build.log'
        with log.open('wb') as stream:
            result = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(log.read_text(encoding='utf-8', errors='replace')[-12000:])
        result.check_returncode()
        print(f'PASS {project} FreelancerDlss5={a.enabled}', flush=True)

if __name__ == '__main__':
    main()
