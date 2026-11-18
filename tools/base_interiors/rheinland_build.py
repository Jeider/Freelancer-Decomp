"""Stage sparse structural relief in reviewed Rheinland room models."""
from rheinland_audit import *
from relief_mesh import refine
from native_patch import patch

def main(selected_models=None):
    definitions=json.loads((BATCH/'authored_features.json').read_text());summary=[]
    for model in MODELS:
        if selected_models and model not in selected_models:
            summary.append(json.loads((BATCH/model/'validation.json').read_text()));continue
        dest=BATCH/model;catalog=json.loads((dest/'source_scene.json').read_text());source=Path(catalog['source']);raw=source.read_bytes()
        assert sha(raw)==catalog['sha256']
        root=read_tree(raw)[1][0];trans,kinds=transforms(root);parts=get_parts(root);changes={};records=[]
        # All selected materials are architectural; also exclude animated roots
        # and their descendants, independently of material names.
        parents={};moving={n for n,k in kinds.items() if k!='Fix'}
        for kind in child(child(root,'Cmpnd'),'Cons').children:
            size={'Fix':176,'Rev':208,'Pris':208,'Sphere':212}[kind.name]
            for off in range(0,len(kind.blob),size):parents[text(kind.blob[off+64:off+128])]=text(kind.blob[off:off+64])
        for _ in range(len(parents)):
            moving.update(n for n,p in parents.items() if p in moving)
        for p in parts:
            if p['name'] in moving:continue
            if model=='rh_depot_deck' and p['name'] not in ('Root','room'):continue
            if model=='rh_battleship_deck' and not (p['name'].lower().startswith(('wall_back_','wall_exit_')) or p['name']=='lock'):continue
            for gi,g in enumerate(p['groups']):
                m=catalog['materials'][str(g['material'])];definition=definitions[model].get(m['name'])
                if definition is None or g['corners'].shape[-1]<8:continue
                assert definition['texture_sha256']==m['textures']['Dt_name']['sha256']
                updated,stats=refine(g['corners'],definition['features'],trans[p['name']][0])
                stats.update(part=p['name'],group=gi,material=m['name'])
                records.append(stats)
                if stats['source_triangles_with_relief']:
                    changes[p['name'],gi]=updated
        assert changes,model
        result,validation=patch(raw,changes,model)
        rel=source.relative_to(GAME/'DATA').as_posix();DataFolder(root=BATCH/'stage').sync_data_file(rel,result)
        validation.update(changed_groups=records,source=str(source),relative='DATA/'+rel,animated_parts_preserved=sorted(moving),installed=False)
        dump(dest/'validation.json',validation);summary.append(validation)
        print(model,validation['source_triangles'],'->',validation['result_triangles'],'triangles;',len(changes),'changed groups',flush=True)
    dump(BATCH/'geometry_summary.json',summary)
if __name__=='__main__':main(sys.argv[1:] or None)
