"""Install only the two approved epaulette DFM files as a verified transaction."""
import argparse,datetime,gzip,json,os,shutil,subprocess
from pathlib import Path
import epaulettes as e


def safe_path(path,root):
    path=Path(path).absolute();root=Path(root).absolute()
    assert path!=root and path.is_relative_to(root) and path.resolve().is_relative_to(root.resolve())
    for p in (path,*path.parents):
        if p.exists():assert not (os.lstat(p).st_file_attributes & 0x400),'Reparse point: '+str(p)
        if p==root:break
    return path.resolve()


def load(path):return json.loads(path.read_text(encoding='utf8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    live=e.c.DataFolder(root=e.c.GAME);stage=e.c.DataFolder(root=e.OUT/'stage')
    entries=[];private_names=set()
    for name in e.TARGETS:
        folder=e.OUT/name;native=load(folder/'native_validation.json');pins=load(folder/'source.json')
        preview=load(folder/'preview_validation.json');visual=load(folder/'visual_review.json');surface=load(folder/'surface_validation.json')
        culling=load(folder/'culling_validation.json');report=load(folder/'report.json')
        relative=f'CHARACTERS/BODIES/{name}.dfm';expected=native['dfm_sha256']
        target=safe_path(e.c.GAME/'DATA'/relative,e.c.GAME);source=safe_path(e.OUT/'stage/DATA'/relative,e.OUT)
        assert relative==native['relative'] and target==live.data_path(relative)==Path(pins['source']).resolve()
        assert source==stage.data_path(relative)==Path(native['dfm']).resolve() and target!=source
        assert expected==surface['dfm_sha256']==visual['dfm_sha256']
        assert native['geometry_sha256']==preview['geometry_sha256']==visual['geometry_sha256']==surface['geometry_sha256']==culling['geometry_sha256']
        assert native['all_passed'] and surface['all_passed'] and visual['review_ready']
        assert native['lower_lods_and_marker_unchanged'] and native['materials_textures_rig_unchanged']
        assert preview['reopened'] and preview['original_hidden_in_viewport_and_render'] and culling['actual_backface_transparency']
        assert e.c.digest((folder/'epaulettes.blend').read_bytes())==preview['blend_sha256']==visual['blend_sha256']
        for filename,digest in visual['reviewed_images'].items():
            assert e.c.digest(safe_path(folder/filename,folder).read_bytes())==digest,filename
        before=target.read_bytes();current=e.c.digest(before)
        if current==expected and not source.exists():
            installed=load(folder/'installed.json');assert installed['verified'] and installed['sha256']==expected
            print('ALREADY_INSTALLED_AND_VERIFIED',name,flush=True);continue
        assert current==native['source_sha256']==pins['source_sha256'],'Live model changed since review: '+name
        payload=source.read_bytes();assert e.c.digest(payload)==expected
        h,roots=e.c.read_tree(payload);root=roots[0];old=e.c.read_tree(before)[1][0]
        for level in e.c.child(root,'MultiLevel').children:
            if level.name!='Mesh0':assert e.c.write_tree(h,[level])==e.c.write_tree(h,[e.c.child(e.c.child(old,'MultiLevel'),level.name)])
        mesh=e.c.mesh_of(root);assert e.c.digest(e.c.write_tree(h,[mesh]))==native['geometry_sha256']
        triangles=sum(len(e.c.triangles(g)) for g in e.c.child(mesh,'Face_groups').children if g.children)
        assert triangles==native['triangles']==report['triangles_after']<=report['triangle_limit']
        for key in ('Material library','Texture library','Skeleton'):
            assert e.c.write_tree(h,[e.c.child(root,key)])==e.c.write_tree(h,[e.c.child(old,key)])
        names=set(native['private_resource_mapping'].values());assert not names.intersection(private_names);private_names.update(names)
        patch=safe_path(folder/'mesh0.utf.gz',e.OUT)
        assert e.c.digest(gzip.decompress(patch.read_bytes()))==native['geometry_sha256']
        entries.append(dict(name=name,folder=folder,relative=relative,target=target,source=source,patch=patch,
                            payload=payload,before=before,expected=expected,geometry_sha256=native['geometry_sha256'],triangles=triangles))
        print('VERIFIED',name,triangles,'triangles',expected,flush=True)
    if not args.apply or not entries:return
    tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in tasks for name in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close the game before installation'
    assert shutil.disk_usage(e.c.GAME).free>2*sum(len(r['payload']) for r in entries),'Insufficient disk space'
    backup=e.c.DataFolder(root=e.OUT/'installation_transaction')
    for r in entries:
        path=safe_path(e.OUT/'installation_transaction/DATA'/r['relative'],e.OUT)
        assert not path.exists(),'Unfinished transaction requires review'
    for r in entries:
        backup.sync_data_file(r['relative'],r['before'])
        assert backup.data_path(r['relative']).read_bytes()==r['before']
    written=[]
    try:
        for r in entries:
            safe_path(r['target'],e.c.GAME)
            assert r['target'].read_bytes()==r['before'],'Destination changed during transaction'
            written.append(r);live.sync_data_file(r['relative'],r['payload'])
        for r in entries:assert e.c.digest(r['target'].read_bytes())==r['expected']
    except BaseException:
        for r in reversed(written):
            live.sync_data_file(r['relative'],r['before']);assert r['target'].read_bytes()==r['before']
        for r in entries:
            safe_path(backup.data_path(r['relative']),e.OUT);backup.remove_data_file(r['relative'])
        raise
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();records=[]
    for r in entries:
        receipt=dict(name=r['name'],target=str(r['target']),sha256=r['expected'],previous_sha256=e.c.digest(r['before']),
                     triangles=r['triangles'],installed_at=stamp,verified=True,game_launched=False,
                     removed_package_copy=False,removed_transaction_backup=False,removed_compiled_patch=False)
        e.dump(r['folder']/'installed.json',receipt)
        assert e.c.digest(r['target'].read_bytes())==e.c.digest(r['source'].read_bytes())==r['expected']
        safe_path(r['source'],e.OUT);stage.remove_data_file(r['relative'])
        assert backup.data_path(r['relative']).read_bytes()==r['before']
        safe_path(backup.data_path(r['relative']),e.OUT);backup.remove_data_file(r['relative'])
        assert e.c.digest(gzip.decompress(r['patch'].read_bytes()))==r['geometry_sha256']
        safe_path(r['patch'],e.OUT).unlink()
        receipt.update(removed_package_copy=not r['source'].exists(),removed_transaction_backup=not backup.data_path(r['relative']).exists(),
                       removed_compiled_patch=not r['patch'].exists())
        e.dump(r['folder']/'installed.json',receipt);records.append(receipt)
        print('INSTALLED_AND_VERIFIED',r['name'],flush=True)
    e.dump(e.OUT/'installed.json',dict(installed_at=stamp,verified=True,game_launched=False,files=records))


if __name__=='__main__':main()
