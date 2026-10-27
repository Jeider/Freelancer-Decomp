"""Build the three affected modules with the current FL_MOD feature set; never deploy."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/nomad_surfaces'
MSBUILD='C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe'
FEATURES=['Rp9','WalkMode','HudTargetView','HudStatusView','HudInventoryView','Jflp','Flplusplus','Flsharp','DbgOptions','Adoxa','ModPlugins','Language','PreciseRender','ParticleFx']
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for module in ['RP9','Shading','freelancer']:
        args=[MSBUILD,str(ROOT/f'src/{module}/{module}.vcxproj'),'/p:Configuration=Release','/p:Platform=Win32','/p:PlatformToolset=v145','/p:Dx8SdkDir=C:/DXSDK','/p:Dx9SdkDir=C:/DXSDK_Jun10','/p:BuildProjectReferences=false','/nologo','/v:minimal']
        args += [f'/p:Freelancer{f}=1' for f in FEATURES]
        with (OUT/f'build-{module}.log').open('wb') as log:r=subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        print(f'{module}: exit {r.returncode}, log {OUT/f"build-{module}.log"}',flush=True);r.check_returncode()
if __name__=='__main__':main()
