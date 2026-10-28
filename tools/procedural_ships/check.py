"""Validate the staged li_elite replacement against the actual source, then package it."""
import hashlib
import json
from pathlib import Path
import struct
import zipfile

import numpy as np
from li_elite import SOURCE, MAT, OUT, leaves, crc, decode, extract_part


def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    report=json.loads((OUT/'report.json').read_text())
    target=OUT/'DATA/SHIPS/LIBERTY/LI_ELITE/li_elite.cmp'
    source=SOURCE.read_bytes();output=target.read_bytes()
    for raw,key in ((source,'source_sha256'),(output,'output_sha256'),(MAT.read_bytes(),'material_sha256')):
        require(hashlib.sha256(raw).hexdigest()==report[key],'Source or artifact hash mismatch: '+key)
    old={p:b for p,_,b in leaves(source)[1]}
    new={p:b for p,_,b in leaves(output)[1]}
    require(set(old)<=set(new),'Original UTF leaves removed')
    changed={p for p in old if old[p]!=new[p]}
    require(len(changed)==4 and all(p.endswith('/Level0/VMeshPart/VMeshRef') for p in changed),
            'Unexpected original leaf changed')
    added=set(new)-set(old)
    require(len(added)==4 and all('/VMeshLibrary/proc_li_elite_medium_' in p and p.endswith('/VMeshData') for p in added),
            'Unexpected additions')
    libraries={};library_paths={}
    for p,b in new.items():
        if not p.endswith('/VMeshData'):continue
        key=crc(p.split('/')[-2]);require(key not in libraries,'Library CRC collision')
        libraries[key]=decode(b);library_paths[key]=p
    total=0;references=0;wireframes=0
    for p,b in new.items():
        if p.endswith('/VMeshRef'):
            groups=extract_part(b,libraries);references+=1
            if '/Level0/' in p:total+=sum(len(g['corners']) for g in groups)
            if p in changed:
                v=np.concatenate([g['corners'].reshape(-1,8) for g in groups])
                require(np.isfinite(v).all(),'Non-finite output')
                require(np.allclose(np.linalg.norm(v[:,3:6],axis=1),1,atol=2e-5),'Invalid normals')
        if p.endswith('/VWireData'):
            key=struct.unpack_from('<I',b,4)[0]
            require(key in libraries,'Unresolved HUD wire library')
            lp=library_paths[key]
            require(b==old[p] and new[lp]==old[lp],'HUD wire or its backing vertex stream changed')
            wireframes+=1
    require(total==report['medium_triangles']==17305,'Medium budget changed')
    unchanged=sum(1 for p in old if '/Hardpoints/' in p or '/Animation/' in p or '/Cmpnd/' in p)
    readme=Path(__file__).with_name('README.txt')
    (OUT/'README.txt').write_bytes(readme.read_bytes())
    checks=dict(result='PASS',source_sha256=report['source_sha256'],output_sha256=report['output_sha256'],
                original_triangles=report['original_triangles'],medium_triangles=total,
                resolved_mesh_references=references,unchanged_hud_wires=wireframes,
                unchanged_hardpoint_animation_construction_leaves=unchanged,
                original_libraries_retained=True,source_hashes_match=True,
                live_game_test=False)
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    archive=OUT/'li_elite_medium_max_recess.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in (target,OUT/'report.json',OUT/'checks.json',OUT/'README.txt',
                  OUT/'comparison.jpg',OUT/'hull_closeup.jpg',OUT/'depth_masks.jpg'):
            z.write(p,p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as z:require(z.testzip() is None,'Archive checksum failure')
    print(json.dumps(checks,indent=2))
    print('Archive:',archive)


if __name__=='__main__':main()
