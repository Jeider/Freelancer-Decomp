"""Generate one short local VoiceStudio PCM WAV sample using an existing Trent profile."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT))
spec = importlib.util.spec_from_file_location('pcm_probe', ROOT / 'out/voicestudio_pcm/payload/tools/voicestudio.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
V = module.VoiceStudioClone
V.assets_root = staticmethod(lambda: PROJECT.parent)
source = V.source_file('Trent', 'en')
cache = json.loads((PROJECT / 'results/voicestudio/profiles.json').read_text(encoding='utf-8'))
key = 'Trent|en|' + hashlib.sha1(source.read_bytes()).hexdigest()
profile = cache.get(key)
if not profile:
    raise SystemExit('No existing matching Trent EN profile; probe stopped without cloning')
with V._client() as client:
    response = client.get('/profiles/' + profile)
    response.raise_for_status()
V._profile_id = classmethod(lambda cls, client, source_name, source_lang, source: profile)
from story.actors import Trent
path = V.generate_sound(Trent, 'This is a PCM recording test.',
                        ROOT / 'out/voicestudio_pcm/pcm_test.wav', source_lang='en')
with wave.open(str(path), 'rb') as wav:
    assert wav.getsampwidth() == 2 and wav.getcomptype() == 'NONE'
    print(f'PASS: real VoiceStudio response -> PCM16 WAV; {wav.getframerate()} Hz, '
          f'{wav.getnchannels()} channel(s), {wav.getnframes()/wav.getframerate():.3f} s; {path}')
