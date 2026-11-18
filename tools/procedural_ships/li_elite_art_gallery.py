"""Verify LI elite generated images and create a local comparison gallery."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image
from rh_redesign_paths import TOPIC


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', default='round_01')
    args = parser.parse_args()
    assert args.round.startswith('round_') and args.round[6:].isdigit()
    topic = TOPIC/'li_elite'
    folder = topic/'concepts'/args.round
    pack = load(folder/'prompts.json')
    audit = load(topic/'source_audit.json')
    assert sha(audit['source_model']) == audit['source_sha256']
    cards, artifacts = [], []
    for v in pack['variants']:
        row = load(folder/(v['id']+'.json'))
        image = Path(row['destination'])
        assert image.resolve().parent == folder.resolve()
        assert sha(image) == sha(row['source'])
        with Image.open(image) as im:
            dimensions = list(im.size)
            assert im.format == 'PNG' and min(dimensions) >= 1024
            im.verify()
        row.update(sha256=sha(image), dimensions=dimensions, copy_matches_generated=True)
        artifacts.append(row)
        v.update(generated_output=image.as_posix(), review_output=image.as_posix(), generation_status='generated_for_review', review_status=row['status'])
        label = html.escape(v['id']+' — '+v['title_ru'])
        if row['status'] == 'rejected_by_user':
            label += ' — ОТКЛОНЁН'
        elif row['status'] == 'revision_required':
            label += ' — ТРЕБУЕТ ПЕРЕРАБОТКИ'
        filename = html.escape(image.name, quote=True)
        cards.append(f'<article><h2>{label}</h2><a href="{filename}" target="_blank">'
                     f'<img src="{filename}" alt="{label}" width="{dimensions[0]}" height="{dimensions[1]}"></a></article>')
    assert len(artifacts) == pack['requested_count'] and len(artifacts) > 0
    pack['status'] = ('rejected_by_user' if all(r['status'] == 'rejected_by_user' for r in artifacts)
                      else 'revision_required' if any(r['status'] == 'revision_required' for r in artifacts)
                      else 'complete_for_review')
    refs = list(pack['referenced_image_paths']) + pack.get('analysis_reference_paths', [])
    save(folder/'prompts.json', pack)
    save(folder/'artifacts.json', dict(completed=len(artifacts), artifacts=artifacts, approved_for_modeling=False,
        generation_mode='built-in image_gen', source_model=audit['source_model'],
        source_sha256=audit['source_sha256'], source_model_unchanged=True,
        references=[dict(path=p,sha256=sha(p)) for p in dict.fromkeys(refs)],
        limitations='Raster concept studies. Native cabin and mechanisms remain authoritative; no new mesh validation.'))
    content = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>LI pirate elite — L01 / L02</title>
<style>body{margin:0;background:#181d25;color:#e8ebf2;font:17px/1.55 system-ui,sans-serif}
header,main,footer{max-width:1800px;margin:auto;padding:24px}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
a{color:#acd2ff}article{background:#272f3b;padding:16px;border-radius:9px}h2{margin:0 0 15px;font-size:23px}
img{display:block;width:100%;height:auto}footer{color:#c5cbd6}@media(max-width:950px){main{grid-template-columns:1fr}}</style>
<header><h1>LI pirate elite — два первых направления</h1><p>Крупная перспектива, профиль и вид сверху на каждом листе. Нажмите на изображение для полного размера.</p>
<p><a href="../../README.md">Исследование модели и арт-деко Либерти</a> · <a href="README.md">Разбор результатов</a> · <a href="prompts.json">Точные промпты</a></p></header>
<main>'''+''.join(cards)+'''</main><footer>Пробные концепты, ещё не выбранные для моделирования. Родная кабина остаётся обязательной; новые формы люка и крыльев требуют проверки по реальной механике. Малые виды не являются точным чертежом.</footer></html>'''
    if args.round != 'round_01':
        codes = ' / '.join(v['id'] for v in pack['variants'])
        if len(artifacts) > 2:
            codes = f"{pack['variants'][0]['id']}–{pack['variants'][-1]['id']} · {len(artifacts)} вариантов"
        content = content.replace('L01 / L02', html.escape(codes))
        content = content.replace('два первых направления', html.escape(codes+' — новые формы корпуса'))
        content = content.replace('<main>', '<p style="padding:0 24px"><a href="../../comparison/README.md">Сравнение LI elite / Order / LI elite2</a></p><main>')
        if len(artifacts) == 1:
            content = content.replace('repeat(2,minmax(0,1fr))', 'minmax(0,1fr)')
    (folder/'index.html').write_text(content,encoding='utf8')
    print(json.dumps(dict(completed=len(artifacts), source_unchanged=True, images=[r['destination'] for r in artifacts])))


if __name__ == '__main__':
    main()
