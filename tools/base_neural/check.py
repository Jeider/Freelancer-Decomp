"""Validate compile exclusion and run the hidden GPU integration/failure probes."""
from pathlib import Path
import argparse
import json
import hashlib
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[2]
BIN=ROOT/'out/base_neural/on/bin'
REPORT=ROOT/'out/base_neural/checks'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--gpu',action='store_true')
    a=ap.parse_args()
    REPORT.mkdir(parents=True,exist_ok=True)
    for enabled in ('on','off'):
        for name in ('freelancer.exe','RP9.dll'):
            data=(ROOT/'out/base_neural'/enabled/'bin'/name).read_bytes()
            present=b'IRPBaseNeural_v2' in data
            if present!=(enabled=='on'):raise RuntimeError(f'{enabled}/{name}: compile exclusion failed')
    print('PASS both clients/renderers: interface present only with FreelancerDlss5=1',flush=True)
    if not a.gpu:return
    tests=[('identity',[str(BIN/'probe_wrapper.exe'),'1']),
           ('neural1440',[str(BIN/'probe_wrapper.exe'),'2','2560','1440']),
           ('kill_host',[str(BIN/'probe_feed.exe'),str(BIN/'neural/host64'),'1','--kill-host']),
           ('cancel_startup',[str(BIN/'probe_feed.exe'),str(BIN/'neural/host64'),'1','--cancel-startup']),
           ('transport',[str(BIN/'probe_feed.exe'),str(BIN/'neural/host64'),'1'])]
    results=[]
    for name,cmd in tests:
        start=time.monotonic()
        result=subprocess.run(cmd,cwd=BIN,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        folder=REPORT/name;folder.mkdir(exist_ok=True)
        (folder/'stdout.txt').write_bytes(result.stdout)
        for src,dst in [(BIN/'ReShade.log','adapter.log'),(BIN/'neural/host64/ReShade.log','neural.log'),
                        (BIN/'neural/host64/dlss5-feed-host.log','host.log')]:
            if src.exists():shutil.copy2(src,folder/dst)
        results.append({'test':name,'seconds':round(time.monotonic()-start,3),'exit_code':result.returncode})
        (REPORT/'results.json').write_text(json.dumps(results,indent=2))
        print(result.stdout.decode(errors='replace').strip(),flush=True)
        result.check_returncode()
        if name=='neural1440' and 'inline feature 18 evaluation succeeded' not in (folder/'neural.log').read_text(errors='replace'):
            raise RuntimeError('No proof of actual signed NR evaluation; DLAA-only is not a pass')
        print(f'PASS {name}',flush=True)
    names=['freelancer.exe','RP9.dll','fl_base_neural.addon32','D3D9.dll','dxgi.dll',
           'neural/host64/fl_base_neural_host.exe','neural/host64/nvngx_dlss.dll',
           'neural/host64/nvngx_dlssnr.dll','neural/host64/renodx-dlss5.addon64','neural/host64/dxgi.dll']
    (REPORT/'binaries.json').write_text(json.dumps({n:hashlib.sha256((BIN/n).read_bytes()).hexdigest() for n in names},indent=2))

if __name__=='__main__':main()
