"""Sequential, validated content-only batch; never invokes Pythonlancer generation."""
import argparse,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/station_batch'

def run(config,script,*args):
    env=dict(os.environ,STATION_BATCH_CONFIG=json.dumps(config))
    folder=OUT/config['task'];folder.mkdir(parents=True,exist_ok=True)
    with (folder/(script+'.log')).open('wb') as log:
        result=subprocess.run([sys.executable,'-B','tools/'+script+'.py',*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(script+': '+(folder/(script+'.log')).read_text(errors='replace')[-2200:])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--only',nargs='*');ap.add_argument('--cleanup',action='store_true');ap.add_argument('--install-prepared',action='store_true');args=ap.parse_args()
    if args.cleanup:cleanup();return
    configs=json.loads((OUT/'inventory.json').read_text())['candidates']
    results=[]
    for config in configs:
        if args.only and config['class'] not in args.only:continue
        folder=OUT/config['task']
        if (folder/'installed.json').exists() and not config.get('rebuild'):
            results.append(dict(task=config['task'],status='installed'));continue
        print('START',config['class'],flush=True)
        try:
            if args.install_prepared:
                assert args.apply
                config=json.loads((folder/'manifest.json').read_text())['config']
                run(config,'install_station_batch_model','--apply')
                update_baseline(json.loads((folder/'manifest.json').read_text()))
                print('Installed validated prepared payload',config['class'],flush=True)
                continue
            # Rebuild against the current content after each earlier transaction.
            for attempt in range(8):
                precision=folder/'precision_retained.json';precision.unlink(missing_ok=True)
                try:
                    run(config,'station_batch_model');break
                except RuntimeError:
                    if not precision.exists() or attempt==7:raise
                    config['retain']=sorted(set(config.get('retain',[]))|set(json.loads(precision.read_text())))
                    print('Preserving precision-sensitive objects:',len(config['retain']),flush=True)
            run(config,'check_station_batch_native')
            run(config,'check_station_batch_physics')
            if config.get('docks'):run(config,'check_station_docks')
            if config.get('panel_rotors'):run(config,'check_station_panel_rotors')
            run(config,'install_station_batch_model',*(['--apply'] if args.apply else []))
            manifest=json.loads((folder/'manifest.json').read_text())
            result=dict(task=config['task'],status='installed' if args.apply else 'prepared',before=manifest['before'],after=manifest['after'])
            results.append(result);print(json.dumps(result),flush=True)
            if args.apply:update_baseline(manifest)
        except (RuntimeError,AssertionError) as exc:
            results.append(dict(task=config['task'],status='failed',error=str(exc)))
            print('FAILED',config['class'],str(exc),flush=True)
        (OUT/'results.json').write_text(json.dumps(results,indent=2))

def update_baseline(manifest):
    from valensia_mega import GAME
    import hashlib
    path=ROOT/'out/pythonlancer_preservation/baseline.json'
    baseline=json.loads(path.read_text())
    for name,sha in manifest['payload'].items():
        assert hashlib.sha256((GAME/name).read_bytes()).hexdigest()==sha
        if name in baseline:assert baseline[name]==manifest['sources'][name],name+' prior preservation mismatch'
        baseline[name]=sha
    path.write_text(json.dumps(baseline,indent=2))

def cleanup():
    import valensia_mega as m
    root=OUT.resolve();assert root.is_relative_to(ROOT.resolve())
    removed=0;size=0
    for folder in OUT.glob('batch_*'):
        stage=folder/'stage'
        data=m.old.data_folder(m.GAME,stage)
        for path in stage.rglob('*') if stage.exists() else []:
            if not path.is_file():continue
            assert path.resolve().is_relative_to(root)
            size+=path.stat().st_size;removed+=1
            relative=path.relative_to(stage).as_posix()
            if relative.startswith('DATA/'):data.remove_data_file(relative[5:])
            else:path.unlink()
        for name in ('native','physics_check','physics_original','physics_candidate','dock_animation','panel_animation'):
            for path in (folder/name).glob('*'):
                if not path.is_file() or path.suffix.lower() not in ('.obj','.exe','.pdb','.ilk'):continue
                assert path.resolve().is_relative_to(root)
                size+=path.stat().st_size;removed+=1;path.unlink()
    (OUT/'cleanup.json').write_text(json.dumps(dict(files=removed,bytes=size),indent=2))
    print('Removed temporary files:',removed,';',round(size/1048576,2),'MiB. Rollback, reports and Originals preserved.')

if __name__=='__main__':main()
