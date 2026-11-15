"""Synchronize live story static prefixes into their authoritative dev sources."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
import re
from pathlib import Path
from train_courier.data_output import data_folder

GAME=Path('D:/Games/FL_MOD')
OUT=Path(__file__).resolve().parents[1]/'out/story_dev_sync'
SYSTEMS={'or_hq':'ORDER_HQ','rh_vien':'RH_VIENNA','asf_hq':'ASF_HQ'}


def split_dev(raw):
    marker=list(re.finditer(rb'(?m)^nickname = divider\r?$',raw))
    assert len(marker)==1,'Expected exactly one story divider'
    starts=list(re.finditer(rb'(?m)^\[Object\][^\r\n]*\r?$',raw[:marker[0].start()]))
    assert starts
    at=starts[-1].start()
    # StorySystem discards precisely the [Object] line before the divider.
    assert raw[at:marker[0].start()].strip()==b'[Object]'
    return raw[:at],raw[at:]


def generator_static(raw):
    # Mirror the read-only extraction algorithm; never import/run Pythonlancer.
    lines=[]
    for line in raw.decode('utf-8-sig').replace('\r\n','\n').splitlines(keepends=True):
        if line.strip()=='nickname = divider':break
        lines.append(line)
        if line.strip()=='[SystemInfo]':lines.append('space_farclip = 100000\n')
    del lines[-1]
    return ''.join(lines)


def semantic(text):
    return [line.split(';',1)[0].strip() for line in text.splitlines() if line.split(';',1)[0].strip()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    pending={};reports={};sources={}
    for name,folder in SYSTEMS.items():
        rel=f'UNIVERSE/SPECIAL/{folder}/{name}'
        live=(GAME/'DATA'/f'{rel}.ini').read_bytes()
        dev=(GAME/'DATA'/f'{rel}_dev.ini').read_bytes()
        prefix,tail=split_dev(dev)
        # Story content classes here contain only STORY=True ships, which emit no
        # system objects. The final system is entirely the static dev prefix.
        farclips=re.findall(rb'(?mi)^space_farclip\s*=\s*([^\r\n]+)',live)
        assert farclips==[b'100000'],(name,farclips)
        new_prefix=re.sub(rb'(?mi)^space_farclip\s*=[^\r\n]*\r?\n',b'',live)
        newline=b'\r\n' if b'\r\n' in dev else b'\n'
        new_prefix=new_prefix.rstrip()+newline+newline
        updated=new_prefix+tail
        assert split_dev(updated)[1]==tail
        projected=generator_static(updated)
        assert semantic(projected)==semantic(live.decode('utf-8-sig')),name+' generation mismatch'
        old_lines=generator_static(dev).splitlines()
        new_lines=projected.splitlines()
        diff='\n'.join(difflib.unified_diff(old_lines,new_lines,fromfile=name+'_dev static',tofile=name+' live',lineterm=''))+'\n'
        (OUT/f'{name}.diff').write_text(diff,encoding='utf-8')
        old_names=Counter(re.findall(rb'(?mi)^nickname\s*=\s*([^\r\n]+)',prefix))
        new_names=Counter(re.findall(rb'(?mi)^nickname\s*=\s*([^\r\n]+)',new_prefix))
        reports[name]=dict(old_prefix_bytes=len(prefix),new_prefix_bytes=len(new_prefix),tail_bytes=len(tail),
            tail_sha256=hashlib.sha256(tail).hexdigest(),removed_names=sum((old_names-new_names).values()),
            added_names=sum((new_names-old_names).values()),changed=updated!=dev,roundtrip_matches_live=True)
        print(name,json.dumps(reports[name]),flush=True)
        sources[f'{rel}.ini']=hashlib.sha256(live).hexdigest()
        sources[f'{rel}_dev.ini']=hashlib.sha256(dev).hexdigest()
        if updated!=dev:pending[f'{rel}_dev.ini']=(dev,updated)
    (OUT/'report.json').write_text(json.dumps(dict(sources=sources,systems=reports),indent=2))
    if not args.apply:return
    folder=data_folder(GAME,GAME);backup=data_folder(GAME,OUT/'rollback')
    # Single small rollback set for these three source files, no game-tree backup.
    for rel,sha in sources.items():assert hashlib.sha256((GAME/'DATA'/rel).read_bytes()).hexdigest()==sha
    for rel,(old,new) in pending.items():
        target=backup.data_path(rel)
        if target.exists():assert target.read_bytes()==old,'Existing rollback differs'
        else:backup.sync_data_file(rel,old)
    touched=[]
    try:
        for rel,(old,new) in pending.items():
            touched.append(rel);folder.sync_data_file(rel,new)
        for rel,(_,new) in pending.items():assert (GAME/'DATA'/rel).read_bytes()==new
    except Exception:
        for rel in reversed(touched):folder.sync_data_file(rel,pending[rel][0])
        raise
    (OUT/'installed.json').write_text(json.dumps({rel:hashlib.sha256(new).hexdigest() for rel,(_,new) in pending.items()},indent=2))
    print('Synced',len(pending),'dev files; static round-trip matches live, all dev tails byte-identical; generator not run')


if __name__=='__main__':main()
