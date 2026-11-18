"""Local VoiceStudio Russian emotion probe; never writes to game assets."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import time

from pydub import AudioSegment

from generate_evacuation_audio import Recorder,inspect

OUT=Path(__file__).resolve().parents[2]/'out/train_courier/evacuation/russian_emotion'
REFERENCE_DIR=Path('D:/Games/FL_MOD/Assets/PILOTS/dispatcher01/default')
REFERENCE_PARTS=('gcs_combat_announce_allclear_01-.mp3','gcs_combat_announce_allclear_03-.mp3')
REFERENCE_TEXT='Противников в радиусе базы не обнаружено. Противников в ближайшем радиусе не обнаружено.'
REFERENCES={
    'neutral':(REFERENCE_PARTS,REFERENCE_TEXT),
    'urgent':(('gcs_dockrequest_responsehostile_01-.mp3','gcs_combat_announce_engage_03-.mp3'),
              'Запрос отклонён, вам запрещено находиться в этой зоне. Всем кораблям! Обнаружен неприятель! Код красный, приготовиться к обороне!'),
}
TEXT='Трент, ты куда собрался? Немедленно возвращайся в локомотив. У тебя одна минута!'
RAGE_DIRECTION='请用俄语说话。极其愤怒，暴怒地大声怒吼，严厉斥责对方！声音紧绷、粗粝，有爆发力，重重强调命令，句间有短促的停顿。保持正常语速，不要加快。'
STYLES={
    'neutral':'Please speak calmly and neutrally.',
    # The anger instruction included in upstream CosyVoice's instruct_list.
    'angry':'请非常生气地说一句话。',
    'angry_en':'Speak in Russian with strong anger. Scold the listener sharply and demand an immediate return.',
    # No instruct: the sidecar uses inference_zero_shot with the Russian
    # transcript AND reference speech tokens, unlike inference_instruct2.
    'zero_shot':None,
    'angry_ru':'Говори по-русски, с естественным русским произношением. Очень сердито и резко потребуй немедленно вернуться.',
    'rage_instruct':RAGE_DIRECTION,
    # Experimental combination: the direction occupies the system portion
    # of the zero-shot prompt, before the transcript boundary. This keeps
    # the Russian LLM speech tokens that instruct2 normally removes.
    'rage_context':None,
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare_reference(reference_set='neutral'):
    OUT.mkdir(parents=True,exist_ok=True)
    reference=OUT/('dispatcher_reference'+('' if reference_set=='neutral' else '_'+reference_set)+'.wav')
    joined=AudioSegment.empty()
    sources=[]
    for name in REFERENCES[reference_set][0]:
        source=REFERENCE_DIR/name
        sound=AudioSegment.from_file(source).set_channels(1).set_frame_rate(24000).set_sample_width(2)
        if len(joined):joined+=AudioSegment.silent(duration=200,frame_rate=24000)
        joined+=sound
        sources.append({'path':str(source),'sha256':sha(source)})
    joined.export(reference,format='wav')
    return reference,sources


def transcribe(path):
    with Recorder._client() as client,path.open('rb') as stream:
        response=client.post('/transcribe',data={'language':'ru','mode':'reference','refine':'false'},
                             files={'audio':(path.name,stream,'audio/wav')})
    response.raise_for_status()
    return response.json()


def wait_for_install(wait):
    deadline=time.monotonic()+3600
    last_notice=0
    with Recorder._client() as client:
        while True:
            response=client.get('/engines/sidecar/cosyvoice/install/status',timeout=30)
            response.raise_for_status()
            state=response.json()
            (OUT/'cosyvoice_install.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
            if state.get('installed'):return
            job=state.get('job') or {}
            assert job.get('state')!='failed',job.get('error')
            assert wait and job.get('state')=='running','Wait for the managed CosyVoice installation to finish'
            assert time.monotonic()<deadline,'Installation has exceeded one hour'
            if time.monotonic()-last_notice>=55:
                print('Waiting for model installation:',json.dumps(job.get('weights_progress')),flush=True)
                last_notice=time.monotonic()
            time.sleep(15)


def words(text):return re.findall(r'\w+',text.lower().replace('ё','е'))


def compare_accent():
    """Original Russian acting, then two copies conditioned on that acting."""
    manifest=OUT/'probes.json'
    report=json.loads(manifest.read_text(encoding='utf-8'))
    for name,record in report.items():
        record['asr_words_match']=words(record['request']['text'])==words(record['asr'].get('text',''))
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    reference=OUT/'dispatcher_reference_urgent.wav'
    reference_report=json.loads((OUT/'reference_urgent.json').read_text(encoding='utf-8'))
    assert sha(reference)==reference_report['sha256']
    entries=[('Original Russian reference',reference)]
    for name in ('cosyvoice_zero_shot_urgent_ref','omnivoice_zero_shot_urgent_ref'):
        path=OUT/(name+'.wav')
        assert report[name]['asr_words_match'] and sha(path)==report[name]['sha256'],name
        entries.append((name,path))
    combined=AudioSegment.empty()
    order=[]
    for label,path in entries:
        if len(combined):combined+=AudioSegment.silent(duration=1000,frame_rate=24000)
        segment=AudioSegment.from_wav(path).set_frame_rate(24000).set_channels(1).set_sample_width(2)
        # Compare voice and pronunciation without the original recording's
        # higher overall level favouring it. Original files are untouched.
        gain=min(-16-segment.dBFS,-2-segment.max_dBFS)
        segment=segment.apply_gain(gain)
        order.append({'label':label,'start_seconds':len(combined)/1000,'source_sha256':sha(path),'gain_db':gain})
        combined+=segment
    target=OUT/'accent_reference_comparison.wav'
    combined.export(target,format='wav')
    (OUT/'accent_reference_comparison.json').write_text(json.dumps({'order':order,'sha256':sha(target),**inspect(target)},indent=2),encoding='utf-8')
    print(target)


def generate(styles,wait=False,comparison_name='comparison',engine='cosyvoice',reference_set='neutral'):
    OUT.mkdir(parents=True,exist_ok=True)
    if engine=='cosyvoice':wait_for_install(wait)
    reference,sources=prepare_reference(reference_set)
    def take_name(style):return engine+'_'+style+('' if reference_set=='neutral' else '_'+reference_set+'_ref')
    manifest=OUT/'probes.json'
    report=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    def save():manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for style in styles:
        name=take_name(style)
        path=OUT/(name+'.wav')
        form={'engine':engine,'language':'ru','text':TEXT,
              'ref_text':REFERENCES[reference_set][1],
              'seed':'42','speed':'1.0','denoise':'false','postprocess_output':'false','pronounce':'false'}
        if STYLES[style]:form['instruct']=STYLES[style]
        if style=='rage_context':
            form['ref_text']='You are a helpful assistant. '+RAGE_DIRECTION+'<|endofprompt|>'+REFERENCES[reference_set][1]
        signature=hashlib.sha256(json.dumps([form,sha(reference)],sort_keys=True).encode()).hexdigest()
        old=report.get(name,{})
        if not (path.exists() and old.get('signature')==signature and old.get('sha256')==sha(path)):
            print('Generating',name,flush=True)
            started=time.time()
            with Recorder._client() as client,reference.open('rb') as stream:
                response=client.post('/generate',data=form,files={'ref_audio':(reference.name,stream,'audio/wav')})
            if response.status_code!=200:
                print(response.text[:2000],flush=True)
            response.raise_for_status()
            assert not int(response.headers.get('X-OmniVoice-Dropped-Chunks','0')),dict(response.headers)
            sound=AudioSegment.from_file(io.BytesIO(response.content),format='wav').set_channels(1).set_sample_width(2)
            if sound.max_dBFS>-.5:sound=sound.apply_gain(-.5-sound.max_dBFS)
            sound.export(path,format='wav')
            info=inspect(path)
            assert 1<info['duration']<25,info
            report[name]={'request':form,'signature':signature,'sha256':sha(path),
                          'response_headers':{key:value for key,value in response.headers.items() if key.startswith('x-')},
                          'reference_sources':sources,'reference_sha256':sha(reference),
                          'generation_seconds':time.time()-started,**info}
            save()
        if 'asr' not in report[name]:
            report[name]['asr']=transcribe(path);save()
        report[name]['asr_words_match']=words(TEXT)==words(report[name]['asr'].get('text',''))
        save()
        print(name,report[name]['duration'],'seconds; ASR:',report[name]['asr'].get('text'),flush=True)
        if not report[name]['asr_words_match']:print('Rejected from comparison: transcript mismatch',flush=True)
    comparison=AudioSegment.empty()
    order=[]
    for style in styles:
        name=take_name(style)
        if not report[name]['asr_words_match']:continue
        if len(comparison):comparison+=AudioSegment.silent(duration=1000,frame_rate=24000)
        segment=AudioSegment.from_wav(OUT/(name+'.wav'))
        gain=min(-16-segment.dBFS,-2-segment.max_dBFS)
        order.append({'probe':name,'start_seconds':len(comparison)/1000,'sha256':report[name]['sha256'],'gain_db':gain})
        comparison+=segment.apply_gain(gain)
    path=OUT/(comparison_name+'.wav')
    assert order,'No takes passed the transcript check'
    comparison.export(path,format='wav')
    (OUT/(comparison_name+'.json')).write_text(json.dumps({'order':order,'sha256':sha(path),**inspect(path)},indent=2),encoding='utf-8')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('install','status','generate','reference','compare_accent'))
    parser.add_argument('--styles',nargs='+',choices=tuple(STYLES),default=['neutral','angry','angry_en'])
    parser.add_argument('--comparison',default='comparison',help='Comparison basename; keep rejected rounds intact')
    parser.add_argument('--engine',choices=('cosyvoice','omnivoice'),default='cosyvoice')
    parser.add_argument('--reference-set',choices=tuple(REFERENCES),default='neutral')
    parser.add_argument('--wait',action='store_true',help='Generate once the ongoing managed installation completes')
    args=parser.parse_args()
    if args.action=='compare_accent':
        compare_accent()
        return
    if args.action=='reference':
        reference,sources=prepare_reference(args.reference_set)
        report={'sources':sources,'sha256':sha(reference),**inspect(reference),'asr':transcribe(reference)}
        (OUT/('reference'+('' if args.reference_set=='neutral' else '_'+args.reference_set)+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=True,indent=2))
        return
    if args.action=='generate':
        assert Path(args.comparison).name==args.comparison and re.fullmatch(r'[a-z0-9_]+',args.comparison)
        assert args.engine=='cosyvoice' or args.styles==['zero_shot'],'OmniVoice baseline must not imply emotion control'
        generate(args.styles,args.wait,args.comparison,args.engine,args.reference_set)
        return
    with Recorder._client() as client:
        if args.action=='install':
            assert shutil.disk_usage('C:/').free>25*1024**3,'Insufficient disk space'
            response=client.post('/engines/sidecar/cosyvoice/install')
        else:
            response=client.get('/engines/sidecar/cosyvoice/install/status')
        response.raise_for_status()
        data=response.json()
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'cosyvoice_install.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        if args.action=='status' and data.get('job'):
            job=data['job']
            data={'installed':data.get('installed'),'state':job.get('state'),
                  'steps':{step['id']:step['state'] for step in job.get('steps',[])},
                  'log':job.get('log',[])[-5:],'weights_progress':job.get('weights_progress'),
                  'error':job.get('error'),'remediation':job.get('remediation')}
        print(json.dumps(data,ensure_ascii=True,indent=2))

if __name__=='__main__':main()
