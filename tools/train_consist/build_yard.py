"""Build yard Server/client in isolated directories, using the staged Common ABI."""
from pathlib import Path
import argparse, os, shutil, subprocess, sys
sys.stdout.reconfigure(errors='replace')
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('project',choices=['Server','freelancer'])
args=parser.parse_args()
out=ROOT/'src/obj/train_yard'/args.project
bin=out/'bin';obj=out/'obj'
bin.mkdir(parents=True,exist_ok=True);obj.mkdir(parents=True,exist_ok=True)
for path in (ROOT/'bin').glob('*.lib'):shutil.copy2(path,bin/path.name)
shutil.copy2(ROOT/'src/obj/train_consist/Common.lib',bin/'Common.lib')
env=os.environ.copy();env['LIB']=str(bin)+';'+env.get('LIB','')
cmd=['C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
    str(ROOT/'src'/args.project/(args.project+'.vcxproj')),'/t:Build','/p:Configuration=Release',
    '/p:Platform=Win32','/p:PlatformToolset=v145','/p:FreelancerRp9=1','/p:Dx8SdkDir=C:/DXSDK',
    '/p:Dx9SdkDir=C:/DXSDK_Jun10','/p:BuildProjectReferences=false','/p:FreelancerRpgWorld=1',
    '/p:FlASanOutDir='+str(bin),'/p:OutDir='+str(bin)+'/', '/p:IntDir='+str(obj)+'/',
    '/m:4','/nr:false','/v:minimal','/nologo']
with (out/'build.log').open('wb') as log:
    result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((out/'build.log').read_text(encoding='utf-8',errors='replace')[-14000:])
result.check_returncode()
print('PASS:',args.project,'Release Win32 RPG=1;',out/'build.log')
