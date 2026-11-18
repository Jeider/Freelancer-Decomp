"""Install the three approved depot CMPs as one verified DATA transaction."""
import argparse,datetime,json,subprocess
from pathlib import Path
from depot_family_audit import paths,REGIONS,FAMILY
from native_common import DataFolder,GAME,get_parts,read_tree,sha,dump


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    game=DataFolder(root=GAME);entries=[];resources=set()
    for region in REGIONS:
        out,live,original,relative=paths(region);build=out/'modeled'
        native=json.loads((build/'native_validation.json').read_text())
        preview=json.loads((build/'preview_validation.json').read_text())
        package=DataFolder(root=build/'package');source=package.data_path(relative);target=game.data_path(relative)
        assert target==live.resolve() and source==Path(native['cmp']).resolve()
        assert source.is_relative_to(FAMILY.resolve()) and source!=target
        payload=source.read_bytes();before=target.read_bytes();expected=native['exported_sha256']
        assert sha(payload)==expected==preview['cmp_sha256']
        assert sha(before)==native['installed_source_sha256'],'Installed asset changed since review: '+region
        assert sha(original.read_bytes())==native['original_fl_nd_sha256']
        assert sha((build/f'{region}_depot_deck_relief.blend').read_bytes())==preview['blend_sha256']
        assert preview['reopened'] and preview['originals_hidden_in_viewport_and_render'] and preview['textures_packed']
        for name in ('surface_validation','door_validation','visual_review'):
            check=json.loads((build/(name+'.json')).read_text())
            assert check['all_passed'] and check['cmp_sha256']==expected,(region,name)
            if name=='visual_review':
                for filename,digest in check['reviewed_images'].items():
                    image=(build/filename).resolve()
                    assert image.is_relative_to(build.resolve()) and sha(image.read_bytes())==digest
        names=set(native['private_resource_mapping'].values());assert not resources.intersection(names);resources.update(names)
        assert native['all_native_material_texture_blobs_preserved'] and native['cranes_and_props_unchanged'] and native['native_joints_unchanged']
        parts=get_parts(read_tree(payload)[1][0]);assert sum(len(g['corners']) for p in parts for g in p['groups'])==native['result_triangles']
        entries.append(dict(region=region,relative=relative,target=target,source=source,package=package,
            payload=payload,before=before,expected=expected,build=build,triangles=native['result_triangles']))
        print('VERIFIED',region,target,native['result_triangles'],'triangles')
    if not args.apply:return
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in tasks for name in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close the game before installing'
    written=[]
    try:
        for e in entries:
            # Recheck each destination at the actual write boundary.
            assert e['target'].read_bytes()==e['before'],'Destination changed during transaction'
            written.append(e);game.sync_data_file(e['relative'],e['payload'])
        for e in entries:assert sha(e['target'].read_bytes())==e['expected']
    except BaseException:
        for e in reversed(written):
            game.sync_data_file(e['relative'],e['before']);assert e['target'].read_bytes()==e['before']
        raise
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for e in entries:
        record=dict(target=str(e['target']),sha256=e['expected'],previous_sha256=sha(e['before']),triangles=e['triangles'],
            verified=True,installed_at=stamp,game_launched=False,removed_package_copy=False)
        dump(e['build']/'installed.json',record)
        assert sha(e['source'].read_bytes())==e['expected']==sha(e['target'].read_bytes())
        e['package'].remove_data_file(e['relative'])
        record['removed_package_copy']=not e['source'].exists();dump(e['build']/'installed.json',record)
        print('INSTALLED_AND_VERIFIED',e['region'])


if __name__=='__main__':main()
