"""Build a small hidden D3D9 UV regression; all temporary files stay on D:."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_interiors/rh_biz_01_base/shipdealer/uv_fix'
SOURCE=ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl'
GAME=Path('D:/Games/FL_MOD/DATA_EXTRA/SHADERS/room_material.hlsl')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=OUT/'before_shader.hlsl'
    if not before.exists():before.write_bytes(GAME.read_bytes())
    command=OUT/'build.cmd'
    command.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
        'if errorlevel 1 exit /b 1\n'
        f'cl /nologo /EHsc /MD /O2 /std:c++17 /DNOMINMAX /I"C:/DXSDK_Jun10/Include" '
        f'"{ROOT}/tools/room_materials/check_uv_selection.cpp" /Fo"{OUT}/check.obj" /Fe"{OUT}/check.exe" '
        '/link /LIBPATH:"C:/DXSDK_Jun10/Lib/x86" d3d9.lib d3dx9.lib user32.lib\n')
    env=dict(os.environ,TEMP=str(OUT),TMP=str(OUT))
    with (OUT/'build.log').open('wb') as log:
        result=subprocess.run(['cmd','/c',str(command)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:print('UV fixture build failed; see',OUT/'build.log');return result.returncode
    with (OUT/'gpu.log').open('wb') as log:
        result=subprocess.run([str(OUT/'check.exe'),str(before),str(SOURCE)],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    print((OUT/'gpu.log').read_text(encoding='utf8',errors='replace'))
    report=dict(passed=result.returncode==0,before_sha256=digest(before),fixed_sha256=digest(SOURCE),
        before_source=str(before),fixed_source=str(SOURCE),game_target=str(GAME),
        scope='Real D3D9 GPU: VSMain and VSSkin, UV channels 0/1/2, both texture transforms, unused NaN/Inf, original shader negative control; PSMain compilation.',
        game_launched=False)
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return result.returncode


if __name__=='__main__':sys.exit(main())
