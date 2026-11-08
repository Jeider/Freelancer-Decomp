"""Verify the installed Avalon dialogue and preserve it across catalog generation."""
import hashlib
import json
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True
from story.rpg.script import RpgScript
from managers.rpg_parking import install_parking_runtime, bind_parking_contact
from files.rpg_runtime import dialog_ini
from tools.data_folder import DataFolder
from generate import generate

script = RpgScript.load(PROJECT / 'story/rpg/rm0002.json')
folder = DataFolder(root=PROJECT.parent.parent)
output = ROOT / 'src/obj/ship_parking/avalon/verified'
report = install_parking_runtime(PROJECT, script, None, output, dry_run=True)
contact = folder.data_path('RPG/parking/br_avl_01_base.ini').read_bytes()
assert bind_parking_contact(contact, script) == contact
assert folder.data_path('RPG/rm0002_dialog.ini').read_bytes() == dialog_ini(script).encode('utf-8')
assert b'body = br_male_elite_body' in contact and b'head = br_captain_head' in contact
assert b'parking_base = br_avl_01_base' in folder.data_path('RPG/rm0002_dialog.ini').read_bytes()
catalog = json.loads(folder.data_path('SCRIPTS/RPG/rm0002/en/manifest.json').read_text(encoding='utf-8'))
assert len(catalog['fragments']) == len(script.fragments) and len(catalog['gestures']) == 16
for row in catalog['fragments']:
    with wave.open(str(folder.data_path(row['audio'])), 'rb') as audio:
        seconds = audio.getnframes() / audio.getframerate()
    assert abs(seconds - row['speech_seconds']) < .000001
    assert row['scene_seconds'] >= seconds
    assert row['sha256'] == hashlib.sha256(folder.data_path(row['path']).read_bytes()).hexdigest()
files, _ = generate(folder.get_root(), output / 'regeneration')
assert files['DATA/RPG/parking/br_avl_01_base.ini'] == contact
assert not folder.data_path('SCRIPTS/RPG/rm0002/ru/manifest.json').exists()
installed = folder.get_root() / 'bin/Content.dll'
built = ROOT / 'src/obj/train_courier/rpg1/bin/Content.dll'
assert hashlib.sha256(installed.read_bytes()).digest() == hashlib.sha256(built.read_bytes()).digest()
print('PASS: Avalon actor/contact, graph, all English WAV/THN durations, 16 gestures, installed Content.dll, and authored-contact preservation')
