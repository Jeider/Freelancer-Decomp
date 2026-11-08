"""Apply the user's full-scene maximum-strength NR profile and hide ReShade UI."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_neural'
NR={
    'NeuralUplift':'1','NREnableUpscaling':'0','EnableHooks':'2',
    'NRIntensity':'2','NRGlobalTone':'2','NRLocalTone':'2','NRLocalStructure':'2',
    'NRSkinStructure':'1','NRAutoMask':'0','NRUICorrection':'0',
    'NRColorStrength':'1','NRTransferStrength':'1',
    # These are calibration/conventions, not quality sliders. Native SDR/pixel vectors.
    'NRPaperWhiteScale':'1','NRMVecScaleX':'1','NRMVecScaleY':'1',
}
OVERLAY={k:'0' for k in ('ShowClock','ShowFPS','ShowFrameTime','ShowPresetName',
                        'ShowPresetTransitionMessage','ShowScreenshotMessage','ShowForceLoadEffectsButton')}
OVERLAY['TutorialProgress']='4'

def update(data,section,values):
    # Byte-preserving edits: port.ini can contain localized values in other sections.
    pattern=rb'(?ims)^\['+re.escape(section.encode())+rb'\][^\r\n]*\r?\n.*?(?=^\[|\Z)'
    match=re.search(pattern,data)
    block=match.group() if match else b'['+section.encode()+b']\r\n'
    for key,value in values.items():
        line=key.encode()+b'='+value.encode()
        key_pattern=rb'(?im)^\s*'+re.escape(key.encode())+rb'\s*=[^\r\n]*'
        if re.search(key_pattern,block):block=re.sub(key_pattern,lambda _:line,block)
        else:block=block.rstrip()+b'\r\n'+line+b'\r\n'
    if match:return data[:match.start()]+block.rstrip()+b'\r\n\r\n'+data[match.end():]
    return data.rstrip()+b'\r\n\r\n'+block.rstrip()+b'\r\n\r\n'

def apply_configs(binary):
    result={}
    for relative in ('ReShade.ini','neural/host64/ReShade.ini'):
        data=(binary/relative).read_bytes()
        data=update(data,'INPUT',{'KeyOverlay':'0,0,0,0','KeyScreenshot':'0,0,0,0','InputProcessing':'0','GamepadNavigation':'0'})
        data=update(data,'OVERLAY',OVERLAY)
        if relative.startswith('neural/'):data=update(data,'RenoDX.DLSS5',NR)
        result[relative]=data
    if (binary/'port.ini').exists():
        result['port.ini']=update((binary/'port.ini').read_bytes(),'BaseNeural',
            {'mode':'2','result_deadline_ms':'250','blend_strength':'1'})
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--staged',action='store_true')
    ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    binary=OUT/'on/bin' if args.staged else Path('D:/Games/FL_MOD/bin')
    changes=apply_configs(binary)
    if not args.staged:changes['fl_base_neural.addon32']=(OUT/'on/bin/fl_base_neural.addon32').read_bytes()
    if not args.apply:
        for name,data in changes.items():print(name,hashlib.sha256(data).hexdigest())
        print('Prepared full-scene NR: blend=1; intensity/global tone/local tone/structure=2; skin=1; mask off; enable preference preserved')
        return
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup=OUT/'backups'/('max_profile_'+stamp);backup.mkdir(parents=True)
    manifest={}
    for name,data in changes.items():
        original=binary/name
        (backup/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(original,backup/name)
        manifest[name]={'before':hashlib.sha256(original.read_bytes()).hexdigest(),'after':hashlib.sha256(data).hexdigest()}
    touched=[]
    try:
        # Install binary first: if the game still has it mapped, no settings are changed.
        for name in sorted(changes,key=lambda n:0 if n.endswith('.addon32') else 1):
            touched.append(name);(binary/name).write_bytes(changes[name])
            assert hashlib.sha256((binary/name).read_bytes()).hexdigest()==manifest[name]['after']
    except Exception:
        for name in reversed(touched):
            if (binary/name).read_bytes()!=(backup/name).read_bytes():shutil.copy2(backup/name,binary/name)
        raise
    (backup/'profile.json').write_text(json.dumps({'binary':str(binary),'files':manifest},indent=2))
    print('Applied maximum full-scene profile and hidden overlay at',binary,'; backup:',backup)

if __name__=='__main__':main()
