"""Verify and index BH freighter concept art; no model or game-data writes."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/ship_design/bh_family'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--round', default='round_01')
    ap.add_argument('--allow-incomplete', action='store_true')
    args = ap.parse_args()
    assert args.round.startswith('round_') and args.round[6:].isdigit()
    folder = TOPIC / 'concepts' / args.round
    pack = read(folder/'prompts.json')
    corrections_path = folder/'correction_prompts.json'
    corrections = read(corrections_path) if corrections_path.exists() else dict(variants=[])
    source_checks = [dict(row, unchanged=sha(Path(row['path']))==row['sha256'])
                     for row in read(TOPIC/'manifest.json')['sources']]
    assert all(r['unchanged'] for r in source_checks), 'Pinned source changed; review before continuing'
    results, references = [], {}
    for v in pack['variants']+corrections['variants']:
        meta_path = folder/(v['id']+'.json')
        if not meta_path.exists() and args.allow_incomplete:
            continue
        meta = read(meta_path)
        assert meta['prompt']==v['prompt'] and meta['referenced_image_paths']==v['referenced_image_paths']
        assert meta['parameters']==v['parameters']
        source, dest = Path(meta['source']), Path(meta['destination'])
        digest = sha(dest)
        assert digest==sha(source)
        with Image.open(dest) as im:
            size = list(im.size)
            im.verify()
        assert min(size)>=1024
        hashes = [dict(path=p, sha256=sha(Path(p))) for p in v['referenced_image_paths']]
        if v.get('ordered_reference_hashes'):
            assert v['ordered_reference_hashes']==hashes
        references.update({r['path']:r for r in hashes})
        v.update(generated_output=dest.as_posix(), generated_output_sha256=digest,
                 generation_status='generated_for_review', ordered_reference_hashes=hashes)
        results.append(dict(meta, sha256=digest, size=size, copy_matches_tool_output=True))
    for v in pack['variants']:
        if v.get('generated_output'):
            v['review_output']=v['generated_output']
    for correction in corrections['variants']:
        if correction.get('generated_output'):
            original = next(v for v in pack['variants'] if v['id']==correction['base_variant'])
            original['review_output']=correction['generated_output']
            original.setdefault('correction_history', [])
            entry = dict(id=correction['id'], prompt_file=corrections_path.as_posix(), output=correction['generated_output'])
            original['correction_history']=[r for r in original['correction_history'] if r['id']!=correction['id']]+[entry]
    ready = [v for v in pack['variants'] if v.get('review_output')]
    assert args.allow_incomplete or len(ready)==pack['requested_count']
    selected_id=pack.get('selected_id')
    alternative_ids=pack.get('alternative_ids', [])
    if selected_id:
        assert selected_id in {v['id'] for v in ready}
    assert set(alternative_ids).issubset({v['id'] for v in ready})
    pack['status']='concept_selected_for_modeling' if selected_id else ('complete_for_review' if len(ready)==pack['requested_count'] else 'generation_in_progress')
    write(folder/'prompts.json', pack)
    if corrections_path.exists():
        write(corrections_path, corrections)
    write(folder/'generation_results.json', dict(calls=results))
    write(folder/'source_checks.json', dict(verified=True, source_checks=source_checks, references=list(references.values()),
                                          model_changed=False, installed=False))
    cards=[]
    overview=[]
    for v in ready:
        filename=Path(v['review_output']).name
        chosen=' — БЕРЁМ В РАБОТУ' if v['id']==selected_id else (' — АЛЬТЕРНАТИВА' if v['id'] in alternative_ids else '')
        cards.append(f'<article id="{v["id"]}"><h2>{html.escape(v["id"]+" — "+v["title_ru"]+chosen)}</h2>'
                     f'<p>{html.escape(v["brief_ru"])}</p><a href="{filename}" target="_blank">'
                     f'<img loading="lazy" src="{filename}" alt="{v["id"]}"></a></article>')
        overview.append(f'<a href="#{v["id"]}"><img loading="lazy" src="{filename}" alt="{v["id"]}">'
                        f'<strong>{html.escape(v["id"]+" — "+v["title_ru"]+chosen)}</strong></a>')
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>body{margin:auto;padding:30px;max-width:1500px;background:#182129;color:#e4e8e9;font:17px/1.6 system-ui}
a{color:#a4d2cd}h1{font-size:32px}h2{font-size:23px}p{max-width:1100px}article{margin:24px 0;padding:20px;background:#26333d;border-radius:8px}
img{width:100%;height:auto;display:block}.note{color:#b4c2cb;font-size:15px}nav{padding:12px 0}nav a{padding-right:18px}
.overview{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.overview a{background:#26333d;padding:10px;text-decoration:none;font-size:14px}
@media(max-width:900px){.overview{grid-template-columns:repeat(2,minmax(0,1fr))}body{padding:15px}}</style>
<h1>__TITLE__</h1><p>__INTRO__</p>
<p>Каждый лист: полный передний и задний 3/4, профиль, верх и корма. Нажмите на изображение, чтобы открыть оригинал.</p>
<p class="note">Это поисковые концепты. В модели сохраняем исходное остекление с рамой;
точность изображения и зазоры анимации требуют отдельной проверки. Старый округлый нос с нижней частью не закреплён.</p>
<nav><a href="../../index.html">Исследование семейства</a><a href="README.md">Направления поиска</a><a href="prompts.json">Точные промпты</a></nav>'''
    title=pack.get('gallery_title', f'BH freighter — {pack["requested_count"]} идей формы')
    intro=pack.get('gallery_intro', 'Обычный грузовик BH: основа li_freighter, второй ориентир bw_freighter. Неизменны остекление и непосредственная рама; окружающий корпус свободно перерабатывается.')
    page=page.replace('__TITLE__',html.escape(title)).replace('__INTRO__',html.escape(intro))
    if selected_id:
        page+=f'<p><strong>Выбран {html.escape(selected_id)} — БЕРЁМ В РАБОТУ.</strong> <a href="../../freighter/SELECTED_CONCEPT.md">Карточка передачи</a></p>'
    if alternative_ids:
        page+=f'<p><strong>Альтернатива: {html.escape(", ".join(alternative_ids))}.</strong> Распределение между обычным и пиратским грузовиками пока не выбрано.</p>'
    page+=f'<p>Готово {len(ready)} из {pack["requested_count"]}.</p>'
    if pack['requested_count']>5:
        page+='<div class="overview">'+''.join(overview)+'</div>'
    page+=''.join(cards)+'</html>\n'
    (folder/'index.html').write_text(page,encoding='utf8')
    write(folder/'artifacts.json',dict(topic='bh_family',ship='bh_freighter',variant=pack.get('variant','regular_non_pirate'),round=args.round,
                                     status=pack['status'],selected_id=selected_id,alternative_ids=alternative_ids,
                                     role_assignment=pack.get('role_assignment'),gallery=(folder/'index.html').as_posix(),outputs=results))
    print('Verified',len(results),'calls;',len(ready),'concepts;',len(references),'references; pinned sources unchanged.')
    print(folder/'index.html')


if __name__=='__main__':
    main()
