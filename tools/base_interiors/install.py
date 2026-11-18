"""Install/restore a staged Bismarck or explicitly selected Rheinland package."""
import argparse,datetime,re,subprocess
from native_common import *
ALLOWED_DATA={'DATA/'+REL}

def safe(root,relative):
    assert relative in ALLOWED_DATA or relative=='DATA_EXTRA/ROOM_MATERIALS/profiles.txt' or re.fullmatch(r'DATA_EXTRA/ROOM_MATERIALS/[0-9a-f]{32}\.dds',relative),relative
    p=(root/relative).resolve();assert p.is_relative_to(root.resolve())
    return p
def digest(root,rel):
    p=safe(root,rel);return sha(p.read_bytes()) if p.exists() else None
def write(root,rel,data):
    if rel.startswith('DATA/'):
        df=DataFolder(root=root)
        if data is None:df.remove_data_file(rel[5:])
        else:df.sync_data_file(rel[5:],data)
    else:
        p=safe(root,rel)
        if data is None:p.unlink(missing_ok=True)
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def clean_verified_stage(records):
    # Remove only this package's exact verified payload, never recursive trees.
    assert STAGE.resolve().is_relative_to((ROOT/'out/base_interiors').resolve())
    assert STAGE.resolve()!=GAME.resolve()
    for r in records:
        assert digest(GAME,r['relative'])==r['prepared']
        assert digest(STAGE,r['relative'])==r['prepared']
    removed=[];errors=[]
    for r in records:
        try:
            write(STAGE,r['relative'],None)
            removed.append(r['relative'])
        except OSError as exc:
            errors.append(dict(relative=r['relative'],error=str(exc)))
    return dict(removed=removed,errors=errors)

def main():
    global OUT,STAGE,ALLOWED_DATA
    ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--apply',action='store_true');mode.add_argument('--restore',type=Path)
    ap.add_argument('--rheinland',action='store_true',help='Rheinland room batch including depot and battleship decks; existing Bismarck bar excluded')
    args=ap.parse_args()
    if args.rheinland:
        from rheinland_audit import MODELS,BATCH
        OUT=BATCH;STAGE=BATCH/'stage';ALLOWED_DATA={f'DATA/BASES/RHEINLAND/{name}.cmp' for name in MODELS}
    source=args.restore.resolve(strict=True) if args.restore else STAGE
    manifest=json.loads(((source/'manifest.json') if args.restore else (OUT/'manifest.json')).read_text(encoding='utf8'))
    assert Path(manifest['game']).resolve()==GAME.resolve()
    records=manifest['files'];assert len({r['relative'] for r in records})==len(records)
    assert {r['relative'] for r in records if r['relative'].startswith('DATA/')}==ALLOWED_DATA
    if not args.restore:
        for rel,hash_ in manifest['dependencies'].items():assert sha((GAME/rel).read_bytes())==hash_,f'Dependency changed: {rel}'
    for r in records:
        rel=r['relative'];assert digest(GAME,rel)==r['prepared' if args.restore else 'original'],f'Live file changed: {rel}'
        if not args.restore or r['original'] is not None:assert digest(source,rel)==r['original' if args.restore else 'prepared'],f'Payload changed: {rel}'
    if not (args.apply or args.restore):
        print(f'Ready: {len(records)} files. Original material/texture blobs and both UV sets verified.');return
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    if any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')):raise SystemExit('Game/server running; installation staged, no files changed.')
    if args.restore:
        for r in records:write(GAME,r['relative'],safe(source,r['relative']).read_bytes() if r['original'] is not None else None)
        for r in records:assert digest(GAME,r['relative'])==r['original']
        dump(OUT/'restored.json',dict(backup=str(source),verified=True,game_launched=False));print('Restored and verified.');return
    backup=OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for r in records:
        if r['original'] is not None:
            write(backup,r['relative'],safe(GAME,r['relative']).read_bytes())
            assert digest(backup,r['relative'])==r['original']
    dump(backup/'manifest.json',manifest)
    try:
        for r in records:write(GAME,r['relative'],safe(STAGE,r['relative']).read_bytes())
        for r in records:assert digest(GAME,r['relative'])==r['prepared']
    except BaseException:
        for r in records:write(GAME,r['relative'],safe(backup,r['relative']).read_bytes() if r['original'] is not None else None)
        raise
    result=dict(backup=str(backup),files=records,verified=True,game_launched=False,
                installed_cmp_sha256=({rel:digest(GAME,rel) for rel in sorted(ALLOWED_DATA)} if args.rheinland else digest(GAME,'DATA/'+REL)))
    dump(OUT/'installed.json',result)
    result['staging_cleanup']=clean_verified_stage(records)
    dump(OUT/'installed.json',result)
    print(json.dumps(dict(installed=len(records),backup=str(backup),verified=True,
                         staging_cleanup=result['staging_cleanup'],game_launched=False),indent=2))

if __name__=='__main__':main()
