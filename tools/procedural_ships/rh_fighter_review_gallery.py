"""Verify saved fighter concept PNGs and build a local selection gallery.

Original images are read only. Favorites are browser-local preferences and do
not mark a concept approved for modeling.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image

from rh_freighter_review_gallery import TEMPLATE
from rh_redesign_paths import TOPIC


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', default='round_05')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    fighter = (TOPIC / 'rh_fighter').resolve()
    root = fighter / 'concepts'
    folder = (root / args.round).resolve()
    if not folder.is_relative_to(root):
        raise ValueError('Gallery must stay within the fighter concept topic')
    pack = json.loads((folder / 'prompts.json').read_text(encoding='utf8'))
    selection_path = fighter / 'selection.json'
    selection = json.loads(selection_path.read_text(encoding='utf8')) if selection_path.is_file() else {}
    selected_id = None
    selected_entry = None
    for candidate in (selection, selection.get('rear_view', {})):
        if candidate.get('status') == 'accepted_for_modeling':
            candidate_art = (fighter / candidate['art']).resolve()
            if candidate_art.parent == folder:
                selected_entry = candidate
                selected_art = candidate_art
                selected_id = candidate['concept_id']
    expected = [v['id'] for v in pack['variants']]
    assert len(set(expected)) == len(expected) == pack['requested_count']
    artifacts, missing = [], []
    for variant in pack['variants']:
        meta = folder / (variant['id'] + '.json')
        if not meta.is_file():
            missing.append(variant['id'])
            continue
        row = json.loads(meta.read_text(encoding='utf8'))
        path = Path(row['destination']).resolve()
        assert row['id'] == variant['id']
        assert path.parent == folder and path.is_file()
        with Image.open(path) as im:
            dimensions = list(im.size)
            image_format = im.format
            im.verify()
        digest = sha(path)
        assert image_format == 'PNG' and min(dimensions) >= 1024
        assert digest == sha(Path(row['source']))
        if row['id'] == selected_id:
            assert path == selected_art and digest == selected_entry['art_sha256']
            row['status'] = 'accepted_for_modeling'
        artifacts.append(dict(row, dimensions=dimensions, sha256=digest,
                              bytes=path.stat().st_size,
                              copy_matches_generated=True))
    if args.require_complete and missing:
        raise RuntimeError('Missing requested variants: ' + ', '.join(missing))
    reference_paths = dict.fromkeys(p for v in pack['variants']
                                    for p in v['referenced_image_paths'])
    audit = json.loads((fighter / 'source_audit.json').read_text(encoding='utf8'))
    source_path = Path(audit['source_path'])
    source_hash = sha(source_path)
    assert source_hash == audit['source']['sha256']
    review_path = folder / 'visual_review.json'
    manifest = dict(
        generation_mode='built-in image_gen', requested_count=len(expected),
        completed_count=len(artifacts), missing_ids=missing,
        status='complete' if not missing else 'in_progress',
        approved_for_modeling=selected_id is not None, selected_concept=selected_id,
        source_cmp=source_path.as_posix(), source_sha256=source_hash,
        source_unchanged=True,
        references=[dict(path=p, sha256=sha(Path(p))) for p in reference_paths],
        artifacts=artifacts, prompt_files=['prompts.json'],
        visual_review=json.loads(review_path.read_text(encoding='utf8'))
        if review_path.is_file() else None,
        limitations='Raster concepts; exact cockpit geometry, drum volume and '
                    'new animation clearance require future 3D validation.',
    )
    (folder / 'artifacts.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    items, cards = [], []
    for row in artifacts:
        item = dict(id=row['id'], title=row['title_ru'], group=row['group_ru'],
                    file=Path(row['destination']).name)
        items.append(item)
        ident, title, group, filename = (
            html.escape(item[k], quote=True) for k in ('id', 'title', 'group', 'file'))
        accepted = item['id'] == selected_id
        css = ' class="accepted"' if accepted else ''
        badge = '<strong class="accepted-label">БЕРЁМ В РАБОТУ · выбран пользователем</strong>' if accepted else ''
        cards.append(
            f'<article data-id="{ident}"{css}><a class="image-link" data-id="{ident}" '
            f'href="{filename}" aria-label="Открыть {ident}: {title}">'
            f'<img src="{filename}" alt="{ident} — {title}" loading="lazy" '
            f'width="1536" height="1024"></a><div class="caption"><div>'
            f'{badge}<h2>{ident} — {title}</h2><small>{group}</small></div>'
            f'<button class="star" data-id="{ident}" aria-pressed="false">'
            '☆ В избранное</button></div></article>')
    filters = [f'<button data-group="" aria-pressed="true">Все {len(items)}</button>']
    for group in dict.fromkeys(x['group'] for x in items):
        safe = html.escape(group, quote=True)
        filters.append(f'<button data-group="{safe}" aria-pressed="false">{safe}</button>')
    content = TEMPLATE.replace('__FILTERS__', ''.join(filters))
    content = content.replace('__CARDS__', '\n'.join(cards))
    content = content.replace('__DATA__', json.dumps(items, ensure_ascii=False).replace('<', '\\u003c'))
    tokens = dict(
        __TITLE__='RH fighter — F05–F14',
        __HEADING__='Драугр — 10 вариантов истребителя',
        __INTRO__='Развитие F03/F04: повёрнутый барабан, два двигателя, разные '
                  'крепления крыльев и формы корпуса. Нажмите на лист для '
                  'увеличения; звёздочкой можно отметить понравившиеся варианты.',
        __COUNT__=str(len(items)), __PROMPTS__='prompts.json',
    )
    for key in ('title', 'heading', 'intro'):
        if key in pack.get('presentation', {}):
            tokens['__' + key.upper() + '__'] = pack['presentation'][key]
    if selected_id:
        tokens['__HEADING__'] = f'Драугр — {selected_id} берём в работу'
        tokens['__INTRO__'] = f'Пользователь выбрал {selected_id} для моделирования. Остальные листы — архив поиска. Нажмите на арт для увеличения.'
        if selected_entry is not selection:
            tokens['__HEADING__'] = pack['presentation']['heading']
            tokens['__INTRO__'] = pack['presentation']['intro']
    for token, value in tokens.items():
        content = content.replace(token, html.escape(value, quote=True))
    content = content.replace('__STORAGE_KEY__', json.dumps('rh-fighter-' + folder.name + '-favorites'))
    content = content.replace(
        'Исходная кабина · характерный горб · массивные бортовые выступы с цилиндрами · без крыльев.',
        'Родная кабина · барабан без увеличения · два двигателя · крылья в полёте. '
        'Избранное сохраняется только в браузере и не означает выбор для моделирования.')
    assert '__CARDS__' not in content and '__STORAGE_KEY__' not in content
    (folder / 'index.html').write_text(content, encoding='utf8')
    print(json.dumps(dict(completed=len(artifacts), requested=len(expected),
                          missing=missing, source_unchanged=True,
                          gallery=(folder / 'index.html').as_posix()),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
