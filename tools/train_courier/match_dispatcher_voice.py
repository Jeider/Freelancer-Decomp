"""Audit dispatcher identity and make small neutral voice-match previews offline."""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import time

from pydub import AudioSegment
from generate_evacuation_audio import Recorder,inspect
from generate_courier_ru import OUT,ASSETS,sha,save,transcribe

FOLDER=OUT/'voice_match'
SOURCES=[
    ('default/gcs_combat_announce_allclear_01-.mp3','Противников в радиусе базы не обнаружено.'),
    ('start/gcs_dockhail_dock_idreq_01-.mp3','Укажите направление вашего движения.'),
    ('middle/gcs_docklaunch_clear_berth_04-.mp3','Открываем шлюз, взлёт разрешен.'),
    ('middle/gcs_docklaunch_clear_moor_02-.mp3','Причал деактивирован.'),
]
CODES=('tc_board_04-','te_departed_01-','te_return_30_01-')


def audit():
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    selected={code:r for code,r in records.items() if r['bank'] in ('radio','evacuation')}
    mismatched=[]
    for code,row in selected.items():
        path=ASSETS.parent/'DATA/AUDIO/MOD/dispatcher01'/(code+'.wav')
        if not path.exists() or sha(path)!=row['sha256']:mismatched.append(code)
    report={'actors':dict(Counter(r['actor'] for r in selected.values())),
            'engines':dict(Counter(r['engine'] for r in selected.values())),
            'reference_hashes':dict(Counter(r['reference_sha256'] for r in selected.values())),
            'installed_wav_mismatches':mismatched}
    save(FOLDER/'audit.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


def prepare():
    combined=AudioSegment.empty();sources=[]
    for relative,text in SOURCES:
        path=ASSETS/'PILOTS/dispatcher01'/relative
        sound=AudioSegment.from_file(path).set_channels(1).set_frame_rate(24000).set_sample_width(2)
        gain=min(-18-sound.dBFS,-1-sound.max_dBFS)
        sound=sound.apply_gain(gain)
        if len(combined):combined+=AudioSegment.silent(duration=150,frame_rate=24000)
        combined+=sound
        sources.append({'path':str(path),'text':text,'sha256':sha(path),'seconds':len(sound)/1000})
    path=FOLDER/'reference_neutral.wav';combined.export(path,format='wav')
    info=inspect(path);assert 5<info['duration']<20
    report={'path':str(path),'text':' '.join(text for _,text in SOURCES),'sources':sources,
            'sha256':sha(path),**info}
    save(FOLDER/'reference_neutral.json',report)
    print('Neutral reference:',round(info['duration'],2),'seconds',flush=True)


def generate():
    reference=json.loads((FOLDER/'reference_neutral.json').read_text(encoding='utf-8'))
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    previews={}
    for code in CODES:
        # Preserve the message, reducing only punctuation-driven shouting.
        text=records[code]['text'].replace('!','.')
        form={'engine':'omnivoice','language':'ru','text':text,'ref_text':reference['text'],
              'seed':'42','speed':'1.0','denoise':'false','postprocess_output':'false',
              'pronounce':'false','num_step':'128','guidance_scale':'3.0'}
        print('Voice-match preview:',code,flush=True)
        start=time.time()
        with Recorder._client() as client,Path(reference['path']).open('rb') as audio:
            response=client.post('/generate',data=form,files={'ref_audio':('dispatcher.wav',audio,'audio/wav')})
        response.raise_for_status()
        assert not int(response.headers.get('X-OmniVoice-Dropped-Chunks','0')),code
        sound=AudioSegment.from_file(io.BytesIO(response.content),format='wav').set_channels(1).set_sample_width(2)
        if sound.max_dBFS>-.5:sound=sound.apply_gain(-.5-sound.max_dBFS)
        target=FOLDER/(code+'.wav');sound.export(target,format='wav')
        previews[code]={'request':form,'reference_sha256':reference['sha256'],'sha256':sha(target),
                        'seconds_to_generate':time.time()-start,**inspect(target)}
        previews[code]['asr']=transcribe(target)
        save(FOLDER/'previews.json',previews)
        print('ASR:',previews[code]['asr'].get('text'),flush=True)
    mixed=AudioSegment.empty();order=[]
    queue=[('original_reference',Path(reference['path']))]
    for code in CODES:
        queue += [('installed_'+code,ASSETS.parent/'DATA/AUDIO/MOD/dispatcher01'/(code+'.wav')),
                  ('neutral_preview_'+code,FOLDER/(code+'.wav'))]
    for label,path in queue:
        if len(mixed):mixed+=AudioSegment.silent(duration=900,frame_rate=24000)
        sound=AudioSegment.from_file(path).set_channels(1).set_frame_rate(24000)
        sound=sound.apply_gain(min(-18-sound.dBFS,-1-sound.max_dBFS))
        order.append({'label':label,'start_seconds':len(mixed)/1000,'duration':len(sound)/1000})
        mixed+=sound
    target=FOLDER/'comparison.wav';mixed.export(target,format='wav')
    save(FOLDER/'comparison.json',{'order':order,'sha256':sha(target)})
    print('Offline comparison:',target,flush=True)


if __name__=='__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('audit','prepare','generate'))
    args=parser.parse_args();FOLDER.mkdir(parents=True,exist_ok=True)
    {'audit':audit,'prepare':prepare,'generate':generate}[args.action]()
