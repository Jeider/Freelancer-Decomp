"""Compile/run the production color grade shader on native D3D9, without wrappers."""
from pathlib import Path
import os
import shutil
import subprocess
import hashlib
import json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/color_grade/gpu';OUT.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0';dx=Path('C:/DXSDK_Jun10')
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um','winrt')]+[dx/'Include']))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
shutil.copy2(ROOT/'out/base_neural/on/bin/d3dx9_43.dll',OUT/'d3dx9_43.dll')
assert not (OUT/'D3D9.dll').exists() and not (OUT/'dxgi.dll').exists()
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/DNOMINMAX',
 f'/I{ROOT/"src/RP9"}',str(ROOT/'tools/graphics_settings/probe_color_grade.cpp'),'/Feprobe.exe','/link','d3d9.lib',str(dx/'Lib/x86/d3dx9.lib'),'user32.lib'],cwd=OUT,env=env,check=True)
result=subprocess.run([str(OUT/'probe.exe')],cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
(OUT/'result.txt').write_bytes(result.stdout);print(result.stdout.decode(errors='replace'));result.check_returncode()
(OUT/'verified.json').write_text(json.dumps({'shader_sha256':hashlib.sha256((ROOT/'src/RP9/ColorGradeShader.h').read_bytes()).hexdigest()},indent=2))
