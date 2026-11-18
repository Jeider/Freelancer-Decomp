"""Apply only verified Mesh0 patches; textures stay in their existing DFM files."""
import argparse
from datetime import datetime
import json
import subprocess
import sys
from pathlib import Path
import check_contours
from check_contours import reconstruct
from contours import OUT, OLD, GAME, digest, excluded_name, load_policy, DataFolder


def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--package',choices=['contours_2k','bracer_starts','hero_bodies'],default='contours_2k');args=ap.parse_args()
    OUT=OUT.parent/args.package;check_contours.OUT=OUT
    inventory=json.loads((OLD/'inventory.json').read_text())
    if args.package=='bracer_starts':
        from bracer_starts import TARGETS
        names=sorted(TARGETS)
    elif args.package=='hero_bodies':
        from hero_bodies import TARGETS
        names=sorted(TARGETS)
    else:names=sorted(r['name'] for r in inventory if not excluded_name(r['name']))
    validation=json.loads((OUT/'validation.json').read_text())
    assert not validation['errors'] and {r['name'] for r in validation['results']}==set(names)
    blends=json.loads((OUT/'blend_validation.json').read_text())
    assert not blends['errors'] and set(blends['valid'])==set(names)
    checked={r['name']:r for r in validation['results']}
    pending=[]
    for name in names:
        folder=OUT/name;report=json.loads((folder/'report.json').read_text())
        preview=json.loads((folder/'render_source.json').read_text())
        assert preview['sha256']==report['output_sha256']==checked[name]['output_sha256']
        blend_name='hero_body.blend' if args.package=='hero_bodies' else 'contours_2k.blend'
        assert set(preview['views'])>={'front','back'} and (folder/blend_name).exists()
        if args.package=='bracer_starts':
            assert report['triangles_after']<=report['triangles_before']+100<=2100
            assert 'bracer_start' in preview['views']
        elif args.package=='hero_bodies':
            assert report['triangles_after']<=report['triangles_before']+2000==report['triangle_limit']
            assert ('upper_edges' if name=='li_hatcher_body' else 'cuff') in preview['views']
        else:assert report['triangles_after']<=load_policy()['max_mesh0_triangles']
        rel='CHARACTERS/BODIES/'+name+'.dfm';live=(GAME/'DATA'/rel).read_bytes()
        assert digest(live) in (report['previous_sha256'],report['output_sha256'])
        desired=reconstruct(name,live)
        assert digest(desired)==report['output_sha256']
        if digest(live)!=report['output_sha256']:
            assert digest(reconstruct(name,desired,previous=True))==report['previous_sha256']
            pending.append((name,rel,report))
    print('Verified patches:',len(names),'pending installation:',len(pending),flush=True)
    if not args.apply:return
    if not pending:
        print('All contour models already installed; existing receipt preserved.')
        return
    # Do not replace a body while the game can be loading its textures/geometry.
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    if any(b'"'+name+b'"' in tasks for name in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')):
        raise SystemExit('Game/server is running. Close it before applying model patches; no files changed.')
    live=DataFolder(root=GAME)
    protected={r['name']:digest((GAME/'DATA/CHARACTERS/BODIES'/(r['name']+'.dfm')).read_bytes())
               for r in inventory if r['name'] not in names}
    journal=OUT/('apply_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
    entries=[];completed=[]
    try:
        for name,rel,report in pending:
            before=live.data_path(rel).read_bytes()
            assert digest(before)==report['previous_sha256'],'Changed since validation: '+name
            desired=reconstruct(name,before)
            assert digest(desired)==report['output_sha256']
            # Compact reverse patches have already been checked against the exact live hash.
            assert digest(reconstruct(name,desired,previous=True))==digest(before)
            entries.append(dict(name=name,relative_path=rel,before_sha256=digest(before),after_sha256=digest(desired),
                                reverse_patch=str(OUT/name/'previous_mesh0.utf.gz')))
            journal.write_text(json.dumps(dict(status='applying',files=entries),indent=2))
            try:
                live.sync_data_file(rel,desired)
                assert live.data_path(rel).read_bytes()==desired
            except BaseException:
                live.sync_data_file(rel,before)
                assert live.data_path(rel).read_bytes()==before
                raise
            completed.append((name,rel,report))
    except BaseException:
        failures=[]
        for name,rel,report in reversed(completed):
            try:
                now=live.data_path(rel).read_bytes();assert digest(now)==report['output_sha256']
                previous=reconstruct(name,now,previous=True);assert digest(previous)==report['previous_sha256']
                live.sync_data_file(rel,previous);assert digest(live.data_path(rel).read_bytes())==report['previous_sha256']
            except Exception as error:failures.append(dict(name=name,error=repr(error)))
        journal.write_text(json.dumps(dict(status='rolled_back',files=entries,failures=failures),indent=2))
        raise
    for name,wanted in protected.items():
        assert digest((GAME/'DATA/CHARACTERS/BODIES'/(name+'.dfm')).read_bytes())==wanted
    receipt=dict(installed=len(completed),validated_models=len(names),max_mesh0_triangles=max(checked[n]['triangles'] for n in names),
                 protected_models=protected,only_mesh0_changed=True,game_launched=False,
                 game_animation_validated=False,files=entries)
    journal.write_text(json.dumps(dict(status='complete',**receipt),indent=2))
    (OUT/'installed.json').write_text(json.dumps(receipt,indent=2))
    # Remove this transaction's compiled and reverse geometry patches only
    # after installed hashes and every protected model have been verified.
    # Editable JSON meshes, Blender assets and all source tools remain.
    if args.package in ('bracer_starts','hero_bodies'):
        root=OUT.resolve();deleted=[]
        for name in names:
            for filename in ('mesh0.utf.gz','previous_mesh0.utf.gz'):
                path=OUT/name/filename
                assert not path.is_symlink() and not path.parent.is_symlink()
                assert not path.parent.is_junction() and not OUT.is_junction()
                assert path.resolve().is_relative_to(root)
                if path.exists():path.unlink();deleted.append(str(path.relative_to(OUT)))
        (OUT/'cleanup.json').write_text(json.dumps(dict(verified_installation=True,removed_compiled_patches=deleted),indent=2))
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('files','protected_models')}|{'protected_model_count':len(protected)},indent=2))


if __name__=='__main__':main()
