"""Resolve RTC Location -> universe base -> room -> THN -> petaldb mesh."""
import json
from pathlib import Path
from inventory import DATA, OUT, entries, read_source
from binary import read_binary

def sections(path):
    section=None
    values=[]
    for line in path.read_text(encoding='utf-8-sig',errors='replace').splitlines():
        line=line.split(';',1)[0].strip()
        if line.startswith('['):
            if section: yield section,dict(values)
            section=line.strip('[]').lower();values=[]
        elif '=' in line:
            k,v=line.split('=',1);values.append((k.strip().lower(),v.strip()))
    if section: yield section,dict(values)

def at(path): return DATA/path.replace('\\','/')
bases={v['nickname'].lower():v['file'] for k,v in sections(DATA/'UNIVERSE/universe.ini') if k=='base'}
models={}
for _,key,value in entries(DATA/'petaldb.ini'):
    if key=='room':
        nick,file=value.split(',',1)
        models[nick.strip().lower()]=file.strip().replace('\\','/')
cache={}
results={}
inv=json.loads((OUT/'inventory.json').read_text())
for name,item in inv['scenes'].items():
    info={}
    for use in item['uses']:
        if use['role']=='act_callthorn': continue
        location=next((value for _,key,value in entries(Path(use['reference'])) if key=='location'),None)
        if not location: continue
        base,room=[x.strip().lower() for x in location.split(',')[:2]]
        info['location']=location
        try:
            basefile=at(bases[base])
            roomfile=next(at(v['file']) for k,v in sections(basefile) if k=='room' and v['nickname'].lower()==room)
            set_script=next(v['set_script'] for k,v in sections(roomfile) if k=='room_info')
            info.update(base_file=str(basefile),room_file=str(roomfile),set_script=set_script)
            if set_script not in cache:
                path=at(set_script);raw=path.read_bytes();read_source.SOURCE=path
                cache[set_script]=read_binary(raw) if raw.startswith(b'\x1bLua') else read_source.read()
            room_entities=[e for e in cache[set_script]['entities'] if e.get('template_name','').lower() in models]
            info['models']=[models[e['template_name'].lower()] for e in room_entities]
            # Exported OBJ name is exactly the CMP stem, no guessed substitute room.
            for model in info['models']:
                obj=Path('E:/FL/room')/(Path(model).stem+'.obj')
                if obj.exists():
                    info['room_mesh']=str(obj)
                    break
            info['status']='matched' if 'room_mesh' in info else 'matching OBJ not exported'
        except Exception as exc:
            info['status']='room dependency unavailable'
            info['detail']=repr(exc)
        break
    if not info: info['status']='space/action scene or relocation without room geometry'
    specfile=OUT/'specs'/f'{name}.json'
    spec=json.loads(specfile.read_text())
    spec.update({k:v for k,v in info.items() if k=='room_mesh'})
    specfile.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    results[name]=info
(OUT/'room_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Exact room mesh matches',sum('room_mesh' in i for i in results.values()))
