"""Prepare 20 English empty-locomotive relocation clips and a minimal source edit."""
import ast
import csv
import io
import json
from pathlib import Path
import zipfile
from dispatcher_en import clips,REPOSITION_FAMILIES

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path('D:/Games/FL_MOD/Assets/Pythonlancer/universe/audio/dispatcher_en.py')

def patch_dispatcher(source):
    tree=ast.parse(source)
    actor=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EngMaleDispatcher')
    method=next(n for n in actor.body if isinstance(n,ast.FunctionDef) and n.name=='get_lines')
    existing={n.args[0].value for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
              and n.func.id=='L' and n.args and isinstance(n.args[0],ast.Constant)}
    missing=[(code,text) for code,text in clips(REPOSITION_FAMILIES) if code not in existing]
    if not missing:return source
    ret=next(n for n in method.body if isinstance(n,ast.Return) and isinstance(n.value,ast.Name) and n.value.id=='lines')
    addition='        # Empty locomotive transfer to the next pickup base.\n        lines.extend([\n'
    addition+=''.join(f'            L({code!r}, {text!r}, R.RuleDefaultNoProcess),\n' for code,text in missing)
    addition+='        ])\n'
    lines=source.splitlines(keepends=True);lines.insert(ret.lineno-1,addition)
    result=''.join(lines);ast.parse(result)
    assert 'list(super().get_lines())' in result
    return result

def main():
    out=ROOT/'out/train_courier/dispatcher_en01_reposition';out.mkdir(parents=True,exist_ok=True)
    records=list(clips(REPOSITION_FAMILIES));assert len(records)==20
    table=io.StringIO(newline='');writer=csv.writer(table,delimiter='\t',lineterminator='\n')
    writer.writerow(['id','filename','text']);writer.writerows((c,c+'.wav',t) for c,t in records)
    files={'recording.tsv':table.getvalue(),
           'lines.json':json.dumps([dict(id=c,filename=c+'.wav',text=t) for c,t in records],indent=2)+'\n',
           'README.txt':'''Generate only these 20 additional clips for dispatcher_en01 (EngMaleDispatcher, STEOS_ID 294).
Use the existing voice and processing. No new base or commodity name recordings.
The '+' prefix must lead naturally into an existing base-name clip.
The '-' tail ends its sentences, then the existing full order follows.

Sequence (one random variant from each family):
tc_reposition_<01..10>+ -> [PICKUP BASE NAME] -> tc_reposition_empty_<01..10>-
-> tc_order_<01..10>+ -> [CARGO NAME] -> tc_destination_<01..10>+
-> [DELIVERY BASE NAME] -> tc_collect_<01..10>-

Example:
There is no suitable outbound load here, Mr. Trent. Your next train is waiting at [BISMARCK].
Leave the delivered wagons here and take only the locomotive. The marker leads to your next pickup.
Here are the new delivery details. We have an order for [MEDICAL SUPPLIES] for delivery to [RECEIVER].
[Existing coupling instructions.]

This sequence is used only when the next load is at a different base.
Source: Assets/Pythonlancer/universe/audio/dispatcher_en.py, EngMaleDispatcher.get_lines().
All added L(...) entries use R.RuleDefaultNoProcess; inherited vocabulary is unchanged.
Intended runtime directory: DATA/Audio/MOD_ENG/dispatcher_en01/.
After generation/export, stage_reposition.py validates all clips and enables reposition_audio_enabled.
Until all 20 registered WAVs are available, the existing order audio still works.
The pickup objective names the loading base even before these new recordings are ready.
'''}
    for name,text in files.items():(out/name).write_text(text,encoding='utf-8')
    with zipfile.ZipFile(out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
        for name in files:archive.write(out/name,arcname=out.name+'/'+name)
    edit=ROOT/'out/train_courier/pythonlancer_edit';edit.mkdir(parents=True,exist_ok=True)
    before=SOURCE.read_bytes();after=patch_dispatcher(before.decode('utf-8')).encode('utf-8')
    (edit/'reposition.before.py').write_bytes(before);(edit/'reposition.after.py').write_bytes(after)
    script='''from pathlib import Path
import ast
root=Path(__file__).resolve().parent
target=Path('D:/Games/FL_MOD/Assets/Pythonlancer/universe/audio/dispatcher_en.py')
before=(root/'reposition.before.py').read_bytes()
after=(root/'reposition.after.py').read_bytes()
assert target.read_bytes()==before, 'Dispatcher changed since preparation'
ast.parse(after.decode('utf-8'))
target.write_bytes(after)
assert target.read_bytes()==after
print('Installed 20 additional English L(..., RuleDefaultNoProcess) lines; existing super() inheritance preserved')
'''
    (edit/'apply.py').write_text(script,encoding='utf-8')
    print('Prepared 20 additional recording lines:',out.with_suffix('.zip'))
    print('Minimal Pythonlancer edit staged; no audio generated')

if __name__=='__main__':main()
