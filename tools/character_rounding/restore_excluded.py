"""Restore the pre-rounding torture DFM; verify and preserve today's alien."""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/hatcher_hair'))
from build import GAME, DataFolder, child, read_tree, triangles
from repair_panel_normals import leaves
from policy import excluded_name

BATCH = ROOT / 'out/character_rounding/all_bodies'
OUT = ROOT / 'out/character_rounding/exclusions'
TORTURE = 'br_darcy_body_torture'
ALIEN = 'alien_nomad_body'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lod_counts(data):
    root = read_tree(data)[1][0]
    return {mesh.name: sum(len(triangles(group))
                          for group in child(mesh, 'Face_groups').children
                          if group.children)
            for mesh in child(root, 'MultiLevel').children
            if mesh.children and mesh.name.startswith('Mesh')}


def body_hashes():
    return {p.name: sha(p.read_bytes())
            for p in sorted((GAME / 'DATA/CHARACTERS/BODIES').glob('*.dfm'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    assert excluded_name(TORTURE) and excluded_name(ALIEN)
    live = DataFolder(root=GAME)
    report = read_json(BATCH / TORTURE / 'report.json')
    receipt = read_json(BATCH / 'installed.json')
    relative = 'CHARACTERS/BODIES/' + TORTURE + '.dfm'
    entry = next(row for row in receipt['files'] if row['relative_path'] == relative)
    backup_root = Path(receipt['backup']).resolve()
    assert backup_root.is_relative_to((BATCH / 'backups').resolve())
    original = DataFolder(root=backup_root).data_path(relative).read_bytes()
    current = live.data_path(relative).read_bytes()
    assert sha(original) == report['source_sha256'] == entry['before_sha256']
    assert report['output_sha256'] == entry['after_sha256']
    assert sha(current) in (entry['before_sha256'], entry['after_sha256']), \
        'Torture changed independently; refusing to replace it'

    before_leaves = {key: value for key, _, value in leaves(current)[1]}
    original_leaves = {key: value for key, _, value in leaves(original)[1]}
    changed_leaves = [key for key in set(before_leaves) | set(original_leaves)
                      if before_leaves.get(key) != original_leaves.get(key)]
    assert all('/MultiLevel/Mesh0/' in key for key in changed_leaves)
    assert lod_counts(original)['Mesh0'] == report['triangles_before'] == 3596

    alien_rel = 'CHARACTERS/BODIES/' + ALIEN + '.dfm'
    alien = live.data_path(alien_rel).read_bytes()
    alien_report = read_json(BATCH / ALIEN / 'report.json')
    alien_manifest = read_json(ROOT / 'out/nomad_character/game_body_v3/manifest.json')
    assert not alien_report['changed']
    assert sha(alien) == alien_report['source_sha256'] == alien_report['output_sha256']
    assert sha(alien) == alien_manifest['files'][alien_rel]['after'], \
        'Alien differs from the corrected creation build; inspect before proceeding'
    assert lod_counts(alien)['Mesh0'] == alien_manifest['triangles'] == 19859
    snapshot = body_hashes()
    result = {
        'action': 'restore_rounding_exclusion',
        'mode': 'apply' if args.apply else 'preflight',
        'torture': {
            'relative_path': relative,
            'before_sha256': sha(current),
            'restored_sha256': sha(original),
            'lod_triangles_before': lod_counts(current),
            'lod_triangles_restored': lod_counts(original),
            'source_backup': str(backup_root),
            'only_mesh0_changes': True,
            'needs_restore': current != original,
        },
        'alien': {
            'relative_path': alien_rel, 'sha256': sha(alien),
            'matches_corrected_creation_build': True,
            'rounding_changed_it': False, 'write_required': False,
            'lod_triangles': lod_counts(alien),
        },
        'game_launched': False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'preflight.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    if not args.apply:
        print(json.dumps(result, indent=2))
        return

    if current != original:
        backup = OUT / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        saved = DataFolder(root=backup)
        saved.sync_data_file(relative, current)
        assert saved.data_path(relative).read_bytes() == current
        (backup / 'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        result['undo_backup'] = str(backup)
        assert live.data_path(relative).read_bytes() == current
        assert live.data_path(alien_rel).read_bytes() == alien
        try:
            live.sync_data_file(relative, original)
            assert live.data_path(relative).read_bytes() == original
        except BaseException:
            live.sync_data_file(relative, current)
            assert live.data_path(relative).read_bytes() == current
            raise

    expected = dict(snapshot)
    expected[TORTURE + '.dfm'] = sha(original)
    assert body_hashes() == expected, 'Another body changed during this operation'
    assert live.data_path(alien_rel).read_bytes() == alien
    result.update(restored=current != original, all_other_bodies_unchanged=True,
                  bodies_verified=len(snapshot), hashes_verified=True)
    (OUT / 'restored.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
