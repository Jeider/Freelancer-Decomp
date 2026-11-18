"""Install checked native RTC authoring sources, blends and dumps; never DATA."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys
from inventory import OUT, PL, REPO, sha

ASSETS = PL.parent
INVENTORY = json.loads((OUT / 'inventory.json').read_text())


def digest(path):
    return sha(path.read_bytes()) if path.exists() else None


def safe(path, root):
    assert path.resolve().is_relative_to(root.resolve()), path
    assert not any(p.is_junction() or p.is_symlink() for p in (path, *path.parents)), path


def without_bindings(data):
    tree = ast.parse(data.decode('utf-8-sig'))
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        cls.body = [n for n in cls.body if not (isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id.startswith('THORN') for t in n.targets))]
    return ast.dump(tree)


def prepare():
    assert json.loads((OUT / 'compatibility_check.json').read_text()) == json.loads((OUT / 'compatibility_baseline.json').read_text())
    plan = json.loads((OUT / 'api_plan.json').read_text())
    scripts = {PL / f'story/scripts/main/mission{m}.py': (PL / f'story/scripts/main/mission{m}.py').read_bytes() for m in range(3, 9)}
    registry_path = PL / 'story/cutscenes/reconstructed_m02_m08.py'
    registry = registry_path.read_bytes()
    for name in INVENTORY['scenes']:
        folder = OUT / name
        spec = json.loads((folder / 'spec.json').read_text(encoding='utf-8'))
        check = json.loads((folder / 'check.json').read_text())
        blend = json.loads((folder / 'blender_check.json').read_text())
        assert check['master_actions_checked'] == len(spec['actions']) + len(spec['attachment_events'])
        assert check['master_lines'] == len(spec['dialogue']) and not check['final_thn_written']
        assert blend['reopened'] and blend['source_scene_sha256'] == check['scene_sha256']
        pairs = [(folder / f'{name}.py', PL / f'story/cutscenes/story_scenes/{name}.py', spec['original_scene_sha256'], check['scene_sha256']),
                 (folder / f'{name}.blend', ASSETS / f'SCENES/{name}.blend', spec['original_blend_sha256'], blend['sha256']),
                 (folder / f'{name}.json', ASSETS / f'SCENES/DUMPS/{name}.json', spec['original_dump_sha256'], check['dump_sha256'])]
        for stage, target, before, after in pairs:
            assert digest(stage) == after and digest(target) == before, target
            plan.append(dict(stage=str(stage), target=str(target), before=before, after=after))
        cls = spec['scene_class']
        for path, data in scripts.items():
            scripts[path] = data.replace(f'{name}.ReconstructedScene'.encode(), f'{name}.{cls}'.encode())
        old = f"'module': 'story.cutscenes.story_scenes.{name}', 'class': 'ReconstructedScene'".encode()
        new = f"'module': 'story.cutscenes.story_scenes.{name}', 'class': '{cls}'".encode()
        assert registry.count(old) == 1, name
        registry = registry.replace(old, new)
    for path, data in scripts.items():
        assert without_bindings(data) == without_bindings(path.read_bytes()), path
    # RTCs without dialogue had never been connected to the mission authoring
    # list. Register them without adding or rewriting any spoken lines.
    additional = {
        5: [('Msn5Barman', 'm05_barman')],
        6: [('Msn6VendorHatcher', 'm06_vendor_hatcher'), ('Msn6VendorAlaric', 'm06_vendor_alaric'),
            ('Msn6LabLaunch', 'm06_lab_launch'), ('Msn6OmicronMajor', 'm06_omicron_major')],
        7: [('Msn7TauArrival', 'm07_tau_arrival')],
    }
    for mission, additions in additional.items():
        path = PL / f'story/scripts/main/mission{mission}.py'
        raw = scripts[path]
        newline = '\r\n' if b'\r\n' in raw else '\n'
        text = raw.decode('utf-8-sig')
        new_import = 'from story.cutscenes.story_scenes import ' + ', '.join(n for _, n in additions)
        text = new_import + newline + text
        declarations = []
        for cls, name in additions:
            spec = json.loads((OUT / name / 'spec.json').read_text(encoding='utf-8'))
            declarations += [f'class {cls}(Msn{mission}, script.CutsceneProps):',
                             f'    THORN_CLASS = {name}.{spec["scene_class"]}',
                             f'    ALIAS = {name[4:]!r}', f'    TITLE = {name!r}', "    DESCRIPTION = ''", '', '']
        anchor = f'class Msn{mission}Space('
        assert text.count(anchor) == 1
        text = text.replace(anchor, newline.join(declarations) + anchor)
        anchor = '    CUTSCENES = ['
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor + newline + newline.join(f'        {cls},' for cls, _ in additions))
        # Compare every existing VOICE_LINES assignment, including RU text and
        # delivery controls, to the working script byte-for-byte at AST level.
        def voice_lists(content):
            return {cls.name: ast.dump(n.value) for cls in ast.parse(content).body if isinstance(cls, ast.ClassDef)
                    for n in cls.body if isinstance(n, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == 'VOICE_LINES' for t in n.targets)}
        assert voice_lists(text) == voice_lists(raw.decode('utf-8-sig'))
        scripts[path] = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + text.encode('utf-8')
    # The scale field is opt-in per blend. Existing authored scenes keep their
    # established dump behavior; the master scenes include signed source scales.
    dumper = ASSETS / 'SCENES/SCRIPTS/dumper.py'
    raw = dumper.read_bytes()
    old = b"    }"
    assert raw.count(old) == 1
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    new = old + newline + b"    if C.scene.get('export_point_scale', False):" + newline + b"        results[str(key)]['matrix_scale'] = list(value.scale)"
    shared = {**scripts, registry_path: registry, dumper: raw.replace(old, new)}
    for target, data in shared.items():
        stage = OUT / 'integration' / target.relative_to(ASSETS)
        stage.parent.mkdir(parents=True, exist_ok=True)
        ast.parse(data.decode('utf-8-sig'))
        stage.write_bytes(data)
        plan.append(dict(stage=str(stage), target=str(target), before=digest(target), after=sha(data)))
    protected_paths = [PL / 'story/cutscenes/story_scenes/m08.py', PL / 'story/scripts/main/mission2.py']
    for name in ('br_battleship_deck', 'dig_site', 'm02_bship_bar_offer', 'm02_bship_bar_accept',
                 'm02_bship_bar_decision', 'm02_jacobo_offer', 'm02_reichman'):
        protected_paths += [ASSETS / f'SCENES/{name}.blend', ASSETS / f'SCENES/DUMPS/{name}.json']
        source = PL / f'story/cutscenes/story_scenes/{name}.py'
        if source.exists():
            protected_paths.append(source)
    old_registry = ast.literal_eval(next(n.value for n in ast.parse(registry_path.read_text(encoding='utf-8')).body
                                        if isinstance(n, ast.Assign)))
    new_registry = ast.literal_eval(next(n.value for n in ast.parse(registry.decode('utf-8')).body if isinstance(n, ast.Assign)))
    excluded_names = set(old_registry) - set(INVENTORY['scenes'])
    assert all(old_registry[n] == new_registry[n] for n in excluded_names)
    for name in excluded_names:
        if not all(u['role'] == 'act_callthorn' for u in old_registry[name]['uses']):
            continue
        for path in (PL / f'story/cutscenes/story_scenes/{name}.py', ASSETS / f'SCENES/{name}.blend',
                     ASSETS / f'SCENES/DUMPS/{name}.json'):
            if path.exists():
                protected_paths.append(path)
    protected = [dict(path=str(p), sha256=digest(p)) for p in set(protected_paths)]
    for item in plan:
        safe(Path(item['stage']), OUT)
        safe(Path(item['target']), ASSETS)
        assert digest(Path(item['target'])) == item['before']
        assert digest(Path(item['stage'])) == item['after']
    manifest = dict(files=plan, protected=protected, scenes=list(INVENTORY['scenes']),
                    voice_lines_changed=False, data_writes=False, master_commit=INVENTORY['commit'])
    (OUT / 'install_plan.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Prepared {len(plan)} authoring files for {len(INVENTORY["scenes"])} RTC scenes; {len(protected)} protected files. No DATA.')


def apply():
    manifest = json.loads((OUT / 'install_plan.json').read_text())
    plan = manifest['files']
    previous = {}
    for item in plan:
        target, stage = Path(item['target']), Path(item['stage'])
        safe(target, ASSETS)
        safe(stage, OUT)
        assert digest(target) == item['before'], f'Changed since preparation: {target}'
        assert digest(stage) == item['after'], stage
        previous[target] = target.read_bytes() if target.exists() else None
    for item in manifest['protected']:
        assert digest(Path(item['path'])) == item['sha256'], item['path']
    written = []
    try:
        for item in plan:
            target = Path(item['target'])
            written.append(target)
            target.write_bytes(Path(item['stage']).read_bytes())
        for item in plan:
            assert digest(Path(item['target'])) == item['after'], item['target']
        python = PL / '.venv/Scripts/python.exe'
        for script, args in [('check.py', ['--installed']), ('verify_bindings.py', ['--installed'])]:
            subprocess.run([str(python), '-B', str(Path(__file__).with_name(script)), *args], cwd=REPO, check=True)
        for item in manifest['protected']:
            assert digest(Path(item['path'])) == item['sha256'], item['path']
    except BaseException:
        for target in written:
            safe(target, ASSETS)
            if previous[target] is None:
                target.unlink()
            else:
                target.write_bytes(previous[target])
        raise
    (OUT / 'installed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    for item in plan:
        stage = Path(item['stage'])
        if stage.suffix == '.blend':
            safe(stage, OUT)
            assert digest(stage) == digest(Path(item['target'])) == item['after']
            stage.unlink()
    print(f'Installed and verified {len(plan)} authoring files; 43 RTC scenes. No DATA writes. Staged blend copies removed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    apply() if parser.parse_args().apply else prepare()
