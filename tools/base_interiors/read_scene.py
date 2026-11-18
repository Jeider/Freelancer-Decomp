from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar/prototype_v1';BUILD=TOP/'tool_cache';BUILD.mkdir(parents=True,exist_ok=True)
src=ROOT/'src/Thorn/lua32';files=' '.join('"'+str(p)+'"' for p in list((src/'src').glob('*.c'))+[src/'lparser_stub.c'])
cmd=BUILD/'build_scene.cmd';cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\ncl /nologo /O2 /D_CRT_SECURE_NO_WARNINGS /I"'+str(ROOT/'src/include')+'" /I"'+str(src/'include')+'" /I"'+str(src/'src')+'" '+files+' "'+str(ROOT/'tools/base_interiors/read_scene.c')+'" /Fescene_read.exe\n')
with (BUILD/'build.log').open('w') as log:subprocess.run(['cmd','/c',str(cmd)],cwd=BUILD,check=True,stdout=log,stderr=subprocess.STDOUT)
for stem in ('Rh_01_Bar_hardpoint_01','Rh_01_Bar_ambi_int_01'):
 result=subprocess.run([str(BUILD/'scene_read.exe'),'D:/Games/FL_MOD/DATA/SCRIPTS/BASES/'+stem+'.thn'],capture_output=True,text=True,check=True)
 data=json.loads(result.stdout);(OUT/(stem+'.json')).write_text(json.dumps(data,indent=2));print(stem,len(data['entities']))
