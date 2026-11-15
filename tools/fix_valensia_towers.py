"""Restore skipped Switch2-only tower visuals; verify habitats and unchanged geometry."""
import argparse
from collections import Counter,defaultdict
import json
import struct as S
import numpy as np
import valensia_mega as m
from check_valensia_mega import templates,triangles


def decoded(raw,lods):
    root=m.utf.read_tree(raw)[1][0]
    library={ident:m.b.one(n,'VMeshData').blob for ident,n in m.b.library_meshes(root).items()}
    result=defaultdict(Counter)
    for entry in m.b.one(root,'Cmpnd').children:
        obj,file=m.b.one(entry,'Object name'),m.b.one(entry,'File name')
        if not obj:continue
        node=m.b.one(root,m.b.text(file.blob));ranges=lods[m.b.text(obj.blob)]
        for level in m.b.one(node,'MultiLevel').children:
            if not level.name.startswith('Level'):continue
            ref=m.b.one(level,'VMeshRef')
            if ref:
                ident=S.unpack_from('<I',ref.blob,4)[0]
                result[(ranges,int(level.name[5:]))].update(triangles(library[ident],ref.blob))
    return result


def expected(visuals):
    result=defaultdict(Counter)
    for visual in visuals:
        for level,(groups,verts) in enumerate(visual.levels):
            transformed=[m.mesh.xform_vert(v,visual.rotation,visual.translation) for v in verts]
            for mat,ids in groups:
                result[(visual.ranges,level)].update((mat,tuple(transformed[i] for i in ids[j:j+3])) for j in range(0,len(ids),3))
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest=json.loads((m.OUT/'manifest.json').read_text())
    installed_path=m.OUT/'installed.json';installed=json.loads(installed_path.read_text())
    source=templates((m.GAME/m.old.ORIGINAL_TEMPLATE).read_text(encoding='utf-8-sig'))
    source['or_hq_live']=(m.GAME/'DATA'/m.old.LIVE.replace('.ini','Original.ini')).read_text(encoding='utf-8-sig')
    lods=defaultdict(dict);nick=''
    for block in m.old.blocks((m.GAME/'DATA/SOLAR/solararch.ini').read_text(encoding='utf-8-sig')):
        d=m.old.fields(block)
        if block.lower().startswith('[solar]'):nick=m.old.one(d,'nickname')
        if block.lower().startswith('[lod]') and nick.startswith('vlm_'):
            lods[nick][m.old.one(d,'obj')]=tuple(m.mesh.floats(m.old.one(d,'lodranges')))
    builder=m.Builder();payload={};before={};reports={}
    out=m.OUT/'tower_fix';stage=m.old.data_folder(m.GAME,out)
    for label,report in manifest['reports'].items():
        rows={p.name:p for p in m.b.placements_from_template(source[label])}
        for component in report['components']:
            if component['group'] not in ('TOP','BOTTOM'):continue
            name=component['name'];origin=np.array(component['origin'])
            all_visuals,towers,habitats=[],[],[];tower_count=habitat_count=0
            for nick in component['members']:
                row=rows[nick];visuals,_,_=builder.expand(row,origin)
                all_visuals.extend(visuals)
                if row.archetype=='space_control_tower':towers.extend(visuals);tower_count+=1
                if 'habitat' in row.archetype:habitats.extend(visuals);habitat_count+=1
            assert towers and habitats
            raw,new_lods,stats=m.write_cmp(name,all_visuals)
            new_lods={m.old.one(m.old.fields(block),'obj'):tuple(m.mesh.floats(m.old.one(m.old.fields(block),'lodranges'))) for block in new_lods}
            assert new_lods==lods[name],name+' would require LOD configuration change'
            header,roots=m.utf.read_tree(raw)
            for library_name,entries in builder.embedded.items():
                node=m.utf.Node(library_name);node.children=[m.b.clone(n) for n in entries.values()];roots[0].children.append(node)
            raw=m.utf.write_tree(header,roots)
            relative=f'DATA/SOLAR/OPTIMIZED/valensia_mega/{name}.cmp'
            previous=(m.GAME/relative).read_bytes()
            assert m.old.sha256(previous).hexdigest()==installed['hashes'][relative]
            old_geometry=decoded(previous,lods[name]);new_geometry=decoded(raw,new_lods)
            tower_geometry=expected(towers);habitat_geometry=expected(habitats)
            assert dict(new_geometry)==dict(expected(all_visuals))
            for key in set(old_geometry)|set(new_geometry)|set(tower_geometry):
                assert old_geometry[key]+tower_geometry[key]==new_geometry[key],(name,key,'unexpected geometry change')
            for key,values in habitat_geometry.items():
                assert not (values-new_geometry[key]),name+' habitat absent'
            payload[relative]=raw;before[relative]=previous;stage.sync_data_file(relative[5:],raw)
            reports[name]=dict(towers_restored=tower_count,habitats_verified=habitat_count,
                added_lod_triangles=sum(sum(c.values()) for c in tower_geometry.values()),
                before=m.old.sha256(previous).hexdigest(),after=m.old.sha256(raw).hexdigest(),**stats)
            print(name,reports[name],flush=True)
    for name,sha in builder.sources.items():
        if name in manifest['sources']:assert sha==manifest['sources'][name],name+' source changed'
    # Global file-name CRC uniqueness across every simultaneously loaded compound.
    names={}
    for name in installed['hashes']:
        if not name.endswith('.cmp'):continue
        root=m.utf.read_tree(payload.get(name,(m.GAME/name).read_bytes()))[1][0]
        for entry in m.b.one(root,'Cmpnd').children:
            file=m.b.one(entry,'File name')
            if file:
                key=m.utf.crc(m.b.text(file.blob));assert key not in names,(name,names.get(key));names[key]=name
    out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(reports,indent=2))
    print('PASS: only missing towers added; all habitats present; LOD configuration and SUR unchanged')
    if not args.apply:return
    live=m.old.data_folder(m.GAME,m.GAME);touched=[]
    try:
        for name,raw in payload.items():
            assert (m.GAME/name).read_bytes()==before[name]
            touched.append(name);live.sync_data_file(name[5:],raw)
        for name,raw in payload.items():assert (m.GAME/name).read_bytes()==raw
    except Exception:
        for name in reversed(touched):live.sync_data_file(name[5:],before[name])
        raise
    for name,raw in payload.items():installed['hashes'][name]=m.old.sha256(raw).hexdigest()
    installed['tower_fix']=str(out/'report.json');installed_path.write_text(json.dumps(installed,indent=2))
    for name in payload:stage.remove_data_file(name[5:])
    print('Installed six corrected CMPs; temporary payload removed; no additional full backup')


if __name__=='__main__':main()
