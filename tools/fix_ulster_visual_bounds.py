"""Preserve phantom collision leaves but give rendering the complete visual radius."""
import argparse,json,struct
import numpy as np
import ulster_shortsplit as p
m=p.m
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest_path=p.OUT/'manifest.json';installed_path=p.OUT/'installed.json'
    installed=json.loads(installed_path.read_text());manifest=json.loads(manifest_path.read_text())
    record=p.OUT/'visual_bounds.json'
    if not args.apply:
        assert not record.exists(),'Already prepared; reuse staged patch'
        folder=m.old.data_folder(m.GAME,p.OUT/'stage');changes={}
        # Rehydrate only DATA payload for native validation; all writes use DataFolder.
        for name,digest in installed['hashes'].items():
            if not name.startswith('DATA/'):continue
            raw=(m.GAME/name).read_bytes();assert m.old.sha256(raw).hexdigest()==digest,name
            folder.sync_data_file(name[5:],raw)
        for comp in manifest['components']:
            name=f"DATA/SOLAR/OPTIMIZED/ulster_shortsplit/{comp['name']}.sur"
            cmp=m.GAME/name.replace('.sur','.cmp')
            root=m.utf.read_tree(cmp.read_bytes())[1][0]
            pts=np.concatenate([np.array([struct.unpack_from('<3f',v) for v in m.mesh.read_mesh(m.b.one(node,'VMeshData').blob)[1]]) for node in m.b.one(root,'VMeshLibrary').children])
            lo=pts.min(0);hi=pts.max(0);radius=float(np.linalg.norm(pts,axis=1).max())*1.02
            before=(m.GAME/name).read_bytes();raw=bytearray(before)
            # Root-only SUR: vers(8), part/count(8), !fxd(4), exts(4+24), surf(4+4).
            assert raw[16:20]==b'!fxd' and raw[20:24]==b'exts' and raw[48:52]==b'surf'
            struct.pack_into('<6f',raw,24,*lo,*hi)
            struct.pack_into('<f',raw,56+24,radius)
            old_blob=dict(dict(m.old.parts(before))[m.utf.crc('Root')])[b'surf']
            new_blob=dict(dict(m.old.parts(bytes(raw)))[m.utf.crc('Root')])[b'surf']
            assert old_blob[:24]==new_blob[:24] and old_blob[28:]==new_blob[28:],'collision geometry changed'
            folder.sync_data_file(name[5:],bytes(raw));digest=m.old.sha256(raw).hexdigest()
            changes[name]=dict(before=m.old.sha256(before).hexdigest(),after=digest,radius=radius)
            manifest['payload'][name]=digest
            print(comp['name'],'visual radius',round(radius,2))
        record.write_text(json.dumps(changes,indent=2));manifest_path.write_text(json.dumps(manifest,indent=2))
        return
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    for stamp in ('native_check.ok','physics_check.ok'):assert (p.OUT/stamp).read_text()==digest
    changes=json.loads(record.read_text());live=m.old.data_folder(m.GAME,m.GAME)
    backup=m.old.data_folder(m.GAME,p.OUT/'visual_bounds_rollback')
    for name,c in changes.items():
        before=(m.GAME/name).read_bytes();after=(p.OUT/'stage'/name).read_bytes()
        assert m.old.sha256(before).hexdigest()==c['before'] and m.old.sha256(after).hexdigest()==c['after']
        backup.sync_data_file(name[5:],before);live.sync_data_file(name[5:],after)
        assert (m.GAME/name).read_bytes()==after
        installed['hashes'][name]=c['after']
    installed_path.write_text(json.dumps(installed,indent=2))
    baseline=m.REPO/'out/pythonlancer_preservation/baseline.json';data=json.loads(baseline.read_text())
    for name,c in changes.items():
        assert data[name]==c['before'];data[name]=c['after']
    baseline.write_text(json.dumps(data,indent=2))
    stage=m.old.data_folder(m.GAME,p.OUT/'stage')
    for file in (p.OUT/'stage/DATA').rglob('*'):
        if file.is_file():stage.remove_data_file(file.relative_to(p.OUT/'stage/DATA').as_posix())
    print('Installed two phantom visual bounds; physical collision leaves unchanged.')
if __name__=='__main__':main()
