"""Validate recorded radio words, audio format, event coverage and durations."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from evacuation_script import rows,FAMILIES
from evacuation_delivery import INACTIVE_FAMILIES
from generate_evacuation_audio import inspect,OUT,ROOT,sha

def words(text):
    text=text.lower().replace('cancelled','canceled').replace('’',"'")
    for key,value in {"you're":"you are","you've":"you have","you'll":"you will", "it's":"it is", "don't":"do not", "can't":"cannot",
                      "we're":"we are","we've":"we have","that's":"that is","isn't":"is not","i'm":"i am","doesn't":"does not"}.items():
        text=text.replace(key,value)
    for key,value in {'one':'1','five':'5','ten':'10','thirty':'30','sixty':'60','percent':'per cent'}.items():
        text=re.sub(r'\b'+key+r'\b',value,text)
    return re.findall(r'[a-z0-9]+',text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial',action='store_true')
    args=parser.parse_args()
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    radio=[r for r in rows() if r['speaker']=='dispatcher']
    report={'recordings_sha256':sha(OUT/'recordings.json'),'radio_count':0,'unresolved':[],
            'validation':'PCM/level/duration/hash checks and local ASR text comparison; not an in-game listening test',
            'language':'en','radio_seconds':0,'active_radio_count':0,'active_radio_seconds':0,
            'revised_radio_count':0,'revised_radio_seconds':0,'text_differences':{}}
    for row in radio:
        record=records.get(row['id'])
        if record is None:
            if not args.partial:report['unresolved'].append(row['id']+':missing')
            continue
        path=OUT/(row['id']+'.wav')
        assert record['text']==row['en'] and sha(path)==record['sha256'],path
        assert record.get('delivery')==row.get('delivery'),row['id']
        info=inspect(path)
        assert abs(info['duration']-record['duration'])<.000001
        if row['family']=='te_return_10':assert info['duration']<8
        report['radio_count']+=1;report['radio_seconds']+=info['duration']
        if row['active']:
            report['active_radio_count']+=1;report['active_radio_seconds']+=info['duration']
        if row.get('delivery'):
            report['revised_radio_count']+=1;report['revised_radio_seconds']+=info['duration']
        expected=words(row['en']);heard=words(record.get('asr',{}).get('text',''))
        if expected!=heard:
            report['unresolved'].append(row['id'])
            diff=list(difflib.ndiff(expected,heard))
            report['text_differences'][row['id']]={'expected':row['en'],
                'asr':record.get('asr',{}).get('text',''),'words':[t for t in diff if not t.startswith('  ')]}
    engine='\n'.join((ROOT/p).read_text(encoding='utf-8') for p in ('src/Content/TrainCourier.cpp','src/Content/TrainCourierEvacuation.inl'))
    hooks=set(re.findall(r'"(te_[a-z0-9_]+)"',engine))
    active=set(FAMILIES)-INACTIVE_FAMILIES
    assert hooks==active,{'missing_hooks':active-hooks,'unexpected_hooks':hooks-active}
    report['hooked_families']=len(hooks)
    report['inactive_families']=sorted(INACTIVE_FAMILIES)
    (OUT/('verification_partial.json' if args.partial else 'verification.json')).write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report['unresolved'] and not args.partial:raise SystemExit(1)

if __name__=='__main__':main()
