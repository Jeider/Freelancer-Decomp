"""Courier dependencies for every configured startup INI in the working bin."""
import re
from pathlib import Path
from export import sections, one

DEPENDENCIES={'ships':'SHIPS\\train_courier.ini',
              'solar':'SOLAR\\train_courier.ini',
              'loadouts':'SHIPS\\train_courier_loadouts.ini'}


def startup_inis(game):
    names={'freelancer.ini'}
    port=game/'bin/port.ini'
    if port.exists():
        names.update(one(s,'freelancer_ini') for kind,s in sections(port)
                     if kind.startswith('language.') and one(s,'freelancer_ini'))
    result=[]
    for name in sorted(names):
        path=(game/'bin'/name).resolve()
        assert path.is_relative_to((game/'bin').resolve()), 'Startup INI must belong to the working bin: '+name
        assert path.is_file(), 'Configured startup INI missing: '+name
        result.append(path)
    return result


def add_dependencies(raw,resource_index):
    # Existing launcher comments may use the original Windows code page.
    # Latin-1 preserves those bytes exactly; all inserted names are ASCII.
    bom=b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    text=raw[len(bom):].decode('latin-1'); newline='\r\n' if '\r\n' in text else '\n'
    blocks=re.split(r'(?m)(?=^\[)',text);changed=False;seen=set()
    for i,block in enumerate(blocks):
        match=re.match(r'\[([^\]]+)\]',block)
        if not match or match.group(1).lower() not in ('data','resources'):continue
        kind=match.group(1).lower();assert kind not in seen, 'Duplicate '+kind+' section';seen.add(kind)
        values={}
        for line in block.splitlines()[1:]:
            line=line.split(';',1)[0].strip()
            if '=' in line:
                key,value=line.split('=',1);values.setdefault(key.strip().lower(),[]).append(value.strip().replace('/','\\').lower())
        extra=[]
        if kind=='data':
            for key,value in DEPENDENCIES.items():
                if value.lower() not in values.get(key,[]):extra.append(key+' = '+value)
        else:
            dlls=values.get('dll',[])
            if 'train_courier_text.dll' in dlls:
                assert dlls.index('train_courier_text.dll')+1==resource_index, 'Courier resource index differs between languages'
            else:
                assert len(dlls)+1==resource_index, 'Appending courier resource would change its IDS index'
                extra.append('DLL = train_courier_text.dll')
        if extra:
            blocks[i]=block.rstrip()+newline+newline.join(extra)+newline+newline;changed=True
    assert seen=={'data','resources'}, 'Missing startup sections'
    return bom+''.join(blocks).encode('latin-1') if changed else raw
