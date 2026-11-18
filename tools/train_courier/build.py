"""Build current sources in an isolated tree; never install into the running game."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('projects',nargs='+',choices=['Common','Server','Content','freelancer','RendComp','FLServer','RP9'])
    parser.add_argument('--rpg',choices=['0','1'],default='1')
    parser.add_argument('--rebuild',action='store_true',help='Recompile the selected projects from scratch')
    parser.add_argument('--production',action='store_true',help='Shipping build with crash dumps, without hang watchdog/legacy reporters or tick profiling; separate output tree')
    parser.add_argument('--base-neural',choices=['0','1'],help='Match the installed client optional base NR build profile')
    args=parser.parse_args()
    out=ROOT/'src/obj/train_courier'/('rpg'+args.rpg)
    if args.production:
        out=ROOT/'src/obj/production'/('rpg'+args.rpg)
    binary=out/'bin'
    binary.mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'bin').glob('*.lib'):
        if not (binary/path.name).exists():shutil.copy2(path,binary/path.name)
    env=os.environ.copy()
    env['LIB']=str(binary)+';'+env.get('LIB','')
    for project in args.projects:
        obj=out/project
        obj.mkdir(parents=True,exist_ok=True)
        cmd=['C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
             str(ROOT/'src'/project/(project+'.vcxproj')),'/t:Rebuild' if args.rebuild else '/t:Build','/p:Configuration=Release',
             '/p:Platform=Win32','/p:PlatformToolset=v145','/p:FreelancerRp9=1',
             '/p:Dx8SdkDir=C:/DXSDK','/p:Dx9SdkDir=C:/DXSDK_Jun10',
             '/p:BuildProjectReferences=false','/p:FreelancerRpgWorld='+args.rpg,
             '/p:FreelancerProduction='+('1' if args.production else '0'),
             '/p:FlASanOutDir='+str(binary),'/p:OutDir='+str(binary)+'/',
             '/p:IntDir='+str(obj)+'/', '/m:4','/nr:false','/v:minimal','/nologo']
        if args.base_neural is not None:
            cmd.append('/p:FreelancerDlss5='+args.base_neural)
        with (obj/'build.log').open('wb') as log:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            print((obj/'build.log').read_text(encoding='utf-8',errors='replace')[-14000:])
        result.check_returncode()
        print('PASS:',project,'RPG='+args.rpg,flush=True)
    print('Output:',binary,flush=True)

if __name__=='__main__':main()
