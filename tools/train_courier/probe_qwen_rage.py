"""Isolated Russian acting test with Qwen VoiceDesign; no game/app writes."""
import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/train_courier/evacuation/russian_emotion/qwen_design'
DEPS = OUT / 'dependencies'
WEIGHTS = OUT / 'weights'
PYTHON = Path('C:/Users/Freel/AppData/Roaming/VoiceStudio/runtime/project/.venv/Scripts/python.exe')
UV = Path('C:/Users/Freel/AppData/Local/Programs/VoiceStudio/resources/tools/uv.exe')
MODEL = 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
REVISION = '5ecdb67327fd37bb2e042aab12ff7391903235d3'
TEXT = 'Трент! Ты совсем с ума сошёл?! Немедленно вернись в локомотив! Ещё минута — и за этот груз ответишь лично!'
PERSONA = ('A middle-aged native Russian male, a rough deep baritone, a seasoned cargo dispatcher. '
           'Speak Russian with natural native Russian pronunciation. ')
TAKES = {
    'neutral': PERSONA + 'Read the words calmly and evenly, with a relaxed voice and neutral delivery.',
    'furious': PERSONA + ('He has just discovered that a pilot abandoned his crew and cargo. '
                         'He explodes in uncontrollable rage, furiously yelling directly at the pilot. '
                         'Raw strained chest voice, growling edges, explosive consonants, wide pitch changes. '
                         'Hammer the commands, bite off the accusation, take angry breaths between sentences. '
                         'Furious dramatic acting, at a measured pace with emphatic pauses.'),
    'furious_zh': PERSONA + ('极度暴怒的中年男性，声音低沉粗粝，失去耐心，正在痛斥逃跑的下属。'
                            '怒吼！每个命令都像砸出来一样，咬牙切齿，声音紧绷，带沙哑破音，'
                            '音调强烈起伏，句间有愤怒的呼吸和停顿。不是平静播报，要有真实的暴怒表演。'
                            '用母语般自然的俄语发音，语速不要加快。'),
}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def activate():
    sys.path.insert(0, str(DEPS))
    os.environ['HF_HOME'] = str(OUT / 'tool_cache/huggingface')
    os.environ['NUMBA_CACHE_DIR'] = str(OUT / 'tool_cache/numba')
    os.environ['TORCH_HOME'] = str(OUT / 'tool_cache/torch')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def setup():
    assert shutil.disk_usage(OUT).free > 12 * 1024**3, 'Need 12 GiB free'
    env = os.environ.copy()
    env['UV_CACHE_DIR'] = str(OUT / 'tool_cache/uv')
    packages = ['qwen-tts==0.1.1', 'transformers==4.57.3', 'accelerate==1.12.0',
                'huggingface-hub==0.36.0', 'librosa==0.11.0', 'sox==1.5.0']
    command = [str(UV), 'pip', 'install', '--python', str(PYTHON), '--target', str(DEPS), '--no-deps']
    subprocess.run(command + packages, env=env, check=True)
    activate()
    from packaging.requirements import Requirement
    for _ in range(8):
        missing = set()
        for dist in metadata.distributions(path=[str(DEPS)]):
            for raw in dist.requires or []:
                req = Requirement(raw)
                if req.marker and not req.marker.evaluate():
                    continue
                try:
                    metadata.version(req.name)
                except metadata.PackageNotFoundError:
                    missing.add(str(req))
        if not missing:
            break
        print('Adding absent packages:', sorted(missing), flush=True)
        subprocess.run(command + sorted(missing), env=env, check=True)
    else:
        raise RuntimeError('Missing-dependency resolution did not converge')
    save('dependency_versions.json', {d.metadata['Name']: d.version for d in metadata.distributions(path=[str(DEPS)])})
    subprocess.run([str(PYTHON), '-u', '-B', str(Path(__file__).resolve()), 'check'], check=True)


def download():
    # Use the existing host hub client; private transformers needs an older hub.
    os.environ['HF_HOME'] = str(OUT / 'tool_cache/huggingface')
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    from huggingface_hub import HfApi, snapshot_download
    info = HfApi(token=False).model_info(MODEL, revision=REVISION, files_metadata=True)
    files = {f.rfilename: f.size for f in info.siblings
             if f.rfilename.endswith(('.json', '.txt', '.safetensors'))}
    needed = sum(files.values())
    assert shutil.disk_usage(OUT).free > needed + 4 * 1024**3
    print('Pinned model:', REVISION, 'GiB:', round(needed / 1024**3, 2), flush=True)
    save('download_plan.json', {'model': MODEL, 'revision': REVISION, 'files': files})
    snapshot_download(MODEL, revision=REVISION, local_dir=WEIGHTS, allow_patterns=list(files),
                      token=False, max_workers=3)
    for name, size in files.items():
        assert (WEIGHTS / name).stat().st_size == size, name
    save('model_manifest.json', {'model': MODEL, 'revision': REVISION, 'files': files})


