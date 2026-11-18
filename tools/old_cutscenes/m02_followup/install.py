"""Install only checked authoring sources and direct class bindings; no DATA."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
ASSETS = Path('D:/Games/FL_MOD/Assets')
PL = ASSETS / 'Pythonlancer'
ROOT = REPO / 'out/story_cutscenes'
OUT = ROOT / 'm02_followup'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path, root):
    assert path.resolve().is_relative_to(root.resolve()), path
    assert not any(p.is_junction() or p.is_symlink() for p in (path, *path.parents)), path


def prepare():
    plan = json.loads((OUT / 'api_plan.json').read_text())
    shared = {PL / 'story/scripts/main/mission2.py': None,
              PL / 'story/cutscenes/reconstructed_m02_m08.py': None}
    shared = {p: p.read_bytes() for p in shared}
    for kind in ('jacobo', 'done'):
        folder = ROOT / f'm02_{kind}'
        spec = json.loads((folder / 'spec.json').read_text(encoding='utf-8'))
        check = json.loads((folder / 'check.json').read_text())
        blend = json.loads((folder / 'blender_check.json').read_text())
        name, cls = spec['name'], spec['scene_class']
        assert check['source_actions_checked'] == len(spec['actions'])
        assert not check['missing_references']
        assert check['backward_time_steps'] == check['overlapping_speech'] == 0
        assert blend['reopened'] and blend['max_transform_error'] < 0.000002
        pairs = [(folder / (name + '.py'), PL / f'story/cutscenes/story_scenes/{name}.py',
                  spec['original_scene_sha256'], check['scene_sha256']),
                 (folder / (name + '.blend'), ASSETS / f'SCENES/{name}.blend',
                  spec['original_blend_sha256'], blend['sha256']),
                 (folder / (name + '.json'), ASSETS / f'SCENES/DUMPS/{name}.json',
                  spec['original_dump_sha256'], check['dump_sha256'])]
        assert blend['source_scene_sha256'] == check['scene_sha256']
        for stage, target, before, after in pairs:
            assert digest(stage) == after and digest(target) == before, target
            plan.append({'stage': str(stage), 'target': str(target), 'before': before, 'after': after})
        edits = [(PL / 'story/scripts/main/mission2.py',
                  f'THORN_CLASS = {name}.ReconstructedScene', f'THORN_CLASS = {name}.{cls}'),
                 (PL / 'story/cutscenes/reconstructed_m02_m08.py',
                  f"'module': 'story.cutscenes.story_scenes.{name}', 'class': 'ReconstructedScene'",
                  f"'module': 'story.cutscenes.story_scenes.{name}', 'class': '{cls}'")]
        for target, old, new in edits:
            assert shared[target].count(old.encode()) == 1
            shared[target] = shared[target].replace(old.encode(), new.encode())
    for target, data in shared.items():
        stage = OUT / target.name
        ast.parse(data.decode('utf-8-sig'))
        stage.write_bytes(data)
        plan.append({'stage': str(stage), 'target': str(target), 'before': digest(target), 'after': digest(stage)})
    # Do not regenerate the user's already edited offer or accept.
    protected = []
    for kind in ('offer', 'accept', 'decision'):
        name = f'm02_bship_bar_{kind}'
        for p in (PL / f'story/cutscenes/story_scenes/{name}.py', ASSETS / f'SCENES/{name}.blend',
                  ASSETS / f'SCENES/DUMPS/{name}.json'):
            protected.append({'path': str(p), 'sha256': digest(p)})
    for item in plan:
        safe(Path(item['stage']), ROOT)
        safe(Path(item['target']), ASSETS)
        assert digest(Path(item['target'])) == item['before']
        assert digest(Path(item['stage'])) == item['after']
    (OUT / 'install_plan.json').write_text(json.dumps({'files': plan, 'protected': protected}, indent=2), encoding='utf-8')
    print('\n'.join(item['target'] for item in plan))


def apply():
    manifest = json.loads((OUT / 'install_plan.json').read_text())
    plan = manifest['files']
    previous = {}
    for item in plan:
        target, stage = Path(item['target']), Path(item['stage'])
        safe(target, ASSETS)
        safe(stage, ROOT)
        assert digest(target) == item['before'], f'Changed after preparation: {target}'
        assert digest(stage) == item['after'], stage
        previous[target] = target.read_bytes()
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
        for kind in ('jacobo', 'done'):
            subprocess.run([str(python), '-B', str(Path(__file__).with_name('check.py')),
                            '--scene', kind, '--installed'], cwd=REPO, check=True)
        # Verify actual imports and the registry bindings as used by single.py.
        command = (
            'from story.scripts.main import mission2; '
            'from story.cutscenes import reconstructed_m02_m08 as registry; '
            'assert mission2.Msn2Miner.THORN_CLASS.__name__ == "M02JacoboOfferScene"; '
            'assert mission2.Msn2Done.THORN_CLASS.__name__ == "M02ReichmanScene"; '
            'assert registry.SCENES["m02_jacobo_offer"]["class"] == "M02JacoboOfferScene"; '
            'assert registry.SCENES["m02_reichman"]["class"] == "M02ReichmanScene"'
        )
        subprocess.run([str(python), '-B', '-c', command], cwd=PL, check=True)
        for item in manifest['protected']:
            assert digest(Path(item['path'])) == item['sha256'], item['path']
    except BaseException:
        for target in written:
            target.write_bytes(previous[target])
        raise
    (OUT / 'installed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Only this transaction's verified redundant binary copies are removed.
    for item in plan:
        stage = Path(item['stage'])
        if stage.suffix == '.blend':
            safe(stage, ROOT)
            assert digest(stage) == digest(Path(item['target'])) == item['after']
            stage.unlink()
    print(f'Installed and verified {len(plan)} authoring files. Offer/accept/decision unchanged. No DATA writes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    apply() if parser.parse_args().apply else prepare()
