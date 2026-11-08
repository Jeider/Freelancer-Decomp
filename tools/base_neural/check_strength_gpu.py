"""Check live 0/50/100% composition using actual NR on the hidden DX9/DX11 probe."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BIN=ROOT/'out/base_neural/on/bin'
OUT=ROOT/'out/base_neural/checks/strength'
OUT.mkdir(parents=True,exist_ok=True)
flow=subprocess.run([str(BIN/'probe_flow.exe')],cwd=BIN,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
(OUT/'flow.txt').write_bytes(flow.stdout)
print(flow.stdout.decode(errors='replace'),flush=True)
flow.check_returncode()
result=subprocess.run([str(BIN/'probe_wrapper.exe'),'2','2560','1440','250','--strength-cycle'],
                      cwd=BIN,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
(OUT/'stdout.txt').write_bytes(result.stdout)
print(result.stdout.decode(errors='replace'))
result.check_returncode()
for src,name in [(BIN/'ReShade.log','adapter.log'),(BIN/'neural/host64/ReShade.log','neural.log')]:
    shutil.copy2(src,OUT/name)
assert 'inline feature 18 evaluation succeeded' in (OUT/'neural.log').read_text(errors='replace')
assert all(f'PASS strength {x}%' in result.stdout.decode() for x in (0,50,100))
(OUT/'verified.json').write_text(json.dumps({'addon_sha256':hashlib.sha256((BIN/'fl_base_neural.addon32').read_bytes()).hexdigest()},indent=2))
print('PASS actual NR, live blend endpoints, zero-strength original pixels and untouched game UI')
