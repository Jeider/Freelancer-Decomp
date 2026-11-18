from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/hair_lighting';OUT.mkdir(exist_ok=True)
src=ROOT/'src/Thorn/lua32';files=' '.join('"'+str(p)+'"' for p in list((src/'src').glob('*.c'))+[src/'lparser_stub.c'])
cmd=OUT/'build_lights.cmd';cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\ncl /nologo /O2 /D_CRT_SECURE_NO_WARNINGS /I"'+str(src/'include')+'" /I"'+str(src/'src')+'" '+files+' "'+str(ROOT/'tools/room_materials/read_bar_lights.c')+'" /Febar_lights.exe\n')
cmd.write_text(cmd.read_text().replace(' /O2 ', ' /O2 /I"'+str(ROOT/'src/include')+'" '))
with (OUT/'build.log').open('w') as log:subprocess.run(['cmd','/c',str(cmd)],cwd=OUT,check=True,stdout=log,stderr=subprocess.STDOUT)
result=subprocess.run([str(OUT/'bar_lights.exe'),'D:/Games/FL_MOD/DATA/SCRIPTS/BASES/Br_01_Bar_ambi_int_01.thn'],cwd=OUT,capture_output=True,text=True,check=True)
(OUT/'avalon_bar_lights.txt').write_text(result.stdout);print(result.stdout)
