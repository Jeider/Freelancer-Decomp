"""Exercise the actual asynchronous logger, client export and a separate DLL."""
import csv
import os
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/'src/obj/hitch_log'
out.mkdir(parents=True,exist_ok=True)
cmd=out/'check.cmd'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" >nul\n'
 'if errorlevel 1 exit /b 1\n'
 'cl /nologo /EHsc /std:c++17 /W3 /WX /Isrc/include /LD tools/hitch_log/check_dll.cpp /Fosrc/obj/hitch_log/dll.obj /Fesrc/obj/hitch_log/hitch_fixture.dll\n'
 'if errorlevel 1 exit /b 1\n'
 'cl /nologo /EHsc /std:c++17 /W3 /WX /Isrc/include /Isrc/freelancer/Client tools/hitch_log/check.cpp /Fosrc/obj/hitch_log/check.obj /Fesrc/obj/hitch_log/check.exe\n')
subprocess.run(['cmd','/c',str(cmd)],cwd=root,check=True)
env=dict(os.environ,LOCALAPPDATA=str(out),FREELANCER_HITCH_LOG='1')
subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)
latest=max((out/'Freelancer-Decomp/Diagnostics').glob('*.csv'),key=lambda p:p.stat().st_mtime_ns)
with latest.open(newline='') as f: rows=list(csv.DictReader(f))
categories={r['category'] for r in rows}
assert {'frame','frame_interval','sound_load','texture','model_load'}<=categories,categories
sound=next(r for r in rows if r['category']=='sound_load')
assert sound['resource']=='voice,"test".wav'
frame=next(r for r in rows if r['category']=='frame')
assert float(frame['start_ms'])<=float(sound['start_ms'])<float(sound['end_ms'])<=float(frame['end_ms'])
assert next(r for r in rows if r['category']=='texture')['thread']!=frame['thread']
assert next(r for r in rows if r['category']=='model_load')['resource']=='from_dll.cmp'
assert all(float(r['duration_ms'])>0 for r in rows)
print('PASS: async CSV, live file access, nested spans, timestamps, frame intervals, worker IDs, DLL callbacks, shutdown flush')
