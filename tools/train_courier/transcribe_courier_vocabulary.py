"""Check isolated cargo names inside a generic RU radio context (no target hints).

VoiceStudio's capture endpoint ignores the language hint and auto-detects language.
One short Russian noun can be mistaken for English/noise. A known Russian prefix
anchors detection; its independently verified words are removed from the result.
"""
import argparse
import io
import json
import re
from pydub import AudioSegment
from generate_courier_ru import OUT, sha, save, transcribe
from generate_evacuation_audio import Recorder
from check_courier_ru import words


def check(code, records):
    prefix_ids = ('tc_board_01-', 'tc_order_01+')
    prefix_text = ' '.join(records[name]['text'] for name in prefix_ids)
    sound = AudioSegment.empty()
    for name in prefix_ids:
        row = records[name]
        sound += AudioSegment.from_wav(OUT/row['bank']/(name+'.wav'))
        sound += AudioSegment.silent(duration=250,frame_rate=sound.frame_rate)
    row=records[code]
    path=OUT/row['bank']/(code+'.wav')
    assert sha(path)==row['sha256']
    offset=len(sound)/1000
    sound+=AudioSegment.from_wav(path)
    sound+=AudioSegment.silent(duration=500,frame_rate=sound.frame_rate)
    stream=io.BytesIO();sound.export(stream,format='wav');stream.seek(0)
    with Recorder._client() as client:
        response=client.post('/transcribe',data={'language':'ru','mode':'reference','refine':'false'},
                             files={'audio':(path.name,stream,'audio/wav')})
    response.raise_for_status()
    full=response.json()
    expected=words(prefix_text)
    tokens=list(re.finditer(r'[а-яёa-z0-9]+',full.get('text',''),re.I))
    prefix_heard=' '.join(match[0] for match in tokens[:len(expected)])
    assert words(prefix_heard)==expected, ('Context prefix changed',code,full['text'])
    text=full['text'][tokens[len(expected)-1].end():].lstrip(' .,:;!?—-')
    return dict(text=text,language=full.get('language'),engine=full.get('engine'),
                context_offset_seconds=offset,context_prefix=prefix_text,raw_context_result=full)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids',nargs='+')
    parser.add_argument('--apply',action='store_true',help='Update only ASR records, after other recording writers finish')
    parser.add_argument('--direct',action='store_true',help='Use local STT with explicitly forced Russian, without prefix')
    args=parser.parse_args()
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    ledger_path=OUT/'vocabulary_context_asr.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
    for code,row in records.items():
        if row['bank']!='vocabulary' or args.ids and code not in args.ids:
            continue
        mode='forced_ru' if args.direct else 'ru_context'
        if ledger.get(code,{}).get('sha256')!=row['sha256'] or ledger.get(code,{}).get('mode')!=mode:
            result=transcribe(OUT/'vocabulary'/(code+'.wav')) if args.direct else check(code,records)
            ledger[code]=dict(sha256=row['sha256'],asr=result,mode=mode)
            save(ledger_path,ledger)
        result=ledger[code]['asr']
        print(code, 'OK' if words(row['text'])==words(result['text']) else 'REVIEW',result['text'],flush=True)
        if args.apply:
            records[code]['asr']=result
            save(OUT/'recordings.json',records)


if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
