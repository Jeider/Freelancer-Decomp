"""Prepare and check the canonical ship integration without touching game DATA."""
import argparse
import difflib
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'out/ship_design/rh_elite/rh_pir_elite'
PY = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
STAGE = OUT / 'pythonlancer'
ASSET_REL = 'assets/ships/rheinland/rh_pir_elite'
TPL = 'templates/hardcoded_inis/shiparch/playerships/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


DATA_API = '''
    # BEGIN RH PIR ELITE ASSET OUTPUT
    def sync_rh_pir_elite(self, files=None):
        """Canonical fighter assets; no detached-debris caps or INI rewrites.

        With no argument, load the checked-in source assets for normal builds.
        Explicit payloads use the same API for staging and transaction rollback.
        """
        import hashlib
        base = 'ships/rheinland/rh_pir_elite/'
        allowed = {'rh_pir_elite.cmp', 'rh_pir_elite.sur', 'rh_pir_elite_lods.mat'}
        for zone in ('port_wing', 'starboard_wing', 'port_engine', 'starboard_engine', 'tail'):
            for extension in ('.3db', '.sur'):
                allowed.add('rh_pir_elite_dmg_' + zone + extension)
        if files is None:
            source = pathlib.Path(__file__).resolve().parents[1] / 'assets' / base
            manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
            if set(manifest['files']) != allowed:
                raise ValueError('Incomplete RH pirate source asset manifest')
            files = {}
            for name, expected in manifest['files'].items():
                content = (source / name).read_bytes()
                if hashlib.sha256(content).hexdigest() != expected['sha256']:
                    raise ValueError('RH pirate source asset hash mismatch: ' + name)
                files[base + name] = content
        # Validate the entire set before writing anything.
        for name, content in files.items():
            if name not in {base + item for item in allowed}:
                raise ValueError('Unexpected RH pirate asset target: ' + name)
            if content is not None and not isinstance(content, bytes):
                raise TypeError('RH pirate asset payload must be bytes or None')
            self.data_path(name)
        for name, content in files.items():
            if content is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, content)
    # END RH PIR ELITE ASSET OUTPUT
'''


