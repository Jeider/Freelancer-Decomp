"""Verify presence routing, client lifetime, campaign regression and binary imports."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    for script,args in (('tools/base_presence/check.py',[]),
                        ('tools/base_presence/check_emotes.py',[]),
                        ('tools/base_presence/check_root_motion.py',[]),
                        ('tools/train_courier/check_campaign_server.py',['--with-client'])):
        subprocess.run([sys.executable,str(ROOT/script)]+args,check=True)
    checks=json.loads((ROOT/'out/campaign_server/check/verified.json').read_text(encoding='utf-8'))
    inputs=[Path(__file__),ROOT/'tools/base_presence/check.py',ROOT/'tools/base_presence/install.py',
            ROOT/'tools/train_courier/install_local_triggers.py',ROOT/'src/include/base_presence.h',ROOT/'src/include/base_emotes.h']
    inputs += [ROOT/'src/freelancer/Client'/name for name in
               ('base_walk.cpp','base_walk.h','base_walk_math.h','base_presence_client.inl','client_iclient.cpp','win3d.cpp','nav_bar.cpp','nav_bar.h')]
    checks.update({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    out=ROOT/'out/base_presence/check'
    out.mkdir(parents=True,exist_ok=True)
    (out/'verified.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('PASS checked presence bundle, compatible runtime dependencies and campaign regression')


if __name__=='__main__':main()
