"""Deactivate the regressing Tau4 compound and restore the pre-experiment engine."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import ulster_shortbase as p
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    running=subprocess.run(['tasklist','/FI','IMAGENAME eq freelancer.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=True)
    assert 'freelancer.exe' not in running.stdout.lower(),'Close game first'
    records=json.loads((p.OUT/'rollback/transaction.json').read_text())
    installed=json.loads((p.OUT/'installed.json').read_text())
    engine=p.m.REPO/'out/priority_pool'
    eng=json.loads((engine/'installed.json').read_text())
    targets={}
    for name in (p.TEMPLATE,p.LIVE):
        record=records[name];raw=Path(record['source']).read_bytes()
        assert sha(raw)==record['sha256']
        assert sha((p.m.GAME/name).read_bytes())==installed['hashes'][name],name+' changed since install'
        targets[name]=raw
    raw=(engine/'Common.before.dll').read_bytes()
    assert sha(raw)==eng['before']
    assert sha((p.m.GAME/'bin/Common.dll').read_bytes())==eng['after']
    targets['bin/Common.dll']=raw
    live=p.m.old.data_folder(p.m.GAME,p.m.GAME)
    for name,raw in targets.items():
        if name.startswith('DATA/'):live.sync_data_file(name[5:],raw)
        else:(p.m.GAME/name).write_bytes(raw)
        assert sha((p.m.GAME/name).read_bytes())==sha(raw)
    # Audit the effective template after the targeted rollback. Unused assets
    # stay registered; no unrelated appended definitions or backups are deleted.
    installed['hashes'][p.TEMPLATE]=sha(targets[p.TEMPLATE])
    installed['hashes'][p.LIVE]=sha(targets[p.LIVE])
    installed['deactivated']=True
    (p.OUT/'installed.json').write_text(json.dumps(installed,indent=2))
    baseline=p.m.REPO/'out/pythonlancer_preservation/baseline.json'
    data=json.loads(baseline.read_text())
    for name,raw in targets.items():
        if name in data:data[name]=sha(raw)
    baseline.write_text(json.dumps(data,indent=2))
    (engine/'restored.json').write_text(json.dumps({name:sha(raw) for name,raw in targets.items()},indent=2))
    print('Restored prior Common.dll, original Tau4 station and its template; br_wrw optimized template preserved. No new backups or Pythonlancer generation.')
if __name__=='__main__':main()
