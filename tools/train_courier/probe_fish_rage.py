"""Isolated Fish S2 Pro Russian emotion probe; no game or VoiceStudio edits."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_courier/evacuation/russian_emotion/fish_s2'
SOURCE=OUT/'source'
DEPS=OUT/'dependencies'
WEIGHTS=OUT/'weights'
REVISION='0f8a12e8a651062fdee9c33a894bdccd3a8513f1'
PYTHON=Path('C:/Users/Freel/AppData/Roaming/VoiceStudio/runtime/project/.venv/Scripts/python.exe')
UV=Path('C:/Users/Freel/AppData/Local/Programs/VoiceStudio/resources/tools/uv.exe')
# These optional inference imports are absent from the VoiceStudio environment.
# Install into a private target with --no-deps: its existing torch and packages
# remain read-only. Any additional missing import is handled explicitly.
EXTRA_PACKAGES=['hydra-core==1.3.2','omegaconf==2.3.0','antlr4-python3-runtime==4.9.3',
                'loguru','pyrootutils','einx==0.2.2','frozendict','ormsgpack',
                'descript-audio-codec','descript-audiotools','flatten-dict','randomname',
                'fire','pyloudnorm','torch-stft','julius','ffmpeg-python','natsort','resampy']
TEXT='Трент, ты куда собрался? Немедленно возвращайся в локомотив. У тебя одна минута!'
STYLES={'neutral':'[calm]','angry':'[angry]','rage':'[furious] [shouting]',
        'screaming':'[screaming]','screaming_uncloned':'[screaming]'}
SELECTED=list(STYLES)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def activate():
    sys.path[:0]=[str(DEPS),str(SOURCE)]
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['HF_HOME']=str(OUT/'tool_cache/huggingface')
    os.environ['TORCH_HOME']=str(OUT/'tool_cache/torch')
    os.environ['NUMBA_CACHE_DIR']=str(OUT/'tool_cache/numba')

def setup():
    OUT.mkdir(parents=True,exist_ok=True)
    assert shutil.disk_usage(OUT).free>25*1024**3,'Need at least 25 GiB free'
    marker=SOURCE/'probe_revision.txt'
    if not marker.exists():
        archive=OUT/'source.zip'
        url=f'https://codeload.github.com/fishaudio/fish-speech/zip/{REVISION}'
        print('Fetching pinned Fish Speech source',flush=True)
        with urllib.request.urlopen(url,timeout=90) as response,archive.open('wb') as target:
            shutil.copyfileobj(response,target)
        with zipfile.ZipFile(archive) as bundle:
            prefix=f'fish-speech-{REVISION}/'
            for info in bundle.infolist():
                assert info.filename.startswith(prefix),info.filename
                relative=Path(info.filename[len(prefix):])
                assert not relative.is_absolute() and '..' not in relative.parts,relative
                target=(SOURCE/relative).resolve()
                assert target==SOURCE.resolve() or SOURCE.resolve() in target.parents,target
                if info.is_dir():target.mkdir(parents=True,exist_ok=True)
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with bundle.open(info) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
        marker.write_text(REVISION,encoding='utf-8')
        (OUT/'source_manifest.json').write_text(json.dumps({'revision':REVISION,'url':url,'archive_sha256':sha(archive)},indent=2),encoding='utf-8')
        archive.unlink()
    assert marker.read_text(encoding='utf-8')==REVISION
    env=os.environ.copy();env['UV_CACHE_DIR']=str(OUT/'tool_cache/uv')
    subprocess.run([str(UV),'pip','install','--python',str(PYTHON),'--target',str(DEPS),'--no-deps',*EXTRA_PACKAGES],env=env,check=True)
    # Resolve absent dependencies only; never upgrade/remove the app's shared
    # packages. Upstream audiotools' old protobuf pin is not needed by inference.
    activate()
    import importlib.metadata as metadata
    from packaging.requirements import Requirement
    for _ in range(8):
        missing=set()
        for distribution in metadata.distributions(path=[str(DEPS)]):
            for raw in distribution.requires or []:
                requirement=Requirement(raw)
                if requirement.marker and not requirement.marker.evaluate():continue
                try:metadata.version(requirement.name)
                except metadata.PackageNotFoundError:missing.add(str(requirement))
        if not missing:break
        print('Adding absent dependencies:',sorted(missing),flush=True)
        subprocess.run([str(UV),'pip','install','--python',str(PYTHON),'--target',str(DEPS),'--no-deps',*sorted(missing)],env=env,check=True)
    else:raise RuntimeError('Dependency resolution did not converge')
    versions={d.metadata['Name']:d.version for d in metadata.distributions(path=[str(DEPS)])}
    (OUT/'dependency_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
    subprocess.run([str(PYTHON),'-u','-B',str(Path(__file__).resolve()),'check'],check=True)

def check():
    activate()
    import torch
    print('Torch',torch.__version__,flush=True)
    from fish_speech.models.text2semantic.inference import init_model,generate_long
    from fish_speech.models.dac.inference import load_model
    from fish_speech.models.dac.modded_dac import DAC
    from accelerate import init_empty_weights
    print('Fish inference imports passed',flush=True)
    if all((WEIGHTS/p).exists() for p in ('config.json','tokenizer.json','model.safetensors.index.json')):
        from fish_speech.models.text2semantic.llama import DualARTransformer,_remap_fish_qwen3_omni_keys
        with init_empty_weights(include_buffers=False):
            model=DualARTransformer.from_pretrained(str(WEIGHTS),load_weights=False,max_length=4096)
        assert all(p.is_meta for p in model.parameters()),'Preflight allocated real model parameters'
        assert not any(b.is_meta for b in model.buffers()),'Rotary buffers must be materialized'
        index=json.loads((WEIGHTS/'model.safetensors.index.json').read_text())['weight_map']
        source_keys=set(_remap_fish_qwen3_omni_keys(dict.fromkeys(index)))
        missing=set(model.state_dict())-source_keys
        assert not missing,missing
        report={'parameters':sum(p.numel() for p in model.parameters()),'max_seq_len':4096,
                'missing_checkpoint_keys':sorted(missing),'extra_checkpoint_keys':sorted(source_keys-set(model.state_dict()))}
        report['bf16_parameter_gib']=report['parameters']*2/1024**3
        (OUT/'architecture_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)

def download():
    activate()
    from huggingface_hub import HfApi,snapshot_download
    manifest=OUT/'model_manifest.json'
    revision=json.loads(manifest.read_text())['revision'] if manifest.exists() else None
    info=HfApi(token=False).model_info('fishaudio/s2-pro',revision=revision,files_metadata=True)
    names=[s.rfilename for s in info.siblings if s.rfilename.endswith(('.json','.safetensors','.pth','.txt','.jinja','.tiktoken'))]
    total=sum(s.size or 0 for s in info.siblings if s.rfilename in names)
    assert shutil.disk_usage(OUT).free>total+5*1024**3
    manifest.write_text(json.dumps({'repo':'fishaudio/s2-pro','revision':info.sha,'bytes':total,'files':names,
                                   'sizes':{s.rfilename:s.size for s in info.siblings if s.rfilename in names}},indent=2),encoding='utf-8')
    print('Downloading',round(total/1024**3,2),'GiB at',info.sha,flush=True)
    snapshot_download('fishaudio/s2-pro',revision=info.sha,local_dir=WEIGHTS,
                      allow_patterns=names,token=False,max_workers=4)
    print('Model downloaded',flush=True)

def prepare_reference():
    from pydub import AudioSegment
    parent=OUT.parent
    parts=[parent/'dispatcher_reference.wav',parent/'dispatcher_reference_urgent.wav']
    joined=AudioSegment.from_wav(parts[0])+AudioSegment.silent(duration=200,frame_rate=24000)+AudioSegment.from_wav(parts[1])
    path=OUT/'reference.wav'
    joined.set_channels(1).set_frame_rate(24000).set_sample_width(2).export(path,format='wav')
    text='Противников в радиусе базы не обнаружено. Противников в ближайшем радиусе не обнаружено. Запрос отклонён, вам запрещено находиться в этой зоне. Всем кораблям! Обнаружен неприятель! Код красный, приготовиться к обороне!'
    report={'text':text,'duration':len(joined)/1000,'sha256':sha(path),
            'sources':[{'path':str(p),'sha256':sha(p)} for p in parts]}
    (OUT/'reference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

def encode():
    activate()
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    from fish_speech.models.dac.inference import load_model
    prepare_reference()
    reference=json.loads((OUT/'reference.json').read_text(encoding='utf-8'))
    model_revision=json.loads((OUT/'model_manifest.json').read_text())['revision']
    signature=hashlib.sha256(json.dumps([reference['sha256'],model_revision,REVISION]).encode()).hexdigest()
    cache=OUT/'encode.json';tokens=OUT/'reference_tokens.npy'
    old=json.loads(cache.read_text()) if cache.exists() else {}
    if old.get('signature')==signature and tokens.exists() and old.get('sha256')==sha(tokens):
        print('Using verified reference tokens',flush=True)
        return
    torch.set_num_threads(8)
    with torch.inference_mode():
        model=load_model('modded_dac_vq',str(WEIGHTS/'codec.pth'),device='cuda')
        data,rate=sf.read(OUT/'reference.wav',dtype='float32')
        signal=torch.from_numpy(data).reshape(1,-1)
        signal=torchaudio.functional.resample(signal,rate,model.sample_rate)[None].to('cuda')
        codes,_=model.encode(signal,torch.tensor([signal.shape[-1]],device='cuda',dtype=torch.long))
        np.save(tokens,codes[0].cpu().numpy())
        cache.write_text(json.dumps({'signature':signature,'sha256':sha(tokens),'shape':list(codes.shape),
                                    'peak_gpu_gib':torch.cuda.max_memory_allocated()/1024**3},indent=2),encoding='utf-8')
        print('Reference encoded',tuple(codes.shape),'GPU peak GiB',torch.cuda.max_memory_allocated()/1024**3,flush=True)

def synthesize():
    activate()
    import numpy as np
    import torch
    from accelerate import init_empty_weights
    from fish_speech.models.text2semantic.llama import DualARTransformer,_remap_fish_qwen3_omni_keys
    from fish_speech.models.text2semantic.inference import decode_one_token_ar,generate_long
    from safetensors.torch import load_file
    from collections import OrderedDict
    torch.set_num_threads(8)
    reference=json.loads((OUT/'reference.json').read_text(encoding='utf-8'))
    prompt_tokens=torch.from_numpy(np.load(OUT/'reference_tokens.npy'))
    free,total=torch.cuda.mem_get_info()
    assert free>11*1024**3,f'Need 11 GiB free for this short probe, have {free/1024**3:.2f}'
    print('Loading S2 Pro with a 4096-token context; no weight quantization',flush=True)
    # Empty CPU parameters avoid allocating a redundant 20 GB random model.
    # Nonpersistent rotary buffers remain real. Assign checkpoint parameters
    # outside the empty-weights context so Accelerate cannot turn them meta again.
    with init_empty_weights(include_buffers=False):
        model=DualARTransformer.from_pretrained(str(WEIGHTS),load_weights=False,max_length=4096)
    weight_map=json.loads((WEIGHTS/'model.safetensors.index.json').read_text())['weight_map']
    weights=OrderedDict()
    for shard in sorted(set(weight_map.values())):weights.update(load_file(str(WEIGHTS/shard),device='cpu'))
    result=model.load_state_dict(_remap_fish_qwen3_omni_keys(weights),strict=False,assign=True)
    assert not result.missing_keys,result
    print('Checkpoint status',result,flush=True)
    del weights
    assert not any(p.is_meta for p in model.parameters()),'Unloaded model parameter'
    model=model.to(device='cuda',dtype=torch.bfloat16).eval()
    model._cache_setup_done=False
    records={}
    manifest=OUT/'generation.json'
    model_revision=json.loads((OUT/'model_manifest.json').read_text())['revision']
    if manifest.exists():records=json.loads(manifest.read_text(encoding='utf-8'))
    with torch.inference_mode():
        for style in SELECTED:
            tags=STYLES[style]
            target=OUT/(style+'_tokens.npy')
            request={'text':'<|speaker:0|>'+tags+' '+TEXT,'seed':42,'temperature':0.7,'top_p':0.7,'top_k':30,
                     'max_new_tokens':384,'max_seq_len':4096,'reference_sha256':reference['sha256'],
                     'reference_text':reference['text'],'source_revision':REVISION,'model_revision':model_revision}
            if style.startswith('screaming'):
                request['text']='<|speaker:0|>[screaming] Трент! Ты куда собрался?! [screaming] Немедленно возвращайся в локомотив! [screaming] У тебя одна минута!'
            if style.endswith('_uncloned'):
                request['reference_sha256']=None
                request['reference_text']=None
            signature=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
            old=records.get(style,{})
            if target.exists() and old.get('signature')==signature and old.get('tokens_sha256')==sha(target):continue
            torch.manual_seed(42);torch.cuda.manual_seed_all(42)
            started=time.time();parts=[]
            print('Generating Fish',style,flush=True)
            for result in generate_long(model=model,device='cuda',decode_one_token=decode_one_token_ar,
                                        text=request['text'],prompt_text=[reference['text']] if request['reference_text'] else None,
                                        prompt_tokens=[prompt_tokens] if request['reference_text'] else None,
                                        num_samples=1,max_new_tokens=384,top_p=0.7,top_k=30,temperature=0.7,
                                        compile=False,iterative_prompt=False,chunk_length=1000):
                if result.action=='sample':parts.append(result.codes.cpu())
            assert parts,'No audio codes produced'
            codes=torch.cat(parts,dim=1)
            assert 5<codes.shape[-1]<384,('Empty or truncated output',codes.shape)
            np.save(target,codes.numpy())
            records[style]={'request':request,'signature':signature,'tokens_sha256':sha(target),
                            'frames':codes.shape[-1],'generation_seconds':time.time()-started,
                            'peak_gpu_gib':torch.cuda.max_memory_allocated()/1024**3}
            manifest.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
            print(style,'frames',codes.shape[-1],'seconds',records[style]['generation_seconds'],flush=True)

def decode():
    activate()
    import numpy as np
    import soundfile as sf
    import torch
    from fish_speech.models.dac.inference import load_model
    torch.set_num_threads(8)
    records=json.loads((OUT/'decode.json').read_text()) if (OUT/'decode.json').exists() else {}
    with torch.inference_mode():
        model=load_model('modded_dac_vq',str(WEIGHTS/'codec.pth'),device='cuda')
        for style in SELECTED:
            tokens=torch.from_numpy(np.load(OUT/(style+'_tokens.npy'))).long().to('cuda')[None]
            sound=model.from_indices(tokens)[0,0].float().cpu().numpy()
            assert np.isfinite(sound).all(),'Nonfinite decoded audio'
            peak=float(np.max(np.abs(sound)))
            gain=min(1.0,10**(-1/20)/max(peak,1e-12))
            sound*=gain
            sf.write(OUT/(style+'.wav'),sound,model.sample_rate,subtype='PCM_16')
            records[style]={'raw_float_peak':peak,'gain':gain,'rate':model.sample_rate,'duration':len(sound)/model.sample_rate}
            print('Decoded',style,len(sound)/model.sample_rate,'seconds',flush=True)
    (OUT/'decode.json').write_text(json.dumps(records,indent=2),encoding='utf-8')

def review():
    # ASR runs after the Fish GPU subprocesses have exited.
    from probe_russian_emotion import transcribe,words,inspect
    from pydub import AudioSegment
    manifest=OUT/'review.json'
    records=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    comparison=AudioSegment.empty();order=[]
    for style in SELECTED:
        path=OUT/(style+'.wav')
        old=records.get(style,{})
        result=old['asr'] if old.get('sha256')==sha(path) else transcribe(path)
        match=words(result.get('text',''))==words(TEXT)
        records[style]={'sha256':sha(path),'asr':result,'asr_words_match':match,**inspect(path)}
        print(style,'ASR:',result.get('text'),flush=True)
        if match:
            segment=AudioSegment.from_wav(path)
            gain=min(-16-segment.dBFS,-2-segment.max_dBFS)
            if len(comparison):comparison+=AudioSegment.silent(duration=1000,frame_rate=segment.frame_rate)
            order.append({'style':style,'start_seconds':len(comparison)/1000,'gain_db':gain})
            comparison+=segment.apply_gain(gain)
    manifest.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    if order:
        comparison.export(OUT/'comparison.wav',format='wav')
        (OUT/'comparison.json').write_text(json.dumps({'order':order,'sha256':sha(OUT/'comparison.wav'),**inspect(OUT/'comparison.wav')},indent=2),encoding='utf-8')

def generate():
    manifest=json.loads((OUT/'model_manifest.json').read_text(encoding='utf-8'))
    assert all((WEIGHTS/p).exists() for p in manifest['files']),'Model download incomplete'
    if manifest.get('sizes'):
        assert all((WEIGHTS/p).stat().st_size==size for p,size in manifest['sizes'].items()),'Model size mismatch'
    for stage in ('encode','synthesize','decode','review'):
        subprocess.run([str(PYTHON),'-u','-B',str(Path(__file__).resolve()),stage,'--styles',*SELECTED],check=True)

def wait_generate():
    deadline=time.monotonic()+3600
    last_notice=0
    while True:
        manifest=json.loads((OUT/'model_manifest.json').read_text(encoding='utf-8'))
        ready=[p for p in manifest['files'] if (WEIGHTS/p).exists()]
        if len(ready)==len(manifest['files']):break
        assert time.monotonic()<deadline,'Model download exceeded one hour'
        if time.monotonic()-last_notice>55:
            print('Waiting for weights:',len(ready),'/',len(manifest['files']),'files',flush=True)
            last_notice=time.monotonic()
        time.sleep(15)
    generate()

def main():
    global SELECTED
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('setup','check','download','encode','synthesize','decode','review','generate','wait_generate'))
    p.add_argument('--styles',nargs='+',choices=list(STYLES),default=['neutral','angry','rage'])
    a=p.parse_args()
    SELECTED=a.styles
    globals()[a.action]()

if __name__=='__main__':main()
