"""Build RP9 and the client against the current Common import library."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--client-only', action='store_true')
parser.add_argument('--common', action='store_true')
parser.add_argument('--build-dir', type=Path, default=root / 'out/shader_startup/build')
options = parser.parse_args()
build = options.build_dir.resolve()
assert build.is_relative_to(root / 'out'), 'Build outputs must stay under out/'
binary = build / 'bin'
binary.mkdir(parents=True, exist_ok=True)
if shutil.disk_usage(root).free < 4 * 1024**3:
    raise RuntimeError('Insufficient free space for the client build')
for library in (root / 'bin').glob('*.lib'):
    shutil.copy2(library, binary / library.name)
# The repository's old Common.lib omits newer installed exports. Link to the
# actual working Common.dll without rebuilding or replacing that dependency.
sys.path.insert(0, str(root / 'tools/room_materials'))
import import_installed
import_installed.OUT = build / 'imports'
import_installed.main()
shutil.copy2(import_installed.OUT / 'Common.lib', binary / 'Common.lib')
msbuild = 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe'
env = dict(os.environ)
env['LIB'] = str(binary) + ';' + env.get('LIB', '')
projects = ('freelancer',) if options.client_only else ('RP9', 'freelancer')
if options.common:
    projects = ('Common', *projects)
for project in projects:
    obj = build / 'obj' / project
    obj.mkdir(parents=True, exist_ok=True)
    args = [msbuild, str(root/'src'/project/(project+'.vcxproj')), '/t:Build',
            '/p:Configuration=Release', '/p:Platform=Win32', '/p:PlatformToolset=v145',
            '/p:FreelancerRp9=1', '/p:FreelancerDlss5=1', '/p:FreelancerRpgWorld=1',
            '/p:Dx8SdkDir=C:/DXSDK', '/p:Dx9SdkDir=C:/DXSDK_Jun10',
            '/p:BuildProjectReferences=false', '/p:FlASanOutDir='+str(binary),
            '/p:OutDir='+str(binary)+'/', '/p:IntDir='+str(obj)+'/', '/m:4', '/nr:false', '/v:minimal', '/nologo']
    log = obj/'shader_startup_build.log'
    with log.open('wb') as stream:
        result = subprocess.run(args, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(encoding='utf-8', errors='replace')[-10000:])
    result.check_returncode()
    print('PASS', project, flush=True)
