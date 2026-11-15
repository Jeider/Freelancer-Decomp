"""Repair global EngBase nested-archetype name collisions; preserve all geometry."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import valensia_mega as m


def signature(node):
    return node.name,node.blob,tuple(signature(c) for c in node.children)


def rename(raw,stem,reverse=False):
    header,roots=m.utf.read_tree(raw)
    root=roots[0];changes=[]
    for entry in m.b.one(root,'Cmpnd').children:
        file=m.b.one(entry,'File name');obj=m.b.one(entry,'Object name')
        if file is None:continue
        previous=m.b.text(file.blob)
        object_name=m.b.text(obj.blob)
        desired=(object_name if reverse else stem+'_'+object_name)+'.3db'
        assert len(desired.encode('ascii'))<64
        node=next(n for n in root.children if n.name==previous)
        node.name=desired;file.blob=(desired+'\0').encode('ascii')
        changes.append((previous,desired))
    return m.utf.write_tree(header,roots),changes


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    installed_path=m.OUT/'installed.json';installed=json.loads(installed_path.read_text())
    destination=m.OUT/'part_name_fix'
    stage=m.old.data_folder(m.GAME,destination)
    payload={};before={};old_names=defaultdict(list);new_names={};reports={}
    paths=[name for name in installed['hashes'] if name.endswith('.cmp')]
    for name in paths:
        raw=(m.GAME/name).read_bytes()
        assert m.old.sha256(raw).hexdigest()==installed['hashes'][name],name+' changed since install'
        stem=Path(name).stem
        fixed,changes=rename(raw,stem)
        # Exact round trip proves that only names changed, not triangle buffers,
        # LODs, transforms, hardpoints, materials, or UTF metadata.
        restored,_=rename(fixed,stem,reverse=True)
        assert restored==raw,name+' non-name data changed'
        for previous,desired in changes:
            old_names[m.utf.crc(previous)].append(name+'/'+previous)
            crc=m.utf.crc(desired)
            assert crc not in new_names,(desired,new_names.get(crc))
            new_names[crc]=name+'/'+desired
        payload[name]=fixed;before[name]=raw
        stage.sync_data_file(name[5:],fixed)
        reports[name]=dict(before=m.old.sha256(raw).hexdigest(),after=m.old.sha256(fixed).hexdigest(),names=changes)
    collisions={hex(crc):names for crc,names in old_names.items() if len(names)>1}
    assert collisions,'Expected to detect the installed generic-name collision'
    destination.mkdir(parents=True,exist_ok=True)
    report=dict(models=len(paths),unique_nested_names=len(new_names),old_collisions=collisions,files=reports,
                geometry_unchanged=True,backup='No binary duplicate: reverse recorded names reproduces exact previous bytes')
    (destination/'report.json').write_text(json.dumps(report,indent=2))
    print('PASS:',len(paths),'models;',len(new_names),'globally unique nested names; exact geometry/LOD/SUR preservation')
    if not args.apply:return
    live=m.old.data_folder(m.GAME,m.GAME);touched=[]
    try:
        for name,raw in payload.items():
            assert (m.GAME/name).read_bytes()==before[name],name+' changed during validation'
            touched.append(name);live.sync_data_file(name[5:],raw)
        for name,raw in payload.items():assert (m.GAME/name).read_bytes()==raw
    except Exception:
        for name in reversed(touched):live.sync_data_file(name[5:],before[name])
        raise
    for name,raw in payload.items():installed['hashes'][name]=m.old.sha256(raw).hexdigest()
    installed['part_name_fix']=str(destination/'report.json')
    installed_path.write_text(json.dumps(installed,indent=2))
    freed=0
    for name,raw in payload.items():freed+=len(raw);stage.remove_data_file(name[5:])
    print('Installed and verified. Removed temporary payload MiB:',round(freed/2**20,2))


if __name__=='__main__':main()
