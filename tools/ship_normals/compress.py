from pathlib import Path
import subprocess,json,hashlib,struct
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'src/obj/ship_normals'
script=OUT/'compress.cmd'
script.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /O2 /D_CRT_SECURE_NO_WARNINGS tools/ship_normals/compress.cpp '
 '/Fosrc/obj/ship_normals/compress.obj /Febin/ship_normal_compress.exe '
 '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd','/c',str(script)],cwd=ROOT,check=True)
subprocess.run([str(ROOT/'bin/ship_normal_compress.exe')],cwd=ROOT,check=True)
p=OUT/'generation.json';r=json.loads(p.read_text());total=0
for name,info in r['maps'].items():
 data=(OUT/'assets/DATA_EXTRA/SHIP_NORMALS'/name).read_bytes()
 assert data[:4]==b'DDS ' and data[84:88]==(b'DXT1' if info.get('kind')=='surface' else b'DXT5')
 assert struct.unpack_from('<I',data,28)[0]>1
 info.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data));total+=len(data)
r['total_bytes']=total;p.write_text(json.dumps(r,indent=2));print(f'Maps: {total/1048576:.1f} MiB with mipmaps')
