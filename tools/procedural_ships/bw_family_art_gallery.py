"""Verify and index generated BW family boards without changing image pixels."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image
from rh_redesign_paths import TOPIC


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', default='round_01')
    args = parser.parse_args()
    parent = (TOPIC/'bw_family/concepts').resolve()
    folder = (parent/args.round).resolve()
    assert folder.is_relative_to(parent)
    pack = read(folder/'prompts.json')
    selection_path = TOPIC/'bw_family/selection.json'
    selection = read(selection_path) if selection_path.is_file() else None
    selected_id = None
    if selection and (selection_path.parent/selection['art']).resolve().parent == folder:
        selected_id = selection['concept_id']
    artifacts = []
    cards = []
    overview = []
    for v in pack['variants']:
        meta_path = folder/(v['id']+'.json')
        row = read(meta_path)
        path = Path(row['destination']).resolve()
        assert row['id'] == v['id'] and path.parent == folder
        assert path.is_file() and sha(path) == sha(Path(row['source']))
        with Image.open(path) as im:
            dimensions, fmt = list(im.size), im.format
            im.verify()
        assert fmt == 'PNG' and min(dimensions) >= 1024
        v['generated_output'] = row.get('initial_output', path.as_posix())
        v['review_output'] = path.as_posix()
        v['generation_status'] = 'generated_for_review'
        row.update(sha256=sha(path), dimensions=dimensions, copy_matches_generated=True)
        artifacts.append(row)
        label = html.escape(v['id']+' — '+v['title_ru'])
        chosen = v['id'] == selected_id
        card_class = ' class="chosen"' if chosen else ''
        badge = '<p class="badge">БЕРЁМ В РАБОТУ · начинаем с ELITE</p>' if chosen else ''
        if chosen:
            assert sha(path) == selection['art_sha256']
            label += ' ★'
        filename = html.escape(path.name, quote=True)
        anchor = html.escape(v['id'], quote=True)
        overview.append(f'<a href="#{anchor}"{card_class}><img src="{filename}" alt="{label}" '
                        f'width="{dimensions[0]}" height="{dimensions[1]}" loading="lazy">'
                        f'<span>{label}</span></a>')
        cards.append(f'<article id="{anchor}"{card_class}><h2>{label}</h2>{badge}<a href="{filename}" target="_blank">'
                     f'<img src="{filename}" alt="{label}" loading="lazy" width="{dimensions[0]}" '
                     f'height="{dimensions[1]}"></a><p><a href="{filename}">Открыть полный PNG</a></p></article>')
    assert len(artifacts) == pack['requested_count']
    prompt_files = ['prompts.json']
    reference_paths = list(pack['referenced_image_paths'])
    for v in pack['variants']:
        reference_paths.extend(v.get('referenced_image_paths', []))
    corrections_path = folder/'correction_prompts.json'
    if corrections_path.is_file():
        corrections = read(corrections_path)
        prompt_files.append('correction_prompts.json')
        for v in corrections['variants']:
            reference_paths.extend(v['referenced_image_paths'])
            output = next(r['destination'] for r in artifacts if r['id'] == v['id'])
            v['generated_output'] = output
            v['generation_status'] = 'generated_for_review'
        corrections['status'] = 'complete_for_review'
        write(corrections_path, corrections)
    references = [dict(path=p, sha256=sha(Path(p))) for p in dict.fromkeys(reference_paths)]
    sources = []
    for key in ('fighter', 'elite', 'vheavy_fighter'):
        audit = read(TOPIC/'bw_family'/key/'source_audit.json')
        assert sha(Path(audit['source_model'])) == audit['source_sha256']
        sources.append(dict(ship=key, path=audit['source_model'], sha256=audit['source_sha256']))
    pack['status'] = 'complete_for_review'
    if selected_id:
        pack['selected_concept'] = selected_id
        pack['selection_status'] = selection['status']
        pack['selection_scope_file'] = '../../selection.json'
    write(folder/'prompts.json', pack)
    write(folder/'artifacts.json', dict(generation_mode='built-in image_gen', requested_count=pack['requested_count'],
          completed_count=len(artifacts), approved_for_modeling=False, artifacts=artifacts,
          references=references, source_models=sources, source_models_unchanged=True,
          prompt_files=prompt_files, selected_direction=selection if selected_id else None,
          limitations='Raster studies; source cockpit remains mandatory. '
          'New geometry, mechanisms and projection consistency require future model validation.'))
    content = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__GALLERY_TITLE__</title>
<style>body{margin:0;background:#171c23;color:#e5e8ee;font:17px/1.5 system-ui,sans-serif}
header,main,footer{max-width:1700px;margin:auto;padding:24px}h1{margin:0 0 12px}
a{color:#b8d8ff}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
article{background:#252d38;border-radius:10px;padding:16px}h2{font-size:21px;margin:0 0 16px}
.chosen{outline:3px solid #e0b554}.badge{color:#ffdb86;font-weight:700}.selection{padding:16px;background:#343126;border-left:4px solid #e0b554}
img{display:block;width:100%;height:auto}footer{color:#bac3cf}
#overview{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:24px}
#overview a{display:block;background:#252d38;padding:8px;border-radius:6px;text-decoration:none}
#overview span{display:block;font-size:14px;margin-top:8px}html{scroll-behavior:smooth}
@media(max-width:850px){main{grid-template-columns:1fr}#overview{grid-template-columns:repeat(2,minmax(0,1fr))}}</style>
<header><h1>__GALLERY_TITLE__</h1>__SELECTION__<p>__GALLERY_INTRO__ На каждом листе:
fighter, elite, vheavy_fighter. Нажмите на изображение для полного размера.</p>
<p><a href="README.md">Разбор результатов</a> · <a href="prompts.json">Точные промпты</a> ·
<a href="../../README.md">Исходники и механика семейства</a></p>
<nav id="overview" aria-label="Все варианты">__OVERVIEW__</nav></header>
<main>'''+''.join(cards)+'''</main><footer>__SELECTION_FOOTER__
Обязательный эталон кабины — исходная модель. Новые модели не создавались.</footer></html>'''
    content = content.replace('__GALLERY_TITLE__', html.escape(pack.get('gallery_title', 'BW pirate — B01 / B02')))
    content = content.replace('__GALLERY_INTRO__', html.escape(pack.get('gallery_intro', 'Пробные направления для сравнения.')))
    content = content.replace('__OVERVIEW__', ''.join(overview))
    note = (f'{html.escape(selected_id)} — основное направление, берём в работу. '
            'Начинаем с ELITE. VHEAVY на листе не утверждён; возможен будущий микс решений.') if selected_id else ''
    banner = f'<p class="selection">{note} <a href="../../SELECTED_CONCEPT.md">Карточка выбора</a></p>' if note else ''
    content = content.replace('__SELECTION__', banner)
    content = content.replace('__SELECTION_FOOTER__', note or 'Концепты для обсуждения; направление ещё не выбрано.')
    (folder/'index.html').write_text(content, encoding='utf8')
    print(json.dumps(dict(completed=len(artifacts), images=[r['destination'] for r in artifacts],
                         source_models_unchanged=True), ensure_ascii=False))


if __name__ == '__main__':
    main()
