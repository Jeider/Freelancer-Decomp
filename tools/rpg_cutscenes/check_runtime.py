"""Validate the engine INI/contact adapter against installed scenes without game writes."""
import argparse
from pathlib import Path
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
project = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path[:0] = [str(source), str(project)]
sys.dont_write_bytecode = True
from story.rpg.script import RpgScript
from managers.rpg_runtime import install_runtime
from files.rpg_runtime import bind_contact, dialog_ini, SESSION_THN
from tools.data_folder import DataFolder
script = RpgScript.load(source / 'story/rpg/rm0001.json')
original = (project.parent.parent / 'DATA/RPG/rh_biz_contact.ini').read_bytes()
bound = bind_contact(original)
assert bind_contact(bound) == bound
assert b'click_script' not in bound and b'[DialogChoice]' not in bound
assert b'dialog = RPG\\rm0001_dialog.ini' in bound
assert b'npc = rpg_biz_contact' in bound and b'affiliation = rh_grp' in bound
assert b'body = rh_commtrader_body' in bound and b'prop_hat_male_rh_elite' not in bound
ini = dialog_ini(script)
assert ini.count('[DialogNode]') == 13
assert 'nickname = tutorial\n' in ini and 'nickname = coupling\n' in ini
available = {row['id'] for row in script.fragments[:21]}
partial = dialog_ini(script, available)
assert 'fragment = rm0001_frag0022' not in partial
assert 'fragment = rm0001_frag0003' not in partial
assert 'fragment = rm0001_frag0001\n' in partial
assert 'лицензии' in partial and 'пятнадцати метров' in partial
for n in (2, 5, 10, 20):
    assert f'first_wagons = {n}\n' in ini
assert 'escape = resume' in ini
assert 'minimum_reputation = 0\n' in ini and 'reputation_strict = 1\n' in ini
assert SESSION_THN.count('ATTACH_ENTITY') == 1
assert SESSION_THN.count('START_IK') == 4
assert SESSION_THN.count('end_effector="Body_Head"') == 2
assert SESSION_THN.count('end_effector="Eye IK Left"') == 2
assert 'type=SCENE' not in SESSION_THN and 'RpgCamera_vendor' in SESSION_THN
out = Path(__file__).resolve().parents[2] / 'out/rpg_cutscenes/runtime_check'
report = install_runtime(project, script, None, out, dry_run=True)
assert len(report['files']) == 3
# A changed text must never reuse old recorded words, even when its ID is retained.
script.fragments[0]['en'] += ' Changed.'
changed = install_runtime(project, script, None, out / 'changed_text', dry_run=True)
assert script.fragments[0]['id'] in changed['pending_voice_fragments']
script.fragments[0]['en'] = script.fragments[0]['en'].removesuffix(' Changed.')
with tempfile.TemporaryDirectory(dir=out) as temporary:
    root = Path(temporary)
    folder = DataFolder(root=root / 'game')
    previous = original + b'; previous installation\r\n'
    folder.sync_data_file('RPG/rh_biz_contact.ini', previous)
    files = {'RPG/rh_biz_contact.ini': bound, 'RPG/rm0001_dialog.ini': ini.encode(),
             'SCRIPTS/RPG/conversation.thn': SESSION_THN.encode()}
    folder.sync_rpg_runtime(files, root / 'backup')
    assert (root / 'backup/DATA/RPG/rh_biz_contact.ini').read_bytes() == previous
    for path, content in files.items():
        assert folder.data_path(path).read_bytes() == content
print('PASS: real THN/audio preflight, Bismarck ACU/PCU placement, idempotent contact binding, '
      'complete dialogue graph, optional reputation, central runtime DATA writes/backups')
