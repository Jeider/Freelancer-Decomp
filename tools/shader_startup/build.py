"""Build RP9 and the client against the current Common import library."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
binary = root / 'out/base_neural/on/bin'
msbuild = 'C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe'
env = dict(os.environ)
env['LIB'] = str(binary) + ';' + env.get('LIB', '')
for project in ('RP9', 'freelancer'):
    obj = root / 'out/base_neural/on/obj' / project
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
