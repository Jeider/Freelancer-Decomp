"""Record short RU cargo names in a full sentence, then crop by verified word timings."""
import argparse
import hashlib
import io
import json
import re
import time
from pathlib import Path
from pydub import AudioSegment
from generate_courier_ru import OUT, plan, references, sha, save, inspect
from generate_evacuation_audio import Recorder
from check_courier_ru import words


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids',nargs='+',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    ref=references()['MaleDispatcher']
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    folder=OUT/'vocabulary_context';folder.mkdir(exist_ok=True)
    ledger_path=folder/'recordings.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
    selected=[r for r in plan() if r['bank']=='vocabulary' and r['id'] in args.ids]
    for row in selected:
        code=row['id']
        text='Новый заказ. Наименование груза: '+row['text']+'. Ожидаю подтверждения.'
        old=ledger.get(code,{})
        target=folder/(code+'_cropped.wav')
        if old.get('text')!=row['text'] or not target.exists() or old.get('sha256')!=sha(target):
            for seed in (42,43,44):
                form=dict(engine='omnivoice',language='ru',text=text,ref_text=ref['text'],num_step='128',
                    seed=str(seed),speed='1.0',denoise='false',postprocess_output='false',pronounce='false')
                started=time.time()
                print('Context generation',code,'seed',seed,flush=True)
                with Recorder._client() as client,Path(ref['path']).open('rb') as stream:
                    response=client.post('/generate',data=form,files={'ref_audio':('MaleDispatcher.wav',stream,'audio/wav')})
                response.raise_for_status()
                sound=AudioSegment.from_file(io.BytesIO(response.content),format='wav').set_channels(1).set_sample_width(2)
                if sound.max_dBFS>-.5:sound=sound.apply_gain(-.5-sound.max_dBFS)
                source=folder/(code+'_context.wav');sound.export(source,format='wav')
                with Recorder._client() as client,source.open('rb') as stream:
                    response=client.post('/v1/audio/transcriptions',data={'language':'ru','model':'whisper-1',
                        'response_format':'verbose_json','timestamp_granularities[]':'word'},
                        files={'file':(source.name,stream,'audio/wav')})
                response.raise_for_status();asr=response.json()
                timeline=asr.get('words',[])
                assert timeline, ('ASR did not return word timings',asr)
                heard=[words(w.get('word',w.get('text',''))) for w in timeline]
                expected=words(row['text']);matches=[]
                for start in range(len(heard)):
                    for end in range(start+1,min(len(heard),start+len(expected)+1)+1):
                        if [t for part in heard[start:end] for t in part]==expected:
                            matches.append((start,end))
                if len(matches)!=1:
                    print('Context mismatch',asr.get('text'),flush=True)
                    continue
                first,last=matches[0]
                a,b=timeline[first]['start'],timeline[last-1]['end']
                previous=timeline[first-1]['end'] if first else 0
                following=timeline[last]['start'] if last<len(timeline) else len(sound)/1000
                a=max(previous,min(a-.06,(previous+a)/2))
                b=min(following,max(b+.06,(b+following)/2))
                cropped=sound[round(a*1000):round(b*1000)]
                silence=AudioSegment.silent(duration=100,frame_rate=sound.frame_rate)
                (silence+cropped+silence).export(target,format='wav')
                info=inspect(target)
                old={**row,'method':'context_crop_v1','reference_sha256':ref['sha256'],'seed':seed,'num_step':128,
                     'request':form,'engine':'omnivoice','signature':hashlib.sha256(json.dumps([form,ref['sha256'],'context_crop_v1']).encode()).hexdigest(),
                     'sha256':sha(target),'source_sha256':sha(source),'context_asr':asr,'crop_seconds':[a,b],
                     'generation_seconds':time.time()-started,**info}
                ledger[code]=old;save(ledger_path,ledger)
                break
            else:
                raise AssertionError('Cannot align the requested name: '+code)
        if args.apply:
            destination=OUT/'vocabulary'/(code+'.wav')
            destination.write_bytes(target.read_bytes())
            records[code]=old
            # Check the cropped result independently inside a known RU prefix.
            from transcribe_courier_vocabulary import check
            result=check(code,records)
            records[code]['asr']=result
            save(OUT/'recordings.json',records)
            print('Cropped ASR',code,result['text'],flush=True)
        else:
            print('Aligned',code,old['crop_seconds'],old['duration'],'seconds',flush=True)


if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
