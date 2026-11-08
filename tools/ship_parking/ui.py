"""Build a native P icon and install parking labels/contact icons with source persistence."""
import argparse
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import struct as S
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
GAME=PROJECT.parent.parent
OUT=ROOT/'src/obj/ship_parking/ui'
ASSET=ROOT/'assets/ship_parking/parking_p.3db'
IDS=238391
ICON_SCALE=.60  # 40% smaller than the original parking sign; button hitbox is unchanged.
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools'))
from generate_station_lods import Node, child, crc, read_tree, write_tree
from make_targeting_icons import branch


def build():
    # Native geometry, with a constant white UI texture for the game's tinting.
    # The P and frame remain sharp at every resolution and need no bitmap font.
    polys=[ [(-14,-18),(-6,-18),(-6,17),(-14,17)] ]
    outer=[(-6,17),(8,17),(15,10),(15,3),(8,-4),(-6,-4)]
    inner=[(-6,10),(5,10),(8,7),(8,6),(5,3),(-6,3)]
    for i in range(len(outer)-1): polys.append([outer[i],outer[i+1],inner[i+1],inner[i]])
    # Thin square border identifies a parking sign at small service-tab sizes.
    polys.extend([[(-24,-24),(24,-24),(24,-22),(-24,-22)],
                  [(-24,22),(24,22),(24,24),(-24,24)],
                  [(-24,-22),(-22,-22),(-22,22),(-24,22)],
                  [(22,-22),(24,-22),(24,22),(22,22)]])
    vertices=[];indices=[]
    for polygon in polys:
        area=sum(polygon[i][0]*polygon[(i+1)%4][1]-polygon[(i+1)%4][0]*polygon[i][1] for i in range(4))
        if area<0: polygon.reverse()
        base=len(vertices)
        vertices.extend((x/1000*ICON_SCALE,y/1000*ICON_SCALE,0,.5,.5) for x,y in polygon)
        indices.extend(base+i for i in (0,1,2,0,2,3))
    header,roots=read_tree((GAME/'DATA/INTERFACE/BASESIDE/ship_dealer.3db').read_bytes())
    root=roots[0]
    material=copy.deepcopy(next(n for n in child(root,'Material library').children if n.children))
    material.name='UI_parking_p'
    child(material,'Dt_name').blob=b'parking_p_white.tga\0'
    texture=S.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,1,1,32,8)+b'\xff'*4
    mesh='parking_p.lod0.vms'
    blob=S.pack('<II4H',1,4,1,len(indices),0x102,len(vertices))
    blob+=S.pack('<I4H',crc(material.name),0,len(vertices)-1,len(indices),204)
    blob+=S.pack('<'+'H'*len(indices),*indices)
    blob+=b''.join(S.pack('<5f',*p) for p in vertices)
    half=.024*ICON_SCALE
    bounds=(half,-half,half,-half,0,0,0,0,0,(2*half**2)**.5)
    ref=S.pack('<II6H10f',60,crc(mesh),0,len(vertices),0,len(indices),0,1,*bounds)
    root.children=[branch('VMeshLibrary',[branch(mesh,[Node('VMeshData',blob)])]),
                   branch('VMeshPart',[Node('VMeshRef',ref)]),
                   branch('Material library',[Node('Material count',S.pack('<I',1)),material]),
                   branch('Texture library',[branch('parking_p_white.tga',[Node('MIP0',texture)])])]
    data=write_tree(header,roots)
    checked=read_tree(data)[1][0]
    assert child(child(checked,'VMeshPart'),'VMeshRef').blob==ref
    assert child(child(checked,'VMeshLibrary').children[0],'VMeshData').blob==blob
    ASSET.parent.mkdir(parents=True,exist_ok=True);ASSET.write_bytes(data)
    OUT.mkdir(parents=True,exist_ok=True)
    # Preview rendered from the same polygons as the native mesh.
    from PIL import Image,ImageDraw
    preview=Image.new('RGB',(512,512),(12,19,29));draw=ImageDraw.Draw(preview)
    for polygon in polys: draw.polygon([(256+x*9*ICON_SCALE,256-y*9*ICON_SCALE) for x,y in polygon],fill=(99,190,231))
    preview.resize((256,256),Image.Resampling.LANCZOS).save(OUT/'parking_p.png')
    print('Built native P icon:',ASSET)


def icon():
    """Install only the rebuilt model and its persistent Pythonlancer source asset."""
    sys.path.insert(0,str(PROJECT))
    from tools.data_folder import DataFolder
    content=ASSET.read_bytes()
    backup=OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    target=PROJECT/'assets/parking/parking_p.3db'
    if target.exists():
        backup.mkdir(parents=True,exist_ok=True)
        (backup/'source_parking_p.3db').write_bytes(target.read_bytes())
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(content)
    folder=DataFolder(root=GAME)
    folder.sync_parking_ui({'Interface/Baseside/parking_p.3db':content},backup/'data')
    assert target.read_bytes()==folder.data_path('Interface/Baseside/parking_p.3db').read_bytes()==content
    print('Installed parking icon at 60% size; Pythonlancer source updated; backup:',backup)


def set_icon(content, icon):
    chunks=re.split(rb'(?m)(?=^\[)',content)
    count=0
    for i,chunk in enumerate(chunks):
        if not chunk.lower().startswith(b'[characterencounter]'): continue
        count+=1
        nl=b'\r\n' if b'\r\n' in chunk else b'\n'
        chunk=re.sub(rb'(?im)^icon\s*=[^\r\n]*\r?\n',b'',chunk)
        choices=re.search(rb'(?im)^choices\s*=[^\r\n]*\r?\n',chunk)
        pos=choices.end() if choices else chunk.index(b'\n')+1
        chunks[i]=chunk[:pos]+b'icon = '+icon.encode()+nl+chunk[pos:]
    assert count==1
    return b''.join(chunks)


