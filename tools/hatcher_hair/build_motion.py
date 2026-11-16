"""Build the ABI-preserving Deformable2 motion extension in the current shipping tree."""
from pathlib import Path
import subprocess,argparse
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['Common','Deformable2'],default='Deformable2');project=parser.parse_args().project
binary=ROOT/'out/base_neural/on/bin';obj=ROOT/'out/base_neural/on/obj'/project
obj.mkdir(parents=True,exist_ok=True)
command=['C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe',
 str(ROOT/'src'/project/(project+'.vcxproj')),'/t:Build','/p:Configuration=Release','/p:Platform=Win32',
 '/p:PlatformToolset=v145','/p:FreelancerRp9=1','/p:FreelancerDlss5=1','/p:FreelancerRpgWorld=1',
 '/p:Dx8SdkDir=C:/DXSDK','/p:Dx9SdkDir=C:/DXSDK_Jun10','/p:BuildProjectReferences=false',
 '/p:FlASanOutDir='+str(binary),'/p:OutDir='+str(binary)+'/', '/p:IntDir='+str(obj)+'/',
 '/m:4','/nr:false','/v:minimal','/nologo']
subprocess.run(command,cwd=ROOT,check=True)
