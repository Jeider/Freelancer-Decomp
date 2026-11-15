"""Verify campaign/offer/client regression checks and record the install inputs."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
for script,args in (('check_personal_offer.py',[]),('check_campaign_server.py',['--with-client'])):
    subprocess.run([sys.executable,str(Path(__file__).parent/script)]+args,check=True)
report=json.loads((ROOT/'out/campaign_server/check/verified.json').read_text(encoding='utf-8'))
for path in [Path(__file__),Path(__file__).with_name('check_personal_offer.py'),
             ROOT/'src/include/personal_story_offer.h',
             ROOT/'src/freelancer/Client/gf_script_object.cpp',
             ROOT/'src/freelancer/Client/gf_character_object.cpp']:
    report[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
out=ROOT/'out/personal_offer/check'
out.mkdir(parents=True,exist_ok=True)
(out/'verified.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