def check():
    activate()
    from qwen_tts import Qwen3TTSModel
    import torch
    print('Qwen imports OK; torch:', torch.__version__, 'CUDA:', torch.cuda.is_available(), flush=True)


def generate(names, without_name=False):
    activate()
    os.environ['HF_HUB_OFFLINE'] = '1'
    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel
    from transformers import set_seed
    assert (OUT / 'model_manifest.json').exists(), 'Download weights first'
    assert torch.cuda.mem_get_info()[0] > 7 * 1024**3, 'Need 7 GiB free VRAM'
    torch.set_num_threads(8)
    model = Qwen3TTSModel.from_pretrained(str(WEIGHTS), device_map='cuda:0',
                                         dtype=torch.bfloat16, attn_implementation='sdpa',
                                         local_files_only=True)
    manifest = OUT / 'generation.json'
    records = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    for style in names:
        name = style + ('_direct' if without_name else '')
        request = {'text': TEXT.removeprefix('Трент! ') if without_name else TEXT,
                   'language': 'Russian', 'instruct': TAKES[style],
                   'max_new_tokens': 480, 'temperature': 0.9, 'top_k': 50, 'top_p': 1.0}
        signature = hashlib.sha256(json.dumps([REVISION, request, 42], sort_keys=True).encode()).hexdigest()
        path = OUT / (name + '.wav')
        old = records.get(name, {})
        if path.exists() and old.get('signature') == signature and old.get('sha256') == sha(path):
            continue
        set_seed(42)
        started = time.monotonic()
        print('Generating:', name, flush=True)
        with torch.inference_mode():
            waves, rate = model.generate_voice_design(**request)
        signal = np.asarray(waves[0], dtype=np.float32)
        assert np.isfinite(signal).all()
        duration = len(signal) / rate
        assert 2 < duration < 35, duration
        peak = float(np.max(np.abs(signal)))
        gain = min(1.0, 10 ** (-1 / 20) / max(peak, 1e-8))
        sf.write(path, signal * gain, rate, subtype='PCM_16')
        records[name] = {'request': request, 'seed': 42, 'model_revision': REVISION,
                         'signature': signature, 'sha256': sha(path), 'duration': duration,
                         'rate': rate, 'native_peak': peak, 'peak_guard_gain': gain,
                         'elapsed': time.monotonic() - started,
                         'peak_gpu_gib': torch.cuda.max_memory_allocated() / 1024**3}
        save('generation.json', records)
        print(name, round(duration, 3), 'seconds', flush=True)
    save('runtime.json', {'script_sha256': sha(Path(__file__)), 'torch': torch.__version__,
                          **{p: metadata.version(p) for p in ('qwen-tts', 'transformers', 'accelerate')}})


def review(names, without_name=False):
    # Separate process: generation frees GPU before the local ASR check.
    from probe_russian_emotion import transcribe, words
    from pydub import AudioSegment
    records = json.loads((OUT / 'generation.json').read_text(encoding='utf-8'))
    report_file = OUT / 'review.json'
    report = json.loads(report_file.read_text(encoding='utf-8')) if report_file.exists() else {}
    combined = AudioSegment.empty()
    order = []
    for style in names:
        name = style + ('_direct' if without_name else '')
        path = OUT / (name + '.wav')
        digest = sha(path)
        assert digest == records[name]['sha256']
        if report.get(name, {}).get('sha256') != digest:
            asr = transcribe(path)
            report[name] = {'sha256': digest, 'asr': asr,
                            'words_match': words(records[name]['request']['text']) == words(asr.get('text', ''))}
            save('review.json', report)
        print(name, 'ASR:', report[name]['asr'].get('text'), flush=True)
        if not report[name]['words_match']:
            print('Excluded from comparison: words do not match', flush=True)
            continue
        sound = AudioSegment.from_wav(path).set_channels(1).set_frame_rate(24000)
        gain = min(-16 - sound.dBFS, -2 - sound.max_dBFS)
        if len(combined):
            combined += AudioSegment.silent(duration=1000, frame_rate=24000)
        order.append({'take': name, 'start_seconds': len(combined) / 1000, 'gain_db': gain, 'sha256': digest})
        combined += sound.apply_gain(gain)
    if order:
        basename = 'comparison_direct' if without_name else 'comparison'
        path = OUT / (basename + '.wav')
        combined.export(path, format='wav')
        save(basename + '.json', {'order': order, 'duration': len(combined) / 1000, 'sha256': sha(path)})
        print('Comparison:', path, flush=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('setup', 'check', 'download', 'generate', 'review'))
    parser.add_argument('--takes', nargs='+', choices=list(TAKES), default=list(TAKES))
    parser.add_argument('--without-name', action='store_true', help='Separate takes without the English proper name')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.action in ('generate', 'review'):
        globals()[args.action](args.takes, args.without_name)
    else:
        globals()[args.action]()


if __name__ == '__main__':
    main()
