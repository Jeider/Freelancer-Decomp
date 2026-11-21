"""Validate and index BW freighter concept rounds without touching B04 selection."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/ship_design/bw_family'
OUT = TOPIC / 'concepts/round_05'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', default='round_05')
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    if not args.round.startswith('round_') or not args.round[6:].isdigit():
        raise ValueError('Expected round_NN')
    OUT = TOPIC / 'concepts' / args.round
    audit = read(TOPIC / 'freighter/source_audit.json')
    sources = [dict(item, unchanged=sha(Path(item['path'])) == item['sha256'])
               for item in audit['assets']]
    assert all(item['unchanged'] for item in sources), 'Native source changed during concept study'
    pack = read(OUT / 'prompts.json')
    selection_path = TOPIC / 'freighter/selection.json'
    selection = read(selection_path) if selection_path.is_file() else None
    selected_id = None
    if selection:
        selected_art = (selection_path.parent / selection['art']).resolve()
        if selected_art.parent == OUT.resolve():
            assert sha(selected_art) == selection['art_sha256']
            selected_id = selection['concept_id']
            assert any(v['id'] == selected_id for v in pack['variants'])
    correction_path = OUT / 'correction_prompts.json'
    corrections = read(correction_path) if correction_path.exists() else dict(variants=[])
    calls = pack['variants'] + corrections['variants']
    results, refs = [], {}
    for call in calls:
        meta_path = OUT / (call['id'] + '.json')
        if not meta_path.exists() and args.allow_incomplete:
            continue
        meta = read(meta_path)
        if 'prompt' in meta:
            assert meta['prompt'] == call['prompt'], 'Actual prompt differs from stored recipe'
            assert meta['referenced_image_paths'] == call['referenced_image_paths']
        dest, source = Path(meta['destination']), Path(meta['source'])
        with Image.open(dest) as im:
            size = list(im.size)
            im.verify()
        assert min(size) >= 1024
        digest = sha(dest)
        assert digest == sha(source), 'Workspace image differs from built-in output'
        call['generated_output'] = dest.as_posix()
        call['generated_output_sha256'] = digest
        call['generation_status'] = 'generated_for_review'
        call['ordered_reference_hashes'] = []
        for name in call['referenced_image_paths']:
            p = Path(name)
            item = dict(path=p.as_posix(), sha256=sha(p))
            call['ordered_reference_hashes'].append(item)
            refs[p.as_posix()] = item
        results.append(dict(meta, sha256=digest, size=size, copy_matches_tool_output=True))
    for v in pack['variants']:
        if v.get('generated_output'):
            v['review_output'] = v['generated_output']
    for correction in corrections['variants']:
        if not correction.get('generated_output'):
            continue
        original = next(v for v in pack['variants'] if v['id'] == correction['base_variant'])
        original['review_output'] = correction['generated_output']
        history = original.setdefault('correction_history', [])
        entry = dict(id=correction['id'], prompt_file=correction_path.as_posix(),
                     generated_output=correction['generated_output'])
        history[:] = [x for x in history if x['id'] != correction['id']] + [entry]
    ready = [v for v in pack['variants'] if v.get('review_output')]
    pack['status'] = 'complete_for_review' if len(ready) == pack['requested_count'] else 'generation_in_progress'
    if selected_id:
        pack['status'] = 'user_selected_concept_for_future_work'
        pack['selected_id'] = selected_id
        pack['selection_file'] = selection_path.as_posix()
        for v in pack['variants']:
            v['selected_for_work'] = v['id'] == selected_id
            v['approved_for_modeling'] = v['id'] == selected_id
    assert args.allow_incomplete or len(ready) == pack['requested_count']
    write(OUT / 'prompts.json', pack)
    if correction_path.exists():
        write(correction_path, corrections)
    write(OUT / 'generation_results.json', dict(calls=results))
    write(OUT / 'source_checks.json', dict(verified=True, sources=sources, references=list(refs.values()),
                                         source_geometry_edited=False, game_launched=False, installed=False))
    cards = []
    for v in ready:
        filename = Path(v['review_output']).name
        title = html.escape(v['id'] + ' — ' + v['title_ru'])
        group = html.escape(v.get('group_ru', 'Первые направления'))
        selected_class = ' class="selected"' if v['id'] == selected_id else ''
        badge = '<p class="badge">ИДЕАЛЬНЫЙ — БЕРЁМ В РАБОТУ</p>' if v['id'] == selected_id else ''
        cards.append(f'<article id="{v["id"]}"{selected_class} data-group="{group}"><h2>{title}</h2>{badge}'
                     f'<p class="group">{group}</p><a href="{filename}" target="_blank">'
                     f'<img loading="lazy" src="{filename}" alt="{title}"></a>'
                     f'<label><input type="checkbox" value="{v["id"]}"> В избранное для сравнения</label></article>')
    content = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BW pirate freighter — поиск формы</title>
<style>body{margin:0 auto;padding:28px;max-width:1550px;background:#1b2026;color:#ece9e0;font:17px/1.55 system-ui}
a{color:#eac18a}h1{font-size:30px}h2{font-size:20px}article{padding:14px;background:#252c34;border-radius:8px}
img{display:block;width:100%;height:auto;border-radius:5px}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
p{max-width:1050px}.note,.group{color:#c4c7ca;font-size:15px}label{display:block;padding-top:10px;cursor:pointer}
nav{position:sticky;top:0;padding:12px;background:#1b2026ed;z-index:2}button,select{padding:8px;margin:5px;background:#343f4c;color:white;border:1px solid #66717c;border-radius:4px}
article[hidden]{display:none}body.large .cards{grid-template-columns:1fr}@media(max-width:850px){.cards{grid-template-columns:1fr}}</style>
<h1>BW pirate freighter — поиск формы</h1>
<p>__GALLERY_INTRO__</p>
<p>Передний и задний 3/4 показывают корабль целиком; ниже — профиль, верх и корма.
__SELECTION_STATUS__</p>
<p><a href="../../freighter/README.md">Исходник и механика</a> · <a href="README.md">Разбор вариантов</a> ·
<a href="prompts.json">Точные промпты</a> · <a href="../round_05/index.html">Исходные BF01/BF02</a></p>
<p class="note">Кабина переносится из исходного CMP без изменений. Арт не является геометрическим доказательством её точности
или проверкой анимационных зазоров. Полная история генерации сохранена.</p>'''
    content = content.replace('__GALLERY_INTRO__', html.escape(pack.get('gallery_intro',
        'Исходник: bw_pir_freighter. Развиваем понравившиеся BF01/BF02: грузовой объём, '
        'боковые ниши, крепления двигателей, короткие задвигающиеся крылья и нижний киль.')))
    choice = ('Выбран ' + selected_id + ': ИДЕАЛЬНЫЙ — БЕРЁМ В РАБОТУ. '
              '<a href="../../freighter/SELECTED_CONCEPT.md">Карточка для моделирования</a>.'
              if selected_id else 'Это пробные концепты, выбор ещё не сделан.')
    content = content.replace('__SELECTION_STATUS__', choice)
    content = content.replace('</style>', 'article.selected{outline:3px solid #eac18a}.badge{color:#eac18a;font-weight:700}</style>')
    if pack.get('base_concept') == 'BF02':
        content += '<p><a href="../round_05/bw_freighter_BF02_sheet.png" target="_blank">Открыть исходный BF02 для сравнения</a></p>'
    groups = sorted({v.get('group_ru', 'Первые направления') for v in ready})
    options = ''.join(f'<option>{html.escape(g)}</option>' for g in groups)
    navigation = f'<p>Готово {len(ready)} из {pack["requested_count"]}. Нажмите на лист, чтобы открыть оригинал.</p>'
    navigation += '<nav><select id="filter"><option value="">Все направления</option>' + options + '</select>'
    navigation += '<button id="large">Крупные листы</button><button id="favorites">Только избранное</button><span id="chosen"></span></nav>'
    script = '''<script>
const key='bw-freighter-'+location.pathname;let selected=new Set();try{selected=new Set(JSON.parse(localStorage.getItem(key)||'[]'))}catch(e){}
let only=false;const cards=[...document.querySelectorAll('article')];
function refresh(){const filter=document.querySelector('#filter').value;for(const card of cards){card.hidden=(filter&&card.dataset.group!==filter)||(only&&!selected.has(card.id));card.querySelector('input').checked=selected.has(card.id)}
document.querySelector('#chosen').textContent='Избранное: '+([...selected].sort().join(', ')||'пока нет');try{localStorage.setItem(key,JSON.stringify([...selected]))}catch(e){}}
for(const input of document.querySelectorAll('input'))input.onchange=()=>{input.checked?selected.add(input.value):selected.delete(input.value);refresh()};
document.querySelector('#filter').onchange=refresh;document.querySelector('#large').onclick=()=>document.body.classList.toggle('large');
document.querySelector('#favorites').onclick=()=>{only=!only;document.querySelector('#favorites').textContent=only?'Показать все':'Только избранное';refresh()};refresh();
</script>'''
    (OUT / 'index.html').write_text(content + navigation + '<div class="cards">' + '\n'.join(cards) + '</div>' + script + '</html>\n', encoding='utf8')
    write(OUT / 'artifacts.json', dict(topic='bw_family', ship='bw_pir_freighter', round=args.round,
                                     status='selected_for_future_work' if selected_id else 'candidate_for_user_review', selected_id=selected_id,
                                     gallery=(OUT / 'index.html').as_posix(), outputs=results))
    print('Verified', len(results), 'generated images;', len(refs), 'distinct references; native assets unchanged.')
    print(OUT / 'index.html')


if __name__ == '__main__':
    main()
