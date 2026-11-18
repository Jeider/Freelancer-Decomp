"""Stage sidecars only for this batch's exclusive material identities."""
from rheinland_audit import *
sys.path.insert(0,str(ROOT/'tools/room_materials'))
from generate import entries,derive,classify

PROFILE='DATA_EXTRA/ROOM_MATERIALS/profiles.txt'

def prepare():
    summary=json.loads((BATCH/'geometry_summary.json').read_text());stage=BATCH/'stage'
    old=(GAME/PROFILE).read_bytes();lines=old.decode('latin1').splitlines(keepends=True);lookup={}
    for i,line in enumerate(lines):
        f=line.split(maxsplit=5)
        if len(f)==6:lookup[f[5].strip().lower()]=(i,f)
    candidates={};files=[];dependencies={PROFILE:sha(old)}
    for model,v in zip(MODELS,summary):
        catalog=json.loads((BATCH/model/'source_scene.json').read_text());raw=Path(v['source']).read_bytes()
        assert sha(raw)==v['source_sha256'];assert sha((stage/v['relative']).read_bytes())==v['prepared_sha256']
        files.append(dict(relative=v['relative'],original=v['source_sha256'],prepared=v['prepared_sha256']))
        root=read_tree(raw)[1][0];textures={t.name.lower():next(n.blob for n in t.children if n.name in ('MIPS','MIP0')) for t in child(root,'Texture library').children}
        names={g['material'] for g in v['changed_groups'] if g['source_triangles_with_relief']}
        for m in child(root,'Material library').children:
            if m.name not in names:continue
            props={n.name:n.blob for n in m.children};tex=text(props['Dt_name']);key=(m.name+'|'+tex).lower()
            candidates[key]=dict(material=m.name,texture=tex,blob=textures[tex.lower()],source=v['relative'])
    # Native material identity is global in the renderer. Even a unique filename
    # is insufficient isolation when another room shares material + diffuse.
    collisions=collections.defaultdict(list);allow={f['relative'].lower() for f in files}
    for folder in ('BASES','CHARACTERS'):
        for path in (GAME/'DATA'/folder).rglob('*'):
            if path.suffix.lower() not in ('.cmp','.3db','.dfm','.mat'):continue
            rel=path.relative_to(GAME).as_posix()
            if rel.lower() in allow:continue
            for parts,off,size,small in entries(path):
                if len(parts)>2 and parts[-1].lower()=='dt_name' and small:
                    key=(parts[-2]+'|'+small.split(b'\0')[0].decode('latin1')).lower()
                    if key in candidates:collisions[key].append(rel)
    records=[];skipped=[]
    for key,c in candidates.items():
        if collisions[key]:skipped.append(dict(key=key,reason='Identity shared outside selected batch',uses=collisions[key]));continue
        if key not in lookup:skipped.append(dict(key=key,reason='No existing shader profile; preserve authored behaviour'));continue
        profile=classify(c['material'],c['texture'],c['source'])
        if profile is None:skipped.append(dict(key=key,reason='Excluded effect/transparent material'));continue
        i,fields=lookup[key];dds,_,packed=derive(c['blob'],profile[0],profile[2]);token=sha(dds)[:32]+'.dds'
        rel='DATA_EXTRA/ROOM_MATERIALS/'+token;oldmap='DATA_EXTRA/ROOM_MATERIALS/'+fields[4]
        unchanged=(GAME/oldmap).read_bytes()==dds
        if unchanged:dependencies[oldmap]=sha(dds)
        else:
            target=stage/rel;target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(dds)
            if rel not in [f['relative'] for f in files]:files.append(dict(relative=rel,original=sha((GAME/rel).read_bytes()) if (GAME/rel).exists() else None,prepared=sha(dds)))
            lines[i]=lines[i].replace(fields[4],token,1)
        records.append(dict(key=key,source=c['source'],source_diffuse_sha256=sha(c['blob']),map=fields[4] if unchanged else token,map_sha256=sha(dds),existing_matches=unchanged,profile_coefficients_unchanged=fields[:4],dimensions=list(packed.shape[:2][::-1])))
    updated=''.join(lines).encode('latin1')
    if updated!=old:
        (stage/PROFILE).write_bytes(updated);files.append(dict(relative=PROFILE,original=sha(old),prepared=sha(updated)))
    # The user added depot + battleship decks; retain the unused commercial
    # variant and the already accepted Bismarck bar.
    for name in ('rh_depot_deck_commercial','rh_bizmark_bar'):
        rel=f'DATA/BASES/RHEINLAND/{name}.cmp';dependencies[rel]=sha((GAME/rel).read_bytes())
    for rel in ('bin/RP9.dll','DATA_EXTRA/SHADERS/room_material.hlsl'):dependencies[rel]=sha((GAME/rel).read_bytes())
    report=dict(records=records,skipped=skipped,foreign_material_identity_scan=True,
        native_materials_unchanged=True,profile_coefficients_unchanged=True,
        algorithm='Existing band-limited normal/roughness estimate from current diffuse; mipmapped RGBA8. Broad baked illumination is filtered in the estimate, not removed from diffuse.',
        new_shader_code=False,game_settings_unchanged=True)
    dump(BATCH/'material_validation.json',report)
    dump(BATCH/'manifest.json',dict(game=str(GAME),files=files,dependencies=dependencies,scope='Nine Rheinland rooms: bars, equipment, depot deck and battleship deck. Other regional/generic rooms, unused commercial depot and existing Bismarck bar excluded. Staged for review.'))
    print(f'{len(records)} recomputed profiles; {len(skipped)} excluded identities; {len(files)} staged files.')

if __name__=='__main__':prepare()
