"""Install the approved Forbes counter CMP through the central DATA API."""
import argparse
import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path

from forbes_counter_audit import OUT, SOURCE, RETAIL, RELATIVE
from native_common import DataFolder, GAME, dump, get_parts, read_tree, sha


def checked_path(path, root):
    path=Path(path).absolute();root=Path(root).absolute()
    assert path.is_relative_to(root) and path.resolve().is_relative_to(root.resolve())
    for p in (path,*path.parents):
        if p.exists():
            assert not (os.lstat(p).st_file_attributes & 0x400),'Reparse point: '+str(p)
        if p==root:break
    return path.resolve()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    build=OUT/'modeled'
    native=json.loads((build/'native_validation.json').read_text())
    preview=json.loads((build/'preview_validation.json').read_text())
    surface=json.loads((build/'surface_validation.json').read_text())
    visual=json.loads((build/'visual_review.json').read_text())
    pins=json.loads((OUT/'sources.json').read_text())
    game=DataFolder(root=GAME);package=DataFolder(root=build/'package')
    target=checked_path(GAME/'DATA'/RELATIVE,GAME)
    source=checked_path(build/'package/DATA'/RELATIVE,OUT)
    assert target==game.data_path(RELATIVE)==SOURCE.resolve()
    assert source==package.data_path(RELATIVE)==Path(native['cmp']).resolve() and source!=target
    expected=native['exported_sha256'];before=target.read_bytes()
    assert expected==preview['cmp_sha256']==surface['cmp_sha256']==visual['cmp_sha256']
    assert surface['all_passed'] and preview['reopened'] and preview['textures_packed']
    assert preview['originals_hidden_in_viewport_and_render']
    assert sha((build/'forbes_bar_counter.blend').read_bytes())==preview['blend_sha256']==visual['blend_sha256']
    for filename,digest in visual['image_sha256'].items():
        assert sha(checked_path(build/filename,build).read_bytes())==digest,filename
    assert sha(RETAIL.read_bytes())==pins['original_sha256']
    assert native['all_native_material_texture_blobs_preserved'] and native['native_joints_unchanged']
    assert native['retained_room_geometry_unchanged']
    for record in pins['scripts'].values():
        assert sha(Path(record['path']).read_bytes())==record['sha256'],'Room script changed since review'
    if not source.exists():
        installed=json.loads((build/'installed.json').read_text())
        assert sha(before)==expected==installed['sha256'] and installed['verified']
        print('ALREADY_INSTALLED_AND_VERIFIED',target);return
    payload=source.read_bytes();assert sha(payload)==expected
    assert sha(before) in (pins['installed_sha256'],expected),'Live model changed since review'
    parts=get_parts(read_tree(payload)[1][0])
    triangles=sum(len(g['corners']) for p in parts for g in p['groups'])
    assert triangles==native['result_triangles']==preview['visible_triangles']
    print('VERIFIED',target,triangles,'triangles',expected,flush=True)
    if not args.apply:return
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in tasks for name in
                   (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close the game before installation'
    assert shutil.disk_usage(GAME).free>len(payload)*2,'Insufficient disk space'
    backup=DataFolder(root=build/'installation_transaction')
    backup_file=checked_path(build/'installation_transaction/DATA'/RELATIVE,OUT)
    assert not backup_file.exists(),'Unfinished installation transaction requires inspection'
    backup.sync_data_file(RELATIVE,before)
    assert backup_file.read_bytes()==before
    touched=False
    try:
        assert target.read_bytes()==before,'Live model changed during installation'
        checked_path(GAME/'DATA'/RELATIVE,GAME)
        touched=True;game.sync_data_file(RELATIVE,payload)
        assert sha(target.read_bytes())==expected
    except BaseException:
        if touched:
            game.sync_data_file(RELATIVE,before);assert target.read_bytes()==before
        checked_path(backup_file,OUT);backup.remove_data_file(RELATIVE)
        raise
    record=dict(target=str(target),sha256=expected,previous_sha256=sha(before),triangles=triangles,
                installed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verified=True,
                game_launched=False,removed_package_copy=False,removed_transaction_backup=False)
    dump(build/'installed.json',record)
    assert sha(target.read_bytes())==sha(source.read_bytes())==expected
    checked_path(source,OUT);package.remove_data_file(RELATIVE)
    assert backup_file.read_bytes()==before
    checked_path(backup_file,OUT);backup.remove_data_file(RELATIVE)
    record.update(removed_package_copy=not source.exists(),removed_transaction_backup=not backup_file.exists())
    dump(build/'installed.json',record)
    print('INSTALLED_AND_VERIFIED',target,flush=True)


if __name__=='__main__':main()
