"""Build the affected modules with the installed equipment-capable feature set."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nomad_surfaces'))
from build import MSBUILD,FEATURES

for module in ('RP9','freelancer'):
    log=ROOT/f'src/obj/ship_normals/build-{module}.log'
    args=[MSBUILD,str(ROOT/f'src/{module}/{module}.vcxproj'),'/p:Configuration=Release',
        '/p:Platform=Win32','/p:PlatformToolset=v145','/p:Dx8SdkDir=C:/DXSDK',
        '/p:Dx9SdkDir=C:/DXSDK_Jun10','/p:BuildProjectReferences=false','/nr:false','/nologo','/v:minimal']
    args += [f'/p:Freelancer{f}=1' for f in FEATURES+['EquipmentSlots']]
    with log.open('wb') as out: result=subprocess.run(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
    print(f'{module}: {result.returncode}, {log}',flush=True)
    result.check_returncode()