def prepare():
    build = json.loads((OUT / 'build.json').read_text())
    assert len(build['files']) == 13 and len(build['damage']) == 5
    updates = {}
    text = (PY / 'world/ship.py').read_text(encoding='utf-8')
    assert 'SHIPARCH_TEMPLATE = ' not in text
    text = text.replace('    TEMPLATE_CODE = None', '    TEMPLATE_CODE = None\n    SHIPARCH_TEMPLATE = None', 1)
    text = text.replace('class PirateValkyrie(Valkyrie):',
                        "class PirateValkyrie(Valkyrie):\n    SHIPARCH_TEMPLATE = 'rh_pir_elite'", 1)
    updates['world/ship.py'] = text
    text = (PY / 'managers/shiparch.py').read_text(encoding='utf-8')
    before, v2 = text.split('class ShiparchManagerV2:', 1)
    old = 'template = PLAYERSHIPS_TEMPLATE_FORMAT.format(archetype=instance.get_clean_archetype())'
    assert v2.count(old) == 1
    v2 = v2.replace(old, 'template = PLAYERSHIPS_TEMPLATE_FORMAT.format(\n'
                        '                archetype=instance.SHIPARCH_TEMPLATE or instance.get_clean_archetype())')
    old = 'data_folder.sync_shiparch_alt(self.get_shiparch_content())  # Temporary!'
    assert v2.count(old) == 1
    v2 = v2.replace(old, 'content = self.get_shiparch_content()\n'
                        '        data_folder.sync_rh_pir_elite()\n'
                        '        data_folder.sync_shiparch_alt(content)  # Temporary!')
    updates['managers/shiparch.py'] = before + 'class ShiparchManagerV2:' + v2
    text = (PY / 'tools/data_folder.py').read_text(encoding='utf-8')
    assert 'def sync_rh_pir_elite(' not in text
    updates['tools/data_folder.py'] = text.rstrip() + '\n' + DATA_API
    text = (PY / (TPL + 'rh_elite.ini')).read_text(encoding='utf-8')
    text = text.replace(';RH_SHIP', '; RH pirate redesign; parent caps only, no flying-debris caps.')
    text = text.replace('0, 1000, 5000, 10000', '0, 180, 550, 10000')
    text = text.replace('rh{{ prefix }}_', 'rh_pir_')
    text = text.replace('material_library = fx\\envmapbasic.mat',
                        'material_library = ships\\rheinland\\rh_pir_elite\\rh_pir_elite_lods.mat\n'
                        'material_library = fx\\envmapbasic.mat')
    text = text.replace('dmg_obj = rh_elite_', 'dmg_obj = rh_pir_elite_')
    updates[TPL + 'rh_pir_elite.ini'] = text
    doc = '''# RH pirate elite integration

Canonical asset directory: `DATA/ships/rheinland/rh_pir_elite`.
Gameplay nickname remains `rh_elite_pir` so saves, loadouts, IDs and balance stay compatible.
PirateValkyrie selects its own template in ShiparchManagerV2. Other variants retain their templates.
Normal V2 synchronization installs these source assets through DataFolder before writing shiparch.ini.
`write=False` is read-only. The initial asset/source installation does not rewrite active shiparch.ini.

Five detachable groups: two wings, two engines and the middle rear upright of tail.
The upper/lower frame and drum remain on Root. Five existing pirate Simple archetypes reference
the new parent-side damage caps. No group_dmg_hp/group_dmg_obj and no debris-side cap assets.
This is the current policy for fighters; debris-side caps are considered separately for capital ships.

Every part owns its wire. Empty explicit wires suppress triangle fallback on glass/doors/sockets.
The HUD snapshots the current animated pose; the SUR stays static in the unfolded pose.
The source user's equipment hardpoints, rig and all three rendered LOD meshes are preserved.
Private resource names carry a fresh export salt. Object names and shared material identities remain stable.
The shared rh_pir_playerships.mat is user-owned; this package adds only a private LOD MAT.

The installer deliberately leaves active shiparch.ini to the user's normal Pythonlancer generation.
No game process is launched by this integration.
'''
    updates['docs/rh_pir_elite.md'] = doc
    manifest = {'files': {}, 'assets': build['files'], 'salt': build['salt']}
    diff = []
    for relative, text in updates.items():
        path = PY / relative
        old = path.read_bytes() if path.exists() else None
        save(STAGE / relative, text)
        manifest['files'][relative] = {'before': sha(old) if old is not None else None,
                                      'after': sha((STAGE / relative).read_bytes())}
        diff.extend(difflib.unified_diff((old.decode('utf-8').splitlines(True) if old else []),
                                        text.splitlines(True), fromfile='a/' + relative, tofile='b/' + relative))
    for name, entry in build['files'].items():
        payload = (OUT / 'assets' / name).read_bytes()
        assert sha(payload) == entry['sha256']
        target = STAGE / ASSET_REL / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    save(STAGE / ASSET_REL / 'manifest.json', json.dumps(build, indent=2))
    save(OUT / 'pythonlancer.patch', ''.join(diff))
    save(OUT / 'source_changes.json', json.dumps(manifest, indent=2))
    print('PREPARED', len(updates), 'source files,', len(build['files']), 'assets')


class Overlay(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        file = STAGE / (fullname.replace('.', '/') + '.py')
        if file.is_file():
            return importlib.util.spec_from_file_location(fullname, file)


def render(mode):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(PY))
    if mode == 'staged':
        sys.meta_path.insert(0, Overlay())
    from managers.ids import IDsManager
    from managers.jinja_manager import JinjaTemplateManager
    from managers.shiparch import ShiparchManagerV2
    from tools.data_folder import DataFolder
    from jinja2 import ChoiceLoader, FileSystemLoader
    core = SimpleNamespace(write=False, build_folder=None, misc_equip=None)
    core.ids = IDsManager(core)
    core.tpl_manager = JinjaTemplateManager()
    directories = [PY / 'templates']
    if mode == 'staged':
        directories.insert(0, STAGE / 'templates')
    core.tpl_manager.environment.loader = ChoiceLoader([FileSystemLoader(str(p)) for p in directories])
    manager = ShiparchManagerV2(core)
    # This standalone render audits all templates. Normal generation marks actual ship usage itself.
    for ship in manager.ships:
        ship.used = True
    content = manager.get_shiparch_content()
    save(OUT / (mode + '_shiparch.ini'), content)
    if mode != 'baseline':
        folder = DataFolder(root=OUT / 'validation_stage')
        folder.sync_rh_pir_elite()
        folder.sync_shiparch_alt(content)
        for bad in ('ships/rheinland/rh_pir_elite/rh_pir_elite_break_tail.3db',
                    'SHIPS/shiparch.ini', '../escape'):
            try:
                folder.sync_rh_pir_elite({bad: b'bad'})
            except ValueError:
                pass
            else:
                raise AssertionError(bad)
    print('RENDERED', mode, len(manager.ships), 'ships', len(content), 'characters')


