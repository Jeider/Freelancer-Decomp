"""Recalculate sidecars from current embedded diffuse, retaining native material blobs."""
from native_common import *
sys.path.insert(0,str(ROOT/'tools/room_materials'))
from generate import derive,classify

PROFILE='DATA_EXTRA/ROOM_MATERIALS/profiles.txt'

def prepare():
    root=read_tree((GAME/'DATA'/REL).read_bytes())[1][0]
    textures={t.name.lower():next(n.blob for n in t.children if n.name in ('MIPS','MIP0')) for t in child(root,'Texture library').children}
    old=(GAME/PROFILE).read_bytes();lines=old.decode('latin1').splitlines();lookup={}
    for i,line in enumerate(lines):
        fields=line.split(maxsplit=5)
        if len(fields)==6:lookup[fields[5].lower()]=(i,fields)
    names=set(json.loads((PROTO/'prototype_stats.json').read_text())['material_triangles'])
    records=[];files=[]
    for m in child(root,'Material library').children:
        if m.name.split('.')[0].lower() not in names:continue
        props={n.name:n.blob for n in m.children}
        tex=text(props['Dt_name']);key=(m.name+'|'+tex).lower()
        role,normal,rough,spec,skin=classify(m.name,tex,'DATA/'+REL)
        assert key in lookup,'Expected installed room shader profile: '+key
        i,fields=lookup[key]
        dds,_,packed=derive(textures[tex.lower()],role,rough)
        oldmap='DATA_EXTRA/ROOM_MATERIALS/'+fields[4]
        same=(GAME/oldmap).read_bytes()==dds
        # New maps are immutable content-addressed sidecars, never overwrite a
        # shared existing file. Retain profile tuning and every unrelated line.
        if not same:
            token=sha(dds)[:32]+'.dds';rel='DATA_EXTRA/ROOM_MATERIALS/'+token
            dest=STAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(dds)
            fields[4]=token;lines[i]=' '.join(fields)
            if rel not in [f['relative'] for f in files]:files.append(dict(relative=rel,original=sha((GAME/rel).read_bytes()) if (GAME/rel).exists() else None,prepared=sha(dds)))
        records.append(dict(material=m.name,texture=tex,type=text(props['Type']),
                            profile=fields[:4],source_diffuse_sha256=sha(textures[tex.lower()]),
                            map=fields[4],map_sha256=sha(dds),existing_map_matches_recalculation=same,
                            dimensions=[packed.shape[1],packed.shape[0]],
                            native_material_unchanged=True))
    assert len(records)==11
    if files:
        data=('\n'.join(lines)+'\n').encode('latin1');dest=STAGE/PROFILE;dest.write_bytes(data)
        files.append(dict(relative=PROFILE,original=sha(old),prepared=sha(data)))
    report=dict(materials=records,files=files,shader='DATA_EXTRA/SHADERS/room_material.hlsl',
                installed_shader_matches_checked_source=(GAME/'DATA_EXTRA/SHADERS/room_material.hlsl').read_bytes()==(ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl').read_bytes(),
                algorithm='Existing room-material band-limited diffuse estimate, full mip chain; geometric bevel normals separately exported.',
                note='Diffuse-derived normals are an estimate; broad baked lighting is filtered, not removed from the original diffuse.')
    assert report['installed_shader_matches_checked_source']
    dump(OUT/'material_validation.json',report)
    print(f'Recomputed {len(records)} maps; {sum(r["existing_map_matches_recalculation"] for r in records)} already match; {len(files)} staged sidecar/profile changes.')
    validation=json.loads((OUT/'native_validation.json').read_text())
    dependencies={'bin/RP9.dll':sha((GAME/'bin/RP9.dll').read_bytes()),'DATA_EXTRA/SHADERS/room_material.hlsl':sha((GAME/'DATA_EXTRA/SHADERS/room_material.hlsl').read_bytes())}
    # Native shader activation remains subject to the user's graphics settings.
    dependencies[PROFILE]=sha(old)
    for r in records:
        if r['existing_map_matches_recalculation']:dependencies['DATA_EXTRA/ROOM_MATERIALS/'+r['map']]=r['map_sha256']
    manifest=dict(game=str(GAME),files=[dict(relative='DATA/'+REL,original=validation['source_sha256'],prepared=validation['prepared_sha256'])]+files,
                  dependencies=dependencies,prototype=str(PROTO),scope='Bismarck bar reviewed relief, authored materials and room effects retained')
    dump(OUT/'manifest.json',manifest)

if __name__=='__main__':prepare()
