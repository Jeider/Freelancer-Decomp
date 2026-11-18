"""Install the GPU-verified UV selection fix; never launch or stop the game."""
import argparse,datetime,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_interiors/rh_biz_01_base/shipdealer/uv_fix'
SOURCE=ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl'
TARGET=Path('D:/Games/FL_MOD/DATA_EXTRA/SHADERS/room_material.hlsl')
MODEL=Path('D:/Games/FL_MOD/DATA/BASES/RHEINLAND/rh_bizmark_shipdealer.cmp')
digest=lambda value:hashlib.sha256(value).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    validation=json.loads((OUT/'validation.json').read_text())
    before=TARGET.read_bytes();payload=SOURCE.read_bytes();model_hash=digest(MODEL.read_bytes())
    assert validation['passed'] and digest(payload)==validation['fixed_sha256'],'GPU validation is stale'
    assert digest(before) in (validation['before_sha256'],validation['fixed_sha256']),'Installed shader changed since validation'
    assert Path(validation['game_target']).resolve()==TARGET.resolve()
    print('Verified single-file shader update:',TARGET)
    if not args.apply:return
    try:
        TARGET.write_bytes(payload)
        assert TARGET.read_bytes()==payload
    except BaseException:
        TARGET.write_bytes(before)
        assert TARGET.read_bytes()==before
        raise
    assert digest(MODEL.read_bytes())==model_hash
    report=dict(installed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        target=str(TARGET),previous_sha256=digest(before),installed_sha256=digest(payload),
        verified=True,game_launched=False,model_unchanged=True,model_sha256=model_hash,
        restart_required=True,cache_policy='Runtime shader cache is keyed by expanded source; new source gets a new cache key.',
        removed_test_binaries=[])
    (OUT/'installed.json').write_text(json.dumps(report,indent=2)+'\n')
    # Exact task-owned test outputs only. Keep sources, the baseline and reports.
    for path in (OUT/'check.exe',OUT/'check.obj'):
        assert path.resolve().is_relative_to((ROOT/'out/base_interiors').resolve())
        for parent in (path,*path.parents):
            if parent==ROOT:break
            assert not parent.is_symlink() and not parent.is_junction()
        if path.exists():path.unlink();report['removed_test_binaries'].append(path.name)
    (OUT/'installed.json').write_text(json.dumps(report,indent=2)+'\n')
    print('INSTALLED_AND_VERIFIED. Restart the game to load the fixed shader.')


if __name__=='__main__':main()