def sections(text):
    result = []
    for block in re.split(r'(?m)(?=^\[)', text):
        match = re.match(r'\[([^]]+)\]', block)
        if not match:
            continue
        values = {}
        for line in block.splitlines()[1:]:
            line = line.split(';', 1)[0].strip()
            if '=' in line:
                name, value = line.split('=', 1)
                values.setdefault(name.strip().lower(), []).append(value.strip())
        result.append((match[1].lower(), values))
    return result


def check():
    a = sections((OUT / 'baseline_shiparch.ini').read_text(encoding='utf-8'))
    b = sections((OUT / 'staged_shiparch.ini').read_text(encoding='utf-8'))
    assert len(a) == len(b)
    changes = []; target = None; groups = []
    for index, ((ka, va), (kb, vb)) in enumerate(zip(a, b)):
        assert ka == kb
        if 'nickname' in vb:
            target = vb['nickname'][0]
        if va != vb:
            assert target == 'rh_elite_pir', (index, target)
            allowed = {'lodranges', 'da_archetype', 'material_library'} if kb == 'ship' else {'dmg_obj'}
            diff = {key for key in va.keys() | vb.keys() if va.get(key) != vb.get(key)}
            assert diff <= allowed, diff
            changes.append({'section': kb, 'changed': sorted(diff)})
        if target == 'rh_elite_pir' and kb == 'collisiongroup':
            assert not any(k.startswith('group_dmg') for k in vb)
            groups.append(vb)
    assert len(groups) == 5 and len(changes) == 6
    import rh_pir_elite_build as build
    f = build.f
    _, nodes = f.mesh.read_tree((OUT / 'assets/rh_pir_elite.cmp').read_bytes())
    hps = build.v.hp.hardpoint_records(nodes)
    names = f.component_map(nodes)
    material_paths = [Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_pir_playerships.mat'),
                      OUT / 'assets/rh_pir_elite_lods.mat']
    materials = set()
    for material_path in material_paths:
        _, library = f.mesh.read_tree(material_path.read_bytes())
        materials.update(f.mesh.crc(n.name) for n in f.mesh.child(library[0], 'Material library').children)
    for model in [OUT / 'assets/rh_pir_elite.cmp', *(OUT / 'assets').glob('*.3db')]:
        _, model_nodes = f.mesh.read_tree(model.read_bytes())
        for path, node in f.mesh.walk(model_nodes):
            assert '/texture library' not in path.lower() and '/material library' not in path.lower()
            if path.lower().endswith('/vmeshdata'):
                import struct
                count = struct.unpack_from('<H', node.blob, 8)[0]
                used = {struct.unpack_from('<I', node.blob, 16 + 12 * i)[0] for i in range(count)}
                assert used <= materials, (model.name, used - materials)
    assert len({hp['name'].lower() for hp in hps}) == len(hps) == 79
    simples = {v['nickname'][0]: v for k, v in b if k == 'simple' and 'nickname' in v}
    group_report = []
    for group in groups:
        part = group['obj'][0].lower(); hp_name = group['dmg_hp'][0].lower()
        assert part in {n.lower() for n in names.values()}
        hp = next(h for h in hps if h['name'].lower() == hp_name)
        assert hp['owner'].lower() != part, (part, hp)
        simple = simples[group['dmg_obj'][0]]
        cap = OUT / 'assets' / simple['da_archetype'][0].replace('\\', '/').split('/')[-1]
        assert cap.is_file() and cap.with_suffix('.sur').is_file()
        _, cap_nodes = f.mesh.read_tree(cap.read_bytes())
        paths = [p.lower() for p, _ in f.mesh.walk(cap_nodes)]
        assert any('/hardpoints/fixed/dpconnect/' in p for p in paths)
        assert not any('/texture library' in p or '/material library' in p for p in paths)
        group_report.append({'part': part, 'hp': hp['name'], 'hp_owner': hp['owner'],
                             'cap': cap.name, 'hit_pts': group['hit_pts'][0]})
    files = json.loads((OUT / 'build.json').read_text())['files']
    staged = OUT / 'validation_stage/DATA/ships/rheinland/rh_pir_elite'
    assert set(p.name for p in staged.iterdir()) == set(files)
    for name, expected in files.items():
        assert sha((staged / name).read_bytes()) == expected['sha256']
    report = dict(sections=len(b), changed_sections=changes, groups=group_report,
                  all_other_generated_sections_unchanged=True, balances_and_ids_unchanged=True,
                  parent_caps=5, debris_caps=0, staging_via_datafolder=True,
                  user_hardpoints=79, all_material_references_resolved=True, active_shiparch_written=False)
    save(OUT / 'integration_check.json', json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'baseline', 'staged', 'installed', 'check'))
    action = parser.parse_args().action
    if action == 'prepare':
        prepare()
    elif action == 'check':
        check()
    else:
        render(action)


if __name__ == '__main__':
    main()
