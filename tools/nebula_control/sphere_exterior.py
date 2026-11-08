"""Stage/install Sphere's meshless 40km retail interior and volumetric exterior."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
OUT=ROOT/'src/obj/sphere_exterior'
SYSTEM='DATA/UNIVERSE/SPECIAL/SPHERE/sphere.ini'
TEMPLATE='DATA/UNIVERSE/SPECIAL/SPHERE/sphere_dev.ini'
NEBULA='DATA/SOLAR/NEBULA_MOD/sphere_nebula.ini'
VOLUME='DATA_EXTRA/VOLUMETRIC/volumetric.ini'
PROFILE='''[NebulaOverride]
; Sphere: volume outside the meshless asteroid-field exclusion; retail fog inside.
; CameraInsideNebulaExclusion disables this entry before style/quality overrides.
file = sphere_nebula
enabled = 1
replace_fog_overlay = 1
replace_object_fog = 1
'''


def sha(data):return hashlib.sha256(data).hexdigest()


def edit_section(text,header,selector,updates):
    count=0
    def edit(match):
        nonlocal count
        body=match[2]
        if selector and not re.search(selector,body,re.I|re.M):return match[0]
        count+=1
        for key,value in updates.items():
            pattern=rf'(?im)^({re.escape(key)}\s*=\s*)[^\n]*'
            if re.search(pattern,body):body=re.sub(pattern,lambda m:m[1]+value,body)
            else:body=f'{key} = {value}\n'+body
        return match[1]+body
    result=re.sub(rf'(?ims)(^\[{re.escape(header)}\][^\n]*\n)(.*?)(?=^\[|\Z)',edit,text)
    assert count==1,(header,count)
    return result


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);manifest={}
    for relative in (SYSTEM,TEMPLATE,NEBULA,VOLUME):
        original=(GAME/relative).read_bytes();text=original.decode('utf-8-sig').replace('\r\n','\n')
        if relative in (SYSTEM,TEMPLATE):
            # This is the actual source template loaded by Pythonlancer StorySystem.
            text=edit_section(text,'Nebula',r'^file\s*=\s*solar\\nebula_mod\\sphere_nebula.ini\s*$',{'volumetric':'true'})
            field=re.search(r'(?ims)^\[zone\]\s*\nnickname\s*=\s*Zone_sphere_main_sphere\s*\n(.*?)(?=^\[|\Z)',text)[1]
            assert re.search(r'(?im)^size\s*=\s*40000\s*$',field)
            assert re.search(r'(?im)^shape\s*=\s*SPHERE\s*$',field)
        elif relative==NEBULA:
            text=edit_section(text,'Exclusion Zones',None,{'exclusion':'Zone_sphere_main_sphere'})
            text=edit_section(text,'Fog',None,{'fog_enabled':'1'})
            assert not re.search(r'(?im)^zone_shell\s*=',text)
            assert re.search(r'(?im)^fog_far\s*=\s*10000(?:\.0+)?\s*$',text)
        else:
            assert not re.search(r'(?im)^file\s*=\s*sphere_nebula\s*$',text),'Sphere override already exists; review it'
            text=text.rstrip()+'\n\n'+PROFILE
        newline='\r\n' if b'\r\n' in original else '\n'
        data=text.replace('\n',newline).encode('utf-8')
        if original.startswith(b'\xef\xbb\xbf'):data=b'\xef\xbb\xbf'+data
        dest=OUT/'staged'/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        manifest[relative]={'before':sha(original),'after':sha(data)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT/'README.txt').write_text('Sphere exterior volume / retail interior\n'
        'Sphere field and meshless nebula exclusion share Zone_sphere_main_sphere (radius 40000).\n'
        'Old inner exclusion radius was 35000, leaving a 5km volumetric annulus inside the field.\n'
        'Retail fog enabled, existing colour 30,55,40 and exclusion fog_far 10000 preserved.\n'
        'Only sphere_nebula overrides replacement of legacy fog outside the exclusion.\n'
        'Inside, the existing native exclusion gate drops the volume entry and restores retail fog.\n'
        'sphere_dev.ini is Pythonlancer StorySystem DIRECT_TEMPLATE_NAME source.\n'
        'No mesh, renderer binary, asteroid layout, unrelated nebula or quality setting changed.\n')
    print('PASS: staged four files; 40km meshless exclusion, fog enabled, sphere-only override, Pythonlancer source preserved')


def apply():
    manifest=json.loads((OUT/'manifest.json').read_text())
    for relative,m in manifest.items():
        assert sha((GAME/relative).read_bytes())==m['before'],relative+' changed since preparation'
        assert sha((OUT/'staged'/relative).read_bytes())==m['after']
    backup=OUT/('backup_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    for relative in manifest:
        dest=backup/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((GAME/relative).read_bytes())
    for relative,m in manifest.items():
        (GAME/relative).write_bytes((OUT/'staged'/relative).read_bytes())
        assert sha((GAME/relative).read_bytes())==m['after']
    print('Installed and hash-verified Sphere configs and Pythonlancer source. Backup:',backup)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else prepare()
