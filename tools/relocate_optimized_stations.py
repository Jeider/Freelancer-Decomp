"""Byte-preserving station relocation through DataFolder; never runs Pythonlancer."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from optimized_station_paths import FOLDERS
ROOT=Path(__file__).resolve().parents[1];GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/optimized_stations'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def folder(root):
    # Load the project's sole DATA writer, without importing its generator.
    import importlib.util
    spec=importlib.util.spec_from_file_location('station_data_folder',GAME/'Assets/Pythonlancer/tools/data_folder.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.DataFolder(root=root)
def rewrite(raw,moves):
    dirs={old.split('/')[2].lower() for old in moves if old.split('/')[2]!='MISC'}
    def replace(match):
        sep=match[1];name=match[2]
        return b'SOLAR'+sep+b'OPTIMIZED'+sep+name+sep if name.decode().lower() in dirs else match[0]
    raw=re.sub(rb'solar([\\/]+)([a-z0-9_]+)[\\/]+',replace,raw,flags=re.I)
    raw=re.sub(rb'solar([\\/]+)misc[\\/]+(trading_station_part\.(?:cmp|sur|3db))',
               lambda m:b'SOLAR'+m[1]+b'OPTIMIZED'+m[1]+b'ku_tgk_01'+m[1]+m[2],raw,flags=re.I)
    return raw
def prepare():
    OUT.mkdir(parents=True,exist_ok=True);moves={};hashes={}
    solar=GAME/'DATA/SOLAR'
    dirs=[p for p in solar.iterdir() if p.is_dir() and (p.name in FOLDERS or p.name.startswith('batch_'))]
    files=[p for d in dirs for p in d.rglob('*') if p.is_file()]
    # Grok's baked reusable part used by the sixteen ku_tgk_01 sector objects.
    parts=list((solar/'MISC').glob('trading_station_part.*'))
    assert {p.suffix for p in parts}>={'.cmp','.sur'}
    for p in files+parts:
        old=p.relative_to(GAME).as_posix()
        new=('DATA/SOLAR/OPTIMIZED/ku_tgk_01/'+p.name if p in parts else old.replace('DATA/SOLAR/','DATA/SOLAR/OPTIMIZED/',1))
        assert not (GAME/new).exists(),new
        moves[old]=new;hashes[old]=sha(p.read_bytes())
    # Only textual reference-bearing files; original asset payloads stay byte identical.
    configs={};stage=folder(OUT/'stage')
    candidates=list((GAME/'DATA').rglob('*.ini'))
    for suffix in ('*.py','*.ini','*.json'):
        candidates += [p for p in (GAME/'Assets/Pythonlancer').rglob(suffix)
                       if not any(x in p.parts for x in ('.venv','venv','.git','__pycache__'))]
    candidates += list((GAME/'BUILDS').rglob('*.ini')) if (GAME/'BUILDS').exists() else []
    # Fast prefilter avoids applying every individual filename regexp to unrelated content.
    roots=[('solar/'+p.name+'/').encode() for p in dirs]+[b'solar/misc/trading_station_part.']
    for p in candidates:
        raw=p.read_bytes();normalized=raw.lower().replace(b'\\',b'/')
        if not any(x.lower() in normalized for x in roots):continue
        after=rewrite(raw,moves)
        if after==raw:continue
        name=p.relative_to(GAME).as_posix();configs[name]=dict(before=sha(raw),after=sha(after))
        if name.startswith('DATA/'):stage.sync_data_file(name[5:],after)
        elif '/DATA/' in name:
            prefix,relative=name.split('/DATA/',1);folder(OUT/'stage'/prefix).sync_data_file(relative,after)
        else:
            target=OUT/'stage'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(after)
    api='Assets/Pythonlancer/tools/data_folder.py'
    raw=(GAME/api).read_bytes()
    if b'def remove_empty_data_directory(' not in raw:
        newline=b'\r\n' if b'\r\n' in raw else b'\n'
        method=('    def remove_empty_data_directory(self, relative):\n'
                '        """Remove only an empty directory within DATA; never recursive."""\n'
                '        self.data_path(relative).rmdir()\n\n').replace('\n',newline.decode()).encode()
        after=raw.replace(b'    def sync_ship_parking(',method+b'    def sync_ship_parking(',1)
        assert after!=raw
        configs[api]=dict(before=sha(raw),after=sha(after))
        target=OUT/'stage'/api;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(after)
    assert 'DATA/SOLAR/solararch.ini' in configs
    plan=dict(moves=moves,hashes=hashes,configs=configs,folders=[p.name for p in dirs],bytes=sum(p.stat().st_size for p in files+parts))
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2))
    print(json.dumps(dict(models=len(moves),folders=len(dirs)+1,configs=list(configs),MiB=round(plan['bytes']/1048576,2)),indent=2))
def apply():
    plan=json.loads((OUT/'plan.json').read_text());live=folder(GAME);backup=folder(OUT/'rollback')
    for old,new in plan['moves'].items():
        assert sha((GAME/old).read_bytes())==plan['hashes'][old]
        assert not (GAME/new).exists(),new
    before={n:(GAME/n).read_bytes() for n in plan['configs']}
    for n,c in plan['configs'].items():
        assert sha(before[n])==c['before'];assert sha((OUT/'stage'/n).read_bytes())==c['after']
        if n.startswith('DATA/'):backup.sync_data_file(n[5:],before[n])
        else:
            p=OUT/'rollback'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(before[n])
    def write(n,raw):
        if n.startswith('DATA/'):live.sync_data_file(n[5:],raw)
        elif '/DATA/' in n:
            prefix,relative=n.split('/DATA/',1);folder(GAME/prefix).sync_data_file(relative,raw)
        else:(GAME/n).write_bytes(raw)
    created=[];changed=[];removed=[]
    try:
        for old,new in plan['moves'].items():
            live.sync_data_file(new[5:],(GAME/old).read_bytes());created.append(new)
            assert sha((GAME/new).read_bytes())==plan['hashes'][old]
        for n in before:changed.append(n);write(n,(OUT/'stage'/n).read_bytes())
        for old in plan['moves']:removed.append(old);live.remove_data_file(old[5:])
        plan['locked_empty_directories']=[]
        import time
        for d in plan['folders']:
            for attempt in range(5):
                try:
                    folder(GAME).remove_empty_data_directory('SOLAR/'+d);break
                except PermissionError:
                    if attempt==4:plan['locked_empty_directories'].append(d)
                    else:time.sleep(.2)
    except Exception:
        for old in removed:live.sync_data_file(old[5:],(GAME/plan['moves'][old]).read_bytes())
        for n in changed:write(n,before[n])
        for n in created:live.remove_data_file(n[5:])
        raise
    baseline=ROOT/'out/pythonlancer_preservation/baseline.json'
    if baseline.exists():
        data=json.loads(baseline.read_text())
        for old,new in plan['moves'].items():
            if old in data:data[new]=data.pop(old)
        for n,c in plan['configs'].items():
            if data.get(n)==c['before']:data[n]=c['after']
        baseline.write_text(json.dumps(data,indent=2))
    (OUT/'installed.json').write_text(json.dumps(plan,indent=2))
    verify()
def verify():
    plan=json.loads((OUT/'installed.json').read_text())
    for old,new in plan['moves'].items():
        assert not (GAME/old).exists(),old
        assert sha((GAME/new).read_bytes())==plan['hashes'][old],new
    for n,c in plan['configs'].items():assert sha((GAME/n).read_bytes())==c['after'],n
    print('PASS: all relocated assets byte-identical, old files removed, references verified; Pythonlancer not run.')
def cleanup_empty():
    path=OUT/'installed.json';plan=json.loads(path.read_text());pending=[]
    for name in plan.get('locked_empty_directories',[]):
        try:folder(GAME).remove_empty_data_directory('SOLAR/'+name)
        except FileNotFoundError:pass
        except PermissionError:pending.append(name)
    plan['locked_empty_directories']=pending;path.write_text(json.dumps(plan,indent=2))
    print('Locked empty directories:',pending)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--verify',action='store_true');ap.add_argument('--cleanup-empty',action='store_true');args=ap.parse_args()
    if args.apply:apply()
    elif args.verify:verify()
    elif args.cleanup_empty:cleanup_empty()
    else:prepare()
