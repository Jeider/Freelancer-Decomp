"""Export regional relief into review packages, retaining the installed artwork."""
import argparse,json,uuid
import numpy as np
from native_common import DataFolder,child,dump,get_parts,leaves,read_tree,sha
from native_patch import patch
from depot_relief_export import salt_resources
from depot_family_audit import paths,REGIONS
from rheinland_audit import transforms


def export(region,source_paths=None):
    out,live,original,relative=source_paths or paths(region);build=out/'modeled'
    pins=json.loads((out/'sources.json').read_text());raw=live.read_bytes()
    assert sha(raw)==pins['installed_sha256']
    assert sha(original.read_bytes())==pins['original_sha256']
    root=read_tree(raw)[1][0];trans,_=transforms(root)
    arrays=np.load(build/'geometry.npz');stats=json.loads((build/'geometry_validation.json').read_text())
    groups=json.loads((out/'surfaces.json').read_text())['groups'];lookup={g['key']:g for g in groups}
    changes={}
    for record in stats['groups']:
        g=lookup[record['group']];t=arrays[g['key']].copy();r,p=trans[g['part']]
        t[:,:,:3]=(t[:,:,:3]-p)@r.T;t[:,:,3:6]=t[:,:,3:6]@r.T
        changes[g['part'],g['group']]=t
    salt=uuid.uuid4().hex[:10]
    result,validation=patch(raw,changes,region+'_depot_'+salt)
    assert not validation['new_static_parts'],'Review native part splitting before export'
    result,mapping=salt_resources(result,salt)
    output=read_tree(result)[1][0]
    for name in ('Material library','Texture library'):
        assert dict(leaves(child(output,name)))==dict(leaves(child(root,name)))
    assert dict(leaves(child(child(output,'Cmpnd'),'Cons')))==dict(leaves(child(child(root,'Cmpnd'),'Cons')))
    world={};outtrans,_=transforms(output);parts={p['name']:p for p in get_parts(root)}
    for part in get_parts(output):
        r,p=outtrans[part['name']];before=parts[part['name']]['groups']
        assert len(before)==len(part['groups'])
        for i,g in enumerate(part['groups']):
            assert g['material']==before[i]['material']
            if (part['name'],i) not in changes:assert np.array_equal(g['corners'],before[i]['corners'])
            t=g['corners'].copy();t[:,:,:3]=t[:,:,:3]@r+p;t[:,:,3:6]=t[:,:,3:6]@r
            world[f'{part["name"]}_{i:02d}']=t
    assert sum(len(t) for t in world.values())==stats['result_triangles']
    target=DataFolder(root=build/'package').sync_data_file(relative,result)
    np.savez_compressed(build/'exported_geometry.npz',**world)
    validation.update(region=region,exported_sha256=sha(result),export_salt=salt,
        private_resource_mapping=mapping,cmp=str(target),relative=relative,
        original_fl_nd_sha256=pins['original_sha256'],installed_source_sha256=pins['installed_sha256'],
        all_native_material_texture_blobs_preserved=True,cranes_and_props_unchanged=True,
        native_joints_unchanged=True,installed=False)
    dump(build/'native_validation.json',validation)
    assert sha(live.read_bytes())==pins['installed_sha256']
    print('EXPORTED',region,validation['result_triangles'],'triangles',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('regions',nargs='+',choices=list(REGIONS));args=ap.parse_args()
    for region in args.regions:export(region)
