"""Preserve ship-art prompts, selected recipes and references outside experiments.

Text snapshots live in docs/ru/ship_design/prompt_archive. Reference images are
deduplicated under out/ship_design/prompt_archive/assets. Nothing is deleted.
--verify checks the archive without reading any original experiment directory.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOPIC = REPO / 'out/ship_design'
DOCS = REPO / 'docs/ru/ship_design/prompt_archive'
ASSETS = TOPIC / 'prompt_archive/assets'
SHIPS = ('rh_freighter', 'rh_fighter', 'bw_family', 'li_elite', 'bh_family')
SELECTION_FOLDERS = {ship: ship for ship in SHIPS}
SELECTION_FOLDERS['bw_freighter'] = 'bw_family/freighter'
SELECTION_FOLDERS['bh_freighter'] = 'bh_family/freighter'
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rel(path):
    return path.resolve().relative_to(REPO).as_posix()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def store_exact(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Refusing to replace immutable archive file: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(data)


def walk_strings(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)
    elif isinstance(value, str):
        yield value


def verify(manifest):
    records = list(manifest['snapshots'].values()) + list(manifest['assets'].values())
    records += list(manifest['selected_recipes'].values())
    for row in records:
        path = (REPO / row['archived_path']).resolve()
        assert path.is_relative_to(REPO) and path.is_file(), str(path)
        assert digest(path.read_bytes()) == row['sha256'], str(path)
    for recipe in manifest['selected_recipes'].values():
        value = load(REPO / recipe['archived_path'])
        assert digest(value['prompt'].encode('utf8')) == value['prompt_sha256']
        for ref in value['references']:
            assert digest((REPO / ref['archived_path']).read_bytes()) == ref['sha256']
        output = value['selected_output']
        assert digest((REPO / output['archived_path']).read_bytes()) == output['sha256']
    return dict(snapshots=len(manifest['snapshots']),
                prompt_snapshots=sum(r['kind'] == 'prompts' for r in manifest['snapshots'].values()),
                reference_assets=len(manifest['assets']),
                selected=list(manifest['selected_recipes']), verified=True,
                original_experiments_required=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    index_path = DOCS / 'manifest.json'
    if args.verify and not index_path.is_file():
        raise FileNotFoundError('Archive manifest does not exist: ' + str(index_path))
    manifest = load(index_path) if index_path.exists() else dict(
        version=1, snapshots={}, assets={}, selected_recipes={},
        retention='Keep all snapshots and asset hashes even if experiments are deleted. '
                  'Historical prompts are not all artistically approved.',
    )
    if args.verify:
        print(json.dumps(verify(manifest), ensure_ascii=False))
        return
    prompt_paths = sorted(p for ship in SHIPS for p in (TOPIC / ship).rglob('*prompt*.json'))
    dependency = TOPIC / 'rh_elite/concepts/concept_prompts.json'
    if dependency.is_file():
        prompt_paths.append(dependency)
    image_paths = set()
    for path in prompt_paths:
        for text in walk_strings(load(path)):
            if len(text) < 500 and Path(text).suffix.lower() in IMAGE_SUFFIXES:
                image = Path(text)
                image = image if image.is_absolute() else path.parent / image
                if not image.is_file():
                    raise FileNotFoundError('Missing prompt reference: ' + str(image))
                image_paths.add(image.resolve())
    for relative_folder in SELECTION_FOLDERS.values():
        selection = TOPIC / relative_folder / 'selection.json'
        if selection.exists():
            image_paths.add((selection.parent / load(selection)['art']).resolve())
    required = sum(p.stat().st_size for p in image_paths)
    if shutil.disk_usage(REPO).free < required + 512 * 1024**2:
        raise OSError('Insufficient free space for retained prompt references')

    def asset(path):
        path = path.resolve()
        data = path.read_bytes()
        key = digest(data)
        target = ASSETS / (key + path.suffix.lower())
        existing = manifest['assets'].get(key)
        if existing:
            target = REPO / existing['archived_path']
        store_exact(target, data)
        row = existing or dict(archived_path=rel(target), sha256=key,
                               bytes=len(data), original_paths=[])
        if path.as_posix() not in row['original_paths']:
            row['original_paths'].append(path.as_posix())
        manifest['assets'][key] = row
        return dict(original_path=path.as_posix(), archived_path=rel(target), sha256=key)

    for path in sorted(image_paths):
        asset(path)

    def snapshot(path, kind):
        data = path.read_bytes()
        key = digest(data)
        original = path.relative_to(TOPIC)
        target = DOCS / 'snapshots' / original.parent / (path.stem + '__' + key[:16] + path.suffix)
        store_exact(target, data)
        record = dict(kind=kind, original_path=rel(path), archived_path=rel(target),
                      sha256=key, bytes=len(data))
        manifest['snapshots'][rel(target)] = record
        return record

    for path in prompt_paths:
        snapshot(path, 'prompts')
    for ship, relative_folder in SELECTION_FOLDERS.items():
        folder = TOPIC / relative_folder
        context = set(folder.rglob('artifacts.json')) | set(folder.rglob('README.md'))
        context |= {folder / 'selection.json', folder / 'SELECTED_CONCEPT.md', folder / 'source_audit.json'}
        for path in sorted(p for p in context if p.is_file()):
            snapshot(path, 'context')
        selection_path = folder / 'selection.json'
        if not selection_path.is_file():
            continue
        selection = load(selection_path)
        output = (folder / selection['art']).resolve()
        assert digest(output.read_bytes()) == selection['art_sha256']
        prompt_path = output.parent / 'prompts.json'
        pack = load(prompt_path)
        variant = next(v for v in pack['variants'] if v['id'] == selection['concept_id'])
        refs = variant.get('referenced_image_paths', pack.get('referenced_image_paths', pack.get('references', [])))
        refs = [x['path'] if isinstance(x, dict) else x for x in refs]
        if variant.get('target_image'):
            refs = [variant['target_image']] + refs
        references = []
        for ref in refs:
            path = Path(ref)
            references.append(asset(path if path.is_absolute() else prompt_path.parent / path))
        prompt = variant['prompt']
        recipe = dict(
            ship=ship, concept_id=selection['concept_id'], title_ru=selection['title_ru'],
            status=selection['status'], selected_by=selection['selected_by'],
            user_evidence=selection['user_evidence'], date=selection['date'],
            tool='built-in image_gen', transparent_background=False,
            prompt=prompt, prompt_sha256=digest(prompt.encode('utf8')),
            prompt_snapshot=snapshot(prompt_path, 'prompts')['archived_path'],
            references=references, selected_output=asset(output),
            replay='Use the prompt verbatim, resolve archived_path against the repository '
                   'root, pass references in this exact order. Generation is not deterministic.',
            lineage='All saved historical prompt and correction files for both ships are '
                    'retained in manifest.json. Referenced intermediate art is retained as assets.',
        )
        if 'rear_view' in selection:
            recipe['rear_view_selection'] = selection['rear_view']
        if 'view_supplement' in selection:
            recipe['view_supplement'] = selection['view_supplement']
        key = ship + '_' + selection['concept_id']
        if 'primary_model' in selection:
            recipe['selection_scope'] = {k: selection[k] for k in (
                'scope', 'primary_model', 'primary_row', 'model_status',
                'mixing_policy', 'cockpit_policy', 'implementation_started',
                'variant', 'role_assignment', 'alternative_concepts', 'latest_user_evidence'
            ) if k in selection}
            recipe['lineage'] = ('All saved historical prompts, correction files and '
                                 'referenced intermediate art are retained in manifest.json.')
        target = DOCS / 'selected' / (key + '.json')
        if target.exists() and load(target) != recipe:
            old = target.read_bytes()
            store_exact(DOCS / 'selected/history' / (key + '__' + digest(old)[:16] + '.json'), old)
        save_json(target, recipe)
        manifest['selected_recipes'][key] = dict(archived_path=rel(target), sha256=digest(target.read_bytes()))
    save_json(index_path, manifest)
    print(json.dumps(verify(manifest), ensure_ascii=False))


if __name__ == '__main__':
    main()
