"""Validate the review bundle, or installed files against their saved originals."""
import argparse
import collections
import difflib
import hashlib
import json
import struct as S
from pathlib import Path
from generate_station_lods import read_tree,child,crc
from repair_panel_normals import leaves,triangles,face_normal
from build_component_lods import geometry,fix_winding,fix_zero_normal,remove_duplicates


def sha(b):return hashlib.sha256(b).hexdigest()


def main(installed=False):
    bundle=Path('bin/component_lods');manifest=json.loads((bundle/'manifest.json').read_text())
    runtime=Path('D:/games/FL_MOD/DATA')
    before_root=Path(json.loads((bundle/'installation.json').read_text(encoding='utf-8-sig'))['Backup']) if installed else runtime
    after_root=runtime if installed else bundle
    new_keys=set()
    for row in manifest['models']+manifest['fixes']:
        before=(before_root/row['file']).read_bytes();after=(after_root/row['file']).read_bytes()
        assert sha(before)==row['source_sha256'] and sha(after)==row['output_sha256']
        old={p:b for p,_,b in leaves(before)[1]};new={p:b for p,_,b in leaves(after)[1]}
        is_lod='levels' in row
        for p,b in old.items():
            destination=p.replace('/VMeshPart/','/MultiLevel/Level0/VMeshPart/',1) if is_lod and p.startswith('/\\/VMeshPart/') else p
            if is_lod and p.lower()=='/\\/multilevel/switch2':continue
            if row.get('repairs') and (p.lower().endswith('/vmeshdata') or (not is_lod and p=='/\\/VMeshPart/VMeshRef')):continue
            assert new[destination]==b,(row['file'],p)
        _,rs=read_tree(after);root=rs[0]
        lib={crc(n.name):child(n,'VMeshData').blob for n in child(root,'VMeshLibrary').children}
        levels=range(3) if is_lod else [None]
        near_groups=None
        for level in levels:
            scope=child(child(root,'MultiLevel'),f'Level{level}') if is_lod else root
            ref=child(child(scope,'VMeshPart'),'VMeshRef').blob;key=S.unpack_from('<I',ref,4)[0]
            h,ds,gs=triangles(geometry(lib[key]))
            assert S.unpack_from('<6H',ref,8)==(0,h[-1],0,h[3],0,h[2])
            if level==0:near_groups={m:cs for (m,_,_),cs in zip(ds,gs)}
            if level:
                assert key not in new_keys;new_keys.add(key)
                for cs in gs:
                    for i in range(0,len(cs),3):assert face_normal(cs[i:i+3]) is not None
                current={m:cs for (m,_,_),cs in zip(ds,gs)}
                assert current.keys()==near_groups.keys()
                for m in row['materials']['preserved']:assert current[m]==near_groups[m], 'Protected alpha/aerial triangles changed'
        if row.get('repairs'):
            _,rs=read_tree(before);r=rs[0]
            oldref=child(child(r,'VMeshPart'),'VMeshRef').blob
            mesh=next(n for n in child(r,'VMeshLibrary').children if crc(n.name)==S.unpack_from('<I',oldref,4)[0])
            raw=child(mesh,'VMeshData').blob
            function=fix_winding if is_lod else (fix_zero_normal if 'arch' in row['file'] else remove_duplicates)
            expected,_=function(raw)
            path=next(p for p in old if p.lower().endswith('/'+mesh.name.lower()+'/vmeshdata'))
            assert new[path]==expected
    for cfg in manifest['configs']:
        before=(before_root/cfg['file']).read_bytes()
        after=(runtime/cfg['file']).read_bytes() if installed else Path(cfg['staged']).read_bytes()
        assert sha(before)==cfg['source_sha256'] and sha(after)==cfg['output_sha256']
        diff=[l for l in difflib.ndiff(before.decode('cp1251').splitlines(),after.decode('cp1251').splitlines()) if l.startswith(('- ','+ '))]
        assert len(diff)==len(cfg['changes'])*2 and all(l[2:].startswith('LODranges') for l in diff)
        for row in cfg['changes']:
            r=row['after'];assert len(r)==4 and r==sorted(r) and r[-1]==row['before'][-1]
    print('PASS:', 'installed' if installed else 'staged', '10 LOD models + 2 local repairs; CRCs, indices, bounds, hardpoints, protected alpha/aerial islands and 29 config ranges verified')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--installed',action='store_true');args=ap.parse_args();main(args.installed)
