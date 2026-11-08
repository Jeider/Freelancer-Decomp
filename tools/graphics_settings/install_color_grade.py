"""Install native color presets and opt-in neural rendering, preserving unrelated settings."""
from pathlib import Path
import argparse
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools/base_neural'))
import install_slider as installer
from max_profile import update
from tools.targeting_hud import stage_interface_strings as strings
installer.PACKAGE=installer.OUT/'color_grade';installer.PAYLOAD=installer.PACKAGE/'payload'

def stage():
    proof=json.loads((ROOT/'out/color_grade/gpu/verified.json').read_text())
    assert installer.sha(ROOT/'src/RP9/ColorGradeShader.h')==proof['shader_sha256'],'Color shader changed after GPU test'
    neural=json.loads((installer.OUT/'checks/strength/verified.json').read_text())
    assert installer.sha(installer.OUT/'on/bin/fl_base_neural.addon32')==neural['addon_sha256'],'Neural adapter changed after GPU test'
    strings.STAGE=installer.PAYLOAD;strings.main();rows=[]
    for row in json.loads((installer.PACKAGE/'strings_manifest.json').read_text()):
        if row['original'].lower()!=row['prepared'].lower():rows.append({'relative':row['relative'],'before':row['original'].lower(),'after':row['prepared'].lower()})
    for name in ('freelancer.exe','RP9.dll','fl_base_neural.addon32'):
        relative='bin/'+name;target=installer.PAYLOAD/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(installer.OUT/'on/bin'/name,target)
        rows.append({'relative':relative,'before':installer.sha(installer.GAME/relative),'after':installer.sha(target)})
    for relative,section,values in (
        ('bin/port.ini','BaseNeural',{'enabled':'0','supersample_scale':'1.0'}),
        ('bin/neural/host64/ReShade.ini','RenoDX.DLSS5',{'NRSkinStructure':'1'})):
        source=installer.GAME/relative;target=installer.PAYLOAD/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(update(source.read_bytes(),section,values))
        rows.append({'relative':relative,'before':installer.sha(source),'after':installer.sha(target)})
    guards={name:installer.sha(installer.GAME/name) for name in ('bin/Common.dll','bin/Content.dll','bin/Server.dll','bin/ReShade.ini')}
    (installer.PACKAGE/'manifest.json').write_text(json.dumps({'files':rows,'guards':guards},indent=2))
    print('Prepared 3 native color presets, RU/EN resources/static cache; DLSS default off; supersampling off;',len(rows),'files')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage',action='store_true');mode.add_argument('--apply',action='store_true');args=ap.parse_args()
    if args.stage:stage()
    else:installer.apply()
