"""Export the reviewed depot geometry to a separate native CMP package."""
import copy,json,sys,uuid
from pathlib import Path
import numpy as np
from native_common import *
from native_patch import patch
from rheinland_audit import transforms
from depot_surface_audit import OUT,ORIGINAL,CURRENT

BUILD=OUT/'modeled'


def salt_resources(raw,salt):
    header,roots=read_tree(raw);root=roots[0]
    mapping={}
    for i,p in enumerate(get_parts(root)):
        mapping[p['filename']]=f'depot_{salt}_part_{i:02d}.3db'
    for i,n in enumerate(child(root,'VMeshLibrary').children):
        mapping[n.name]=f'depot_{salt}_mesh_{i:03d}.vms'
    crcs={crc(a):crc(b) for a,b in mapping.items()}
    assert len(set(crcs.values()))==len(crcs)
    def visit(n):
        if n.name=='File name' and n.blob is not None:
            old=text(n.blob)
            if old in mapping:n.blob=mapping[old].encode()+b'\0'
        if n.name in ('VMeshRef','VWireData') and n.blob is not None:
            old=S.unpack_from('<I',n.blob,4)[0]
            assert old in crcs,(n.name,old)
            value=bytearray(n.blob);S.pack_into('<I',value,4,crcs[old]);n.blob=bytes(value)
        n.name=mapping.get(n.name,n.name)
        for c in n.children:visit(c)
    visit(root)
    return write_tree(header,roots),mapping


def family_audit():
    records=[]
    for nation,folder in [('rh','RHEINLAND'),('ku','KUSARI'),('li','LIBERTY'),('br','BRETONIA')]:
        p=Path('D:/Games/FL_ND/FL_ND/DATA/BASES')/folder/(nation+'_depot_deck.cmp')
        raw=p.read_bytes();root=read_tree(raw)[1][0];parts=get_parts(root)
        records.append(dict(region=nation,source=str(p),sha256=sha(raw),
            parts=[dict(name=q['name'],triangles=sum(len(g['corners']) for g in q['groups'])) for q in parts],
            geometry_sha256=sha(b''.join(g['corners'].tobytes() for q in parts for g in q['groups']))))
    return dict(models=records,conclusion='Shared depot construction and crane topology; regional room geometry and UV/material bindings differ. Transfer the feature schema, meshing, validation and per-wall intent; author regional mappings after RH review.',
                other_regions_modified=False)


def main():
    pins=json.loads((OUT/'sources.json').read_text());raw=ORIGINAL.read_bytes();current=CURRENT.read_bytes()
    assert sha(raw)==pins['original_sha256'] and sha(current)==pins['installed_sha256']
    header,roots=read_tree(raw);root=roots[0];current_root=read_tree(current)[1][0]
    for name in ('Material library','Texture library'):
        original=child(root,name);root.children[root.children.index(original)]=copy.deepcopy(child(current_root,name))
    baseline=write_tree(header,roots)
    arrays=np.load(BUILD/'geometry.npz');stats=json.loads((BUILD/'geometry_validation.json').read_text())
    groups=json.loads((OUT/'surfaces.json').read_text())['groups'];lookup={g['key']:g for g in groups}
    trans,_=transforms(root);changes={}
    for record in stats['groups']:
        g=lookup[record['group']];t=arrays[g['key']].copy();r,p=trans[g['part']]
        t[:,:,:3]=(t[:,:,:3]-p)@r.T;t[:,:,3:6]=t[:,:,3:6]@r.T
        changes[g['part'],g['group']]=t
    salt=uuid.uuid4().hex[:10]
    result,validation=patch(baseline,changes,'depot_rework_'+salt)
    result,mapping=salt_resources(result,salt)
    outroot=read_tree(result)[1][0];after_parts=get_parts(outroot)
    assert dict(leaves(child(outroot,'Material library')))==dict(leaves(child(current_root,'Material library')))
    assert dict(leaves(child(outroot,'Texture library')))==dict(leaves(child(current_root,'Texture library')))
    assert dict(leaves(child(child(outroot,'Cmpnd'),'Cons')))==dict(leaves(child(child(root,'Cmpnd'),'Cons'))), 'Unexpected new joint/part splitting'
    # Decode exported native bytes for the Blender preview, not pre-export arrays.
    world={};outtrans,_=transforms(outroot)
    original_parts={p['name']:p for p in get_parts(root)}
    for part in after_parts:
        r,p=outtrans[part['name']]
        for i,g in enumerate(part['groups']):
            t=g['corners'].copy();t[:,:,:3]=t[:,:,:3]@r+p;t[:,:,3:6]=t[:,:,3:6]@r
            world[f'{part["name"]}_{i:02d}']=t
        if part['name'] not in ('Root','room'):
            original=original_parts[part['name']]
            assert len(original['groups'])==len(part['groups'])
            assert all(a['material']==b['material'] and np.array_equal(a['corners'],b['corners']) for a,b in zip(original['groups'],part['groups']))
    assert sum(len(t) for t in world.values())==stats['result_triangles']
    package=BUILD/'package';relative='BASES/RHEINLAND/rh_depot_deck.cmp'
    target=DataFolder(root=package).sync_data_file(relative,result)
    np.savez_compressed(BUILD/'exported_geometry.npz',**world)
    validation.update(exported_sha256=sha(result),export_salt=salt,private_resource_mapping=mapping,
        cmp=str(target),original_fl_nd_sha256=pins['original_sha256'],installed_source_sha256=pins['installed_sha256'],
        all_native_material_texture_blobs_preserved=True,cranes_and_props_unchanged=True,
        native_joints_unchanged=True,installed=False)
    (BUILD/'native_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    (BUILD/'regional_transfer.json').write_text(json.dumps(family_audit(),indent=2)+'\n')
    assert sha(ORIGINAL.read_bytes())==pins['original_sha256'] and sha(CURRENT.read_bytes())==pins['installed_sha256']
    print('EXPORTED',target,validation['result_triangles'],'triangles')


if __name__=='__main__':main()
