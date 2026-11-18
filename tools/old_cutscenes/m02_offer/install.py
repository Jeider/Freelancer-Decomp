"""Install the selected scene, its editable points, and direct class references."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / 'out/story_cutscenes/m02_offer'
ASSETS = Path('D:/Games/FL_MOD/Assets')
PL = ASSETS / 'Pythonlancer'
NAME = 'm02_bship_bar_offer'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(scene_only=False):
    check = json.loads((OUT / 'check.json').read_text())
    spec = json.loads((OUT / 'spec.json').read_text())
    assert check['source_actions_checked'] == len(spec['actions']) and not check['missing_references']
    assert check['scene_sha256'] == digest((OUT / (NAME + '.py')).read_bytes())
    assert check['backward_time_steps'] == check['overlapping_speech'] == 0
    if scene_only:
        stage = OUT / (NAME + '.py')
        target = PL / f'story/cutscenes/story_scenes/{NAME}.py'
        assert check['scene_sha256'] == digest(stage.read_bytes())
        assert check['backward_time_steps'] == check['overlapping_speech'] == 0
        plan = [{'stage': str(stage), 'target': str(target), 'before': digest(target.read_bytes()),
                 'after': digest(stage.read_bytes())}]
        (OUT / 'install_plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
        print(target)
        return
    blend = json.loads((OUT / 'blender_check.json').read_text())
    assert blend['reopened'] and blend['sha256'] == digest((OUT / (NAME + '.blend')).read_bytes())
    binding = 'THORN_ACCEPT_CLASS' if NAME.endswith('_accept') else 'THORN_CLASS'
    scene_class = spec.get('scene_class', 'Msn2OfferScene')
    edits = [(PL / 'story/scripts/main/mission2.py',
              f'{binding} = {NAME}.ReconstructedScene'.encode(),
              f'{binding} = {NAME}.{scene_class}'.encode()),
             (PL / 'story/cutscenes/reconstructed_m02_m08.py',
              f"'module': 'story.cutscenes.story_scenes.{NAME}', 'class': 'ReconstructedScene'".encode(),
              f"'module': 'story.cutscenes.story_scenes.{NAME}', 'class': '{scene_class}'".encode())]
    pairs = [(OUT / (NAME + '.py'), PL / f'story/cutscenes/story_scenes/{NAME}.py'),
             (OUT / (NAME + '.blend'), ASSETS / f'SCENES/{NAME}.blend'),
             (OUT / (NAME + '.json'), ASSETS / f'SCENES/DUMPS/{NAME}.json')]
    for target, old, new in edits:
        data = target.read_bytes()
        assert data.count(old) == 1, target
        stage = OUT / target.name
        stage.write_bytes(data.replace(old, new))
        ast.parse(stage.read_text(encoding='utf-8-sig'))
        pairs.append((stage, target))
    plan = [{'stage': str(stage), 'target': str(target), 'before': digest(target.read_bytes()),
             'after': digest(stage.read_bytes())} for stage, target in pairs]
    (OUT / 'install_plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print('\n'.join(p['target'] for p in plan))


def apply():
    plan = json.loads((OUT / 'install_plan.json').read_text())
    previous = {}
    for item in plan:
        target, stage = Path(item['target']), Path(item['stage'])
        assert target.resolve().is_relative_to(ASSETS.resolve())
        assert stage.resolve().is_relative_to(OUT.resolve())
        previous[target] = target.read_bytes()
        assert digest(previous[target]) == item['before'], f'Changed after preparation: {target}'
        assert digest(stage.read_bytes()) == item['after'], stage
    written = []
    try:
        for item in plan:
            target = Path(item['target'])
            written.append(target)
            target.write_bytes(Path(item['stage']).read_bytes())
        for item in plan:
            assert digest(Path(item['target']).read_bytes()) == item['after'], item['target']
    except BaseException:
        for target in written:
            target.write_bytes(previous[target])
        raise
    (OUT / 'installed.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    # The installed blend is the editable source; its staging duplicate is redundant.
    staged_blend = OUT / (NAME + '.blend')
    if any(Path(item['stage']) == staged_blend for item in plan):
        assert staged_blend.resolve().is_relative_to(OUT.resolve())
        assert not any(p.is_junction() or p.is_symlink() for p in (staged_blend, *staged_blend.parents))
        staged_blend.unlink()
    print(f'Verified {len(plan)} installed files. No DATA writes.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--scene-only', action='store_true')
    parser.add_argument('--scene', choices=('offer', 'accept'), default='offer')
    args = parser.parse_args()
    NAME = f'm02_bship_bar_{args.scene}'
    OUT = REPO / f'out/story_cutscenes/m02_{args.scene}'
    apply() if args.apply else prepare(scene_only=args.scene_only)
