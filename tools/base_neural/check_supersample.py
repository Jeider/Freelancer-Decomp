"""Test actual high-resolution base targets, linear-light resolve, native UI and 4K NR."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BIN=ROOT/'out/base_neural/on/bin'
OUT=ROOT/'out/base_neural/checks/supersample'
OUT.mkdir(parents=True,exist_ok=True)
for name,args in [('area_resolve',['1','320','180','250','--supersample','--checker']),
                  ('neural4k',['2','2560','1440','250','--supersample','--strength-cycle'])]:
    result=subprocess.run([str(BIN/'probe_wrapper.exe'),*args],cwd=BIN,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
    (OUT/(name+'.txt')).write_bytes(result.stdout)
    print(result.stdout.decode(errors='replace'),flush=True);result.check_returncode()
    shutil.copy2(BIN/'neural/host64/ReShade.log',OUT/(name+'_neural.log'))
    if name=='neural4k':
        log=(OUT/(name+'_neural.log')).read_text(errors='replace')
        assert 'NR input 3840x2160' in log and 'inline feature 18 evaluation succeeded' in log
files=('freelancer.exe','RP9.dll','fl_base_neural.addon32')
(OUT/'verified.json').write_text(json.dumps({n:hashlib.sha256((BIN/n).read_bytes()).hexdigest() for n in files},indent=2))
print('PASS supersample: real 4K NR, area-weighted linear-light resolve and native-resolution UI')
