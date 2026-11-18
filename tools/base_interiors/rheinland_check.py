"""Validate the concrete staged room package, DDS chain and matching previews."""
from rheinland_audit import *
from PIL import Image

def valid_png(path):
    # A disk-full PNG can have a plausible size and still be truncated.
    with Image.open(path) as im:
        assert im.format=='PNG',path
        im.verify()
    with Image.open(path) as im:
        im.load()
        assert min(im.size)>=600,path

def main():
    manifest=json.loads((BATCH/'manifest.json').read_text());records=json.loads((BATCH/'material_validation.json').read_text())['records']
    for f in manifest['files']:
        p=BATCH/'stage'/f['relative'];assert sha(p.read_bytes())==f['prepared']
        live=GAME/f['relative'];assert (sha(live.read_bytes()) if live.exists() else None)==f['original']
    for rel,hash_ in manifest['dependencies'].items():assert sha((GAME/rel).read_bytes())==hash_,rel
    profile='DATA_EXTRA/ROOM_MATERIALS/profiles.txt'
    def keys(raw):
        result={}
        for line in raw.decode('latin1').splitlines():
            f=line.split(maxsplit=5)
            if len(f)==6:result[f[5]]=f[:5]
        return result
    old=keys((GAME/profile).read_bytes());new=keys((BATCH/'stage'/profile).read_bytes())
    assert old.keys()==new.keys()
    for key in old:assert old[key][:4]==new[key][:4],key
    changed={k for k in old if old[k]!=new[k]};assert changed=={r['key'] for r in records if not r['existing_matches']}
    for r in records:
        blob=(BATCH/'stage/DATA_EXTRA/ROOM_MATERIALS'/r['map']).read_bytes();assert sha(blob)==r['map_sha256']
        assert blob[:4]==b'DDS ';h,w=S.unpack_from('<II',blob,12);levels=S.unpack_from('<I',blob,28)[0]
        assert max(h,w)<=256 and levels==int(math.log2(max(h,w)))+1
        offset=128
        for level in range(levels):
            hh,ww=max(1,h>>level),max(1,w>>level);size=hh*ww*4
            pix=np.frombuffer(blob,'uint8',size,offset).reshape(hh,ww,4);offset+=size
            nx=pix[:,:,2].astype(float)/127.5-1;ny=pix[:,:,1].astype(float)/127.5-1
            assert np.max(nx*nx+ny*ny)<1 and pix[:,:,3].min()==255
        assert offset==len(blob)
    report=[]
    for model in MODELS:
        dest=BATCH/model;v=json.loads((dest/'validation.json').read_text());a=json.loads((dest/'preview.json').read_text());b=json.loads((dest/'inspection.json').read_text())
        assert a['prepared_sha256']==b['prepared_sha256']==v['prepared_sha256']
        assert b['saved_originals_hidden_in_viewport_and_render'] and b['source_model_unmodified']
        assert v['original_materials_textures_animations_joint_records_unchanged'] and v['both_uv_sets_preserved']
        assert all(x['indices']<=65535 and x['vertices']<=65535 for x in v['mesh_blocks'])
        assert all(g['max_connected_patch_depth_discontinuity']==0 for g in v['changed_groups'])
        # Verify the preservation claim against actual geometric face normals,
        # independently of the artist normals used by the selection gate.
        root=read_tree(Path(v['source']).read_bytes())[1][0];patched=read_tree((BATCH/'stage'/v['relative']).read_bytes())[1][0]
        trans,_=transforms(root);newparts={p['name']:p for p in get_parts(patched)};max_y=0.
        for part in get_parts(root):
            for gi,g in enumerate(part['groups']):
                untouched={t.tobytes() for t in newparts[part['name']]['groups'][gi]['corners']}
                for t in g['corners']:
                    if t.tobytes() in untouched:continue
                    n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);length=np.linalg.norm(n)
                    if length<1e-10:continue
                    y=abs(((n/length)@trans[part['name']][0])[1]);max_y=max(max_y,float(y));assert y<=.71,(model,'Horizontal surface modified')
        changed_mats={g['material'] for g in v['changed_groups'] if g['source_triangles_with_relief']}
        assert changed_mats=={r['material'] for r in b['materials']},(model,'Missing material preview')
        for mode in ('before','after'):
            for style in ('room','textured','clay'):valid_png(dest/f'{mode}_{style}.png')
        for r in b['materials']:
            for mode in ('before','after','clay'):valid_png(dest/'inspection'/f'{r["stem"]}_{mode}.png')
        report.append(dict(model=model,source_triangles=v['source_triangles'],result_triangles=v['result_triangles'],reviewed_materials=len(changed_mats),max_modified_face_normal_y=max_y))
    dump(BATCH/'package_check.json',dict(models=report,maps=len(records),native_limits_pass=True,material_properties_preserved=True,excluded_models_unchanged=True,source_hashes_match=True,preview_hashes_match=True,preview_png_decode_pass=True,installed=False))
    print(json.dumps(dict(models=len(report),maps=len(records),checks='passed',installed=False),indent=2))

if __name__=='__main__':
    import math
    main()