def label_files():
    sys.path.insert(0,str(ROOT/'tools/targeting_hud'))
    import stage_interface_strings as ids
    sys.path.insert(0,str(ROOT/'tools/train_courier'))
    from launchers import startup_inis
    from generate import sections
    result={}
    source=(PROJECT/'text/static.py').read_text(encoding='utf-8-sig')
    ru,en='Парковка','Parking'
    calls=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Call) and
           isinstance(n.func,ast.Name) and n.func.id=='Static' and n.args and
           isinstance(n.args[0],ast.Constant) and n.args[0].value==IDS]
    if calls:
        assert len(calls)==1 and [ast.literal_eval(v) for v in calls[0].args[1].args]==[ru,en]
    else:
        source=source.replace('STATIC_NAMES = [\n',f'STATIC_NAMES = [\n    Static({IDS}, MS({ru!r}, {en!r})),  # Parking service\n',1)
        assert f'Static({IDS},' in source
    result['Assets/Pythonlancer/text/static.py']=source.encode('utf-8')
    visited=set()
    for ini in startup_inis(GAME):
        resource=next(r for k,r in sections(ini) if k=='resources')['dll'][2]
        path=(GAME/'bin'/resource.replace('\\','/')).resolve()
        assert path.is_relative_to(GAME) and path.name.lower()=='nameresources.dll'
        if path in visited: continue
        visited.add(path)
        english='resources_eng' in str(path).lower()
        label=en if english else ru
        before=ids.resources(path);expected=dict(before)
        block,slot=(IDS&65535)//16+1,IDS%16
        keys=[k for k in before if k[0]==6 and k[1]==block] or [(6,block,1033)]
        temporary=OUT/('parking_label_en.dll' if english else 'parking_label_ru.dll')
        temporary.write_bytes(path.read_bytes())
        handle=ids.check(ids.begin(str(temporary),False))
        try:
            for key in keys:
                strings=ids.decode_block(before.get(key,b'\0'*32))
                assert not strings[slot] or strings[slot]==label,'Occupied parking label IDS'
                strings[slot]=label;raw=ids.encode_block(strings)
                buf=ids.c.create_string_buffer(raw)
                ids.check(ids.update(handle,*key,buf,len(raw)));expected[key]=raw
        except BaseException:
            ids.end(handle,True);raise
        ids.check(ids.end(handle,False))
        assert ids.resources(temporary)==expected
        result[path.relative_to(GAME).as_posix()]=temporary.read_bytes()
    return result


def apply():
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+n+b'"' in processes for n in
                   (b'freelancer.exe',b'freelancer_en.exe',b'freelancer_window.exe',b'freelancer_window_en.exe',b'flserver.exe')),'Close game before replacing resources'
    sys.path.insert(0,str(PROJECT))
    from tools.data_folder import DataFolder
    from managers.parking_commandants import parse,one
    from managers.parking_ui import plan
    backup=OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    changes=label_files()
    changes['Assets/Pythonlancer/assets/parking/parking_p.3db']=ASSET.read_bytes()
    # Patch only these small expressions; preserve concurrent generator changes.
    for name,old,new in (
        ('managers/courier_owners.py',r'choices = true\ndialog =',r'choices = true\nicon = mission\ndialog ='),
        ('files/rpg_runtime.py','(click_script|dialog)','(click_script|dialog|icon)'),
        ('files/rpg_runtime.py',r"b'dialog = RPG\\rm0001_dialog.ini\r\n'",r"b'dialog = RPG\\rm0001_dialog.ini\r\nicon = mission\r\n'")):
        key='Assets/Pythonlancer/'+name
        raw=changes.get(key,(PROJECT/name).read_bytes())
        if new.encode() not in raw:
            assert raw.count(old.encode())==1,name
            raw=raw.replace(old.encode(),new.encode(),1)
        compile(raw,name,'exec');changes[key]=raw
    for name,content in changes.items():
        target=GAME/name
        if target.exists() and target.read_bytes()==content: continue
        if target.exists():
            saved=backup/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(target.read_bytes())
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
        assert target.read_bytes()==content
    folder=DataFolder(root=GAME)
    files=plan(PROJECT,lambda p:folder.data_path(p).read_bytes())
    paths={'RPG/rh_biz_contact.ini':'mission'}
    for catalog,icon in (('RPG/courier_contacts.ini','mission'),('RPG/parking_contacts.ini','rumor')):
        path=folder.data_path(catalog)
        if not path.exists(): continue
        for kind,row in parse(path.read_bytes()):
            if kind=='rpgcontact': paths[one(row,'rtc').replace('\\','/')]=icon
    for path,icon in paths.items(): files[path]=set_icon(folder.data_path(path).read_bytes(),icon)
    folder.sync_parking_ui(files,backup/'data')
    assert all(folder.data_path(p).read_bytes()==c for p,c in files.items())
    report={'contacts':len(paths),'mission':sum(v=='mission' for v in paths.values()),
            'rumor':sum(v=='rumor' for v in paths.values()),'label_ids':IDS,
            'files':{p:hashlib.sha256(c).hexdigest() for p,c in files.items()},'backup':str(backup)}
    (OUT/'installed.json').write_text(json.dumps(report,indent=2))
    print('Installed parking P/labels and contact icons:',report['mission'],'mission,',report['rumor'],'rumor')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['build','apply','icon'])
    globals()[parser.parse_args().command]()
