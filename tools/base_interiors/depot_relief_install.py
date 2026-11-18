"""Install only the validated RH depot deck; DATA writes use DataFolder."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path

from depot_surface_audit import OUT
from native_common import DataFolder, GAME, ROOT, get_parts, read_tree, sha

BUILD=OUT/'modeled'
RELATIVE='BASES/RHEINLAND/rh_depot_deck.cmp'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    native=json.loads((BUILD/'native_validation.json').read_text())
    preview=json.loads((BUILD/'preview_validation.json').read_text())
    package=DataFolder(root=BUILD/'package')
    game=DataFolder(root=GAME)
    source=package.data_path(RELATIVE)
    target=game.data_path(RELATIVE)
    assert source==Path(native['cmp']).resolve()
    assert source.is_relative_to((ROOT/'out/base_interiors').resolve())
    assert target==(GAME/'DATA'/RELATIVE).resolve() and source!=target
    payload=source.read_bytes();before=target.read_bytes()
    expected=native['exported_sha256']
    assert sha(payload)==expected==preview['cmp_sha256']
    assert sha(before)==native['installed_source_sha256'],'Installed source changed since review'
    assert sha((BUILD/'rh_depot_deck_relief.blend').read_bytes())==preview['blend_sha256']
    assert preview['reopened'] and preview['originals_hidden_in_viewport_and_render']
    for name in ('surface_validation','door_validation'):
        check=json.loads((BUILD/(name+'.json')).read_text())
        assert check['all_passed'] and check['cmp_sha256']==expected
    parts=get_parts(read_tree(payload)[1][0])
    assert sum(len(g['corners']) for p in parts for g in p['groups'])==native['result_triangles']
    print('Verified payload:',target,native['result_triangles'],'triangles')
    if not args.apply:return
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+n+b'"' in tasks for n in
        (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close the game before installation'
    # Keep the original in memory only for the installation transaction.
    try:
        game.sync_data_file(RELATIVE,payload)
        assert sha(target.read_bytes())==expected,'Installed file verification failed'
    except BaseException:
        game.sync_data_file(RELATIVE,before)
        assert target.read_bytes()==before,'Rollback verification failed'
        raise
    report=dict(target=str(target),sha256=expected,previous_sha256=sha(before),
        triangles=native['result_triangles'],verified=True,game_launched=False,
        installed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        removed_package_copy=False)
    record=BUILD/'installed.json'
    record.write_text(json.dumps(report,indent=2)+'\n')
    # Remove precisely this installed payload through the same DATA API.
    assert sha(source.read_bytes())==expected==sha(target.read_bytes())
    package.remove_data_file(RELATIVE)
    report['removed_package_copy']=not source.exists()
    record.write_text(json.dumps(report,indent=2)+'\n')
    print('INSTALLED_AND_VERIFIED',target)


if __name__=='__main__':main()
