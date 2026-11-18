"""Resume English evacuation recordings through the running local VoiceStudio."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import sys
import time
import wave

from evacuation_script import rows

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT/'out/train_courier/evacuation/audio_en'
sys.path.insert(0, str(PROJECT))
from tools.voicestudio import VoiceStudioClone
from pydub import AudioSegment
import settings
from audio.delivery import Delivery


class Recorder(VoiceStudioClone):
    @classmethod
    def cache_path(cls):
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT/'profiles.json'
        old = PROJECT/'results/voicestudio/profiles.json'
        if not path.exists() and old.exists():
            shutil.copy2(old, path)
        return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_name(row):
    return {'dispatcher': 'EngMaleDispatcher', 'vendor': 'RpgTradeDirector', 'player': 'Trent'}[row['speaker']]


def inspect(path):
    with wave.open(str(path), 'rb') as wav:
        channels, width, rate, frames, codec, _ = wav.getparams()
        raw = wav.readframes(frames)
    assert width == 2 and channels == 1 and codec == 'NONE' and frames and len(raw) == frames*2, path
    segment = AudioSegment(raw, frame_rate=rate, sample_width=width, channels=channels)
    samples = segment.get_array_of_samples()
    peak = max(abs(value) for value in samples)
    assert peak > 500 and math.isfinite(segment.dBFS) and segment.dBFS > -40, path
    assert sum(abs(value) >= 32760 for value in samples)/frames < .001, path
    return {'duration': frames/rate, 'rate': rate, 'channels': channels,
            'sample_bits': width*8, 'rms_dbfs': segment.dBFS, 'peak_dbfs': segment.max_dBFS}


def save_manifest(records):
    (OUT/'recordings.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids', nargs='*')
    parser.add_argument('--bar', action='store_true', help='Also record the eight prepared briefing lines')
    parser.add_argument('--revised', action='store_true', help='Only the revised post-exit reprimands')
    parser.add_argument('--transcribe', action='store_true', help='Check radio words with local ASR after generation')
    parser.add_argument('--retranscribe', action='store_true', help='Repeat ASR with silence padding; leave the recorded take unchanged')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    assert shutil.disk_usage(ROOT).free > 2*1024**3
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/'recordings.json'
    records = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    selected = [r for r in rows() if (args.bar or r['speaker']=='dispatcher') and
                (not args.ids or r['id'] in args.ids) and (not args.revised or r.get('delivery'))]
    for index, row in enumerate(selected, 1):
        name = actor_name(row)
        reference = Recorder.source_file(name, 'en')
        spec=row.get('delivery')
        delivery=Delivery(spec['code'],emo_vector=tuple(spec['emo_vector']),speed=spec['speed']) if spec else None
        signature_parts=[row['en'], name, sha(reference),settings.VOICESTUDIO_MODEL,
                         settings.VOICESTUDIO_STEPS,1.0,False,'full-sentence-no-trim-v1']
        if spec:signature_parts.append(spec)
        signature = hashlib.sha256(json.dumps(signature_parts,ensure_ascii=False).encode()).hexdigest()
        target = OUT/(row['id']+'.wav')
        old = records.get(row['id'], {})
        if args.force or not (target.exists() and old.get('signature')==signature and old.get('sha256')==sha(target)):
            started = time.time()
            raw = Recorder.generate_voice_bytes(None, row['en'], 'en', 'en', source_name=name, speed=1.0, denoise=False,delivery=delivery)
            sound = AudioSegment.from_file(io.BytesIO(raw), format='wav').set_channels(1).set_sample_width(2)
            # Keep native sample rate and voice loudness; prevent full-scale clips.
            if sound.max_dBFS > -.5:
                sound = sound.apply_gain(-.5-sound.max_dBFS)
            sound.export(target, format='wav')
            # Complete sentences can begin quietly ("You are..."). The legacy
            # fragment trimmer may discard that short first speech region.
            # Preserve the full generated take, including its short lead-in.
            info = inspect(target)
            words = len(re.findall(r"\b[\w']+\b", row['en']))
            assert .5 < info['duration'] < max(8, words*.85), (row['id'], info)
            records[row['id']] = {'id': row['id'], 'text': row['en'], 'speaker': row['speaker'],
                'source': str(reference), 'source_sha256': sha(reference), 'signature': signature,
                'sha256': sha(target), **info, 'generation_seconds': time.time()-started,'delivery':spec}
            save_manifest(records)
        print(f"[{index}/{len(selected)}] {row['id']} {records[row['id']]['duration']:.2f}s", flush=True)
        # Radio transcription is an audio-content check, not cutscene/gesture timing.
        if (args.transcribe or args.retranscribe) and row['speaker']=='dispatcher' and ('asr' not in records[row['id']] or args.retranscribe):
            if args.retranscribe:
                sound=AudioSegment.from_wav(target)
                silence=AudioSegment.silent(duration=500,frame_rate=sound.frame_rate)
                audio=io.BytesIO();(silence+sound+silence).export(audio,format='wav');audio.seek(0)
            else:
                audio=target.open('rb')
            with Recorder._client() as client, audio:
                response = client.post('/transcribe', data={'language':'en', 'mode':'reference', 'refine':'false'},
                                       files={'audio':(target.name, audio, 'audio/wav')})
            response.raise_for_status()
            if args.retranscribe and 'asr' in records[row['id']]:
                records[row['id']].setdefault('asr_previous',[]).append(records[row['id']]['asr'])
            records[row['id']]['asr'] = response.json()
            records[row['id']]['asr_padding_ms'] = 500 if args.retranscribe else 0
            save_manifest(records)
            print('ASR:', response.json().get('text', ''), flush=True)
    print('Recorded', len(records), 'English lines. No live DATA writes.', flush=True)


if __name__ == '__main__':
    main()
