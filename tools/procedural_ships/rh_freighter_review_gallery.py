"""Build a local HTML selection gallery; original generated PNGs are never edited."""
import argparse
import html
import json
from pathlib import Path

from rh_redesign_paths import TOPIC

TEMPLATE = '''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:light;--paper:#f3eddf;--ink:#272521;--accent:#8d392d;--line:#d2c8b7}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}
header,main,footer{max-width:1760px;margin:auto;padding:24px 32px}header{padding-bottom:10px}
.eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent)}
h1{font-size:clamp(26px,3vw,42px);line-height:1.15;margin:10px 0}p{margin:8px 0;color:#60594e}
button,a{touch-action:manipulation}button{font:inherit;cursor:pointer;border:1px solid var(--line);background:#fffaf0;color:var(--ink);border-radius:6px;padding:8px 13px}
button:hover{border-color:var(--accent)}button[aria-pressed="true"]{background:var(--accent);color:white;border-color:var(--accent)}
button:focus-visible,a:focus-visible{outline:3px solid #b87327;outline-offset:3px}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 12px}.summary{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}
#favorites{color:var(--accent);font-weight:600}main{padding-top:16px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
.grid.overview{grid-template-columns:repeat(3,minmax(0,1fr))}article{background:#fffaf1;border:1px solid var(--line);border-radius:8px;overflow:hidden}
article[hidden]{display:none}article.selected{border:2px solid var(--accent)}.image-link{display:block;background:#e9dfce;line-height:0}
.image-link img{display:block;width:100%;height:auto;aspect-ratio:3/2;object-fit:contain}
.caption{padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px}.caption h2{font-size:17px;margin:0;line-height:1.3}
.caption small{display:block;color:#7a7163;font-size:12px;margin-top:4px}.star{white-space:nowrap;font-size:13px}#empty{padding:40px;text-align:center}
article.accepted{outline:3px solid #436044;outline-offset:2px}.accepted-label{display:block;color:#345636;font-size:13px;margin-bottom:6px}
footer{font-size:13px;color:#706657}footer a{color:var(--accent)}
dialog{width:96vw;max-width:1800px;max-height:97vh;padding:14px;border:1px solid var(--line);border-radius:10px;background:#f8f1e5;color:var(--ink)}
dialog::backdrop{background:#171511dd}.viewer-toolbar{display:flex;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px}
.viewer-toolbar strong{font-size:18px}.viewer-actions{display:flex;gap:8px;flex-wrap:wrap}#full-image{display:block;width:100%;height:calc(90vh - 80px);object-fit:contain}
#original{color:var(--accent);font-size:13px}body.modal-open{overflow:hidden}
@media(max-width:900px){.grid,.grid.overview{grid-template-columns:1fr}header,main,footer{padding-left:14px;padding-right:14px}.caption{align-items:flex-start}.viewer-toolbar{align-items:flex-start;flex-direction:column}}
@media print{.controls,.star,dialog{display:none}header,main,footer{padding:10px}.grid{gap:8px}article{break-inside:avoid}}
</style></head><body>
<header><div class="eyebrow">Freelancer · Rheinland · Junkers</div><h1>__HEADING__</h1>
<p>__INTRO__</p>
<nav class="controls" aria-label="Фильтр вариантов">__FILTERS__<button id="only-favorites" aria-pressed="false">★ Избранное</button><button id="overview" aria-pressed="false">Плотный обзор</button></nav>
<div class="summary"><span id="count">__COUNT__ вариантов</span><span id="favorites" aria-live="polite">Избранные: —</span></div></header>
<main><div class="grid" id="grid">__CARDS__</div><p id="empty" hidden>В этой подборке пока нет отмеченных вариантов.</p></main>
<footer>Исходная кабина · характерный горб · массивные бортовые выступы с цилиндрами · без крыльев.<br>
<a href="README.md">Список PNG и описание комплекта</a> · <a href="__PROMPTS__">Промпты</a></footer>
<dialog id="viewer" aria-label="Просмотр концепта"><div class="viewer-toolbar"><div><strong id="full-title"></strong><br><a id="original" target="_blank" rel="noopener">Открыть исходный PNG</a></div><div class="viewer-actions"><button id="previous" aria-label="Предыдущий вариант">←</button><button id="next" aria-label="Следующий вариант">→</button><button id="full-star" aria-pressed="false">☆ В избранное</button><button id="close">Закрыть</button></div></div><img id="full-image" alt=""></dialog>
<script id="data" type="application/json">__DATA__</script>
<script>
const items=JSON.parse(document.getElementById('data').textContent);
const byId=new Map(items.map(x=>[x.id,x]));
const key=__STORAGE_KEY__;
let saved=[];try{const x=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(x))saved=x;}catch{}
const selected=new Set(saved.filter(x=>byId.has(x)));
let group='',onlyFavorites=false,current='';
const viewer=document.getElementById('viewer');
function starText(id){return selected.has(id)?'★ В избранном':'☆ В избранное';}
function refresh(){
 let count=0;
 for(const card of document.querySelectorAll('article[data-id]')){
  const id=card.dataset.id,item=byId.get(id),visible=(!group||item.group===group)&&(!onlyFavorites||selected.has(id));
  card.hidden=!visible;if(visible)count++;
  card.classList.toggle('selected',selected.has(id));
  const b=card.querySelector('.star');b.textContent=starText(id);b.setAttribute('aria-pressed',String(selected.has(id)));
 }
 document.getElementById('count').textContent='Показано: '+count+' / '+items.length;
 document.getElementById('favorites').textContent='Избранные: '+(items.filter(x=>selected.has(x.id)).map(x=>x.id).join(', ')||'—');
 document.getElementById('empty').hidden=count!==0;
 if(current){const b=document.getElementById('full-star');b.textContent=starText(current);b.setAttribute('aria-pressed',String(selected.has(current)));}
}
function toggle(id){if(selected.has(id))selected.delete(id);else selected.add(id);try{localStorage.setItem(key,JSON.stringify([...selected]));}catch{}refresh();}
function openItem(id){
 const item=byId.get(id);if(!item)return;current=id;
 const im=document.getElementById('full-image');im.src=item.file;im.alt=item.id+' — '+item.title;
 document.getElementById('full-title').textContent=im.alt;
 document.getElementById('original').href=item.file;
 refresh();if(!viewer.open)viewer.showModal();document.body.classList.add('modal-open');
}
function step(delta){let list=items.filter(x=>(!group||x.group===group)&&(!onlyFavorites||selected.has(x.id)));if(!list.length)list=items;let index=list.findIndex(x=>x.id===current);if(index<0)index=0;openItem(list[(index+delta+list.length)%list.length].id);}
for(const link of document.querySelectorAll('.image-link'))link.addEventListener('click',e=>{e.preventDefault();openItem(link.dataset.id);});
for(const button of document.querySelectorAll('.star'))button.addEventListener('click',()=>toggle(button.dataset.id));
for(const button of document.querySelectorAll('[data-group]'))button.addEventListener('click',()=>{group=button.dataset.group;for(const b of document.querySelectorAll('[data-group]'))b.setAttribute('aria-pressed',String(b===button));refresh();});
document.getElementById('only-favorites').addEventListener('click',e=>{onlyFavorites=!onlyFavorites;e.currentTarget.setAttribute('aria-pressed',String(onlyFavorites));refresh();});
document.getElementById('overview').addEventListener('click',e=>{const on=document.getElementById('grid').classList.toggle('overview');e.currentTarget.setAttribute('aria-pressed',String(on));});
document.getElementById('full-star').addEventListener('click',()=>toggle(current));
document.getElementById('previous').addEventListener('click',()=>step(-1));document.getElementById('next').addEventListener('click',()=>step(1));
document.getElementById('close').addEventListener('click',()=>viewer.close());viewer.addEventListener('close',()=>document.body.classList.remove('modal-open'));
document.addEventListener('keydown',e=>{if(viewer.open&&e.key==='ArrowLeft'){e.preventDefault();step(-1);}if(viewer.open&&e.key==='ArrowRight'){e.preventDefault();step(1);}});
refresh();
</script></body></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', default='round_05')
    args = parser.parse_args()
    root = (TOPIC / 'rh_freighter/concepts').resolve()
    folder = (root / args.round).resolve()
    if not folder.is_relative_to(root):
        raise ValueError('Gallery must remain in the RH freighter concept topic')
    manifest = json.loads((folder / 'artifacts.json').read_text(encoding='utf8'))
    items = []
    cards = []
    for row in manifest['artifacts']:
        path = Path(row['destination']).resolve()
        assert path.parent == folder and path.is_file()
        item = dict(id=row['id'], title=row['title_ru'], group=row['group_ru'], file=path.name)
        items.append(item)
        ident, title, group, filename = (html.escape(item[k], quote=True) for k in ['id', 'title', 'group', 'file'])
        form_link = ''
        if row.get('shape_image'):
            form = (folder / row['shape_image']).resolve()
            assert form.is_relative_to(folder) and form.is_file()
            safe = html.escape(row['shape_image'], quote=True)
            form_link = f'<small><a href="{safe}" target="_blank" rel="noopener">Чистая форма без окраски ↗</a></small>'
        if row.get('comparison_image'):
            comparison = (folder / row['comparison_image']).resolve()
            assert comparison.is_relative_to(root) and comparison.is_file()
            safe = html.escape(row['comparison_image'], quote=True)
            label = html.escape(row.get('comparison_label', 'Предыдущий вариант'))
            form_link += f'<small><a href="{safe}" target="_blank" rel="noopener">{label} ↗</a></small>'
        accepted = row['id'] == manifest.get('selected_concept')
        badge = '<strong class="accepted-label">БЕРЁМ В РАБОТУ · выбран пользователем</strong>' if accepted else ''
        css = ' class="accepted"' if accepted else ''
        cards.append(f'<article data-id="{ident}"{css}><a class="image-link" data-id="{ident}" href="{filename}" aria-label="Открыть {ident}: {title}"><img src="{filename}" alt="{ident} — {title}" loading="lazy" width="1536" height="1024"></a><div class="caption"><div>{badge}<h2>{ident} — {title}</h2><small>{group}</small>{form_link}</div><button class="star" data-id="{ident}" aria-pressed="false">☆ В избранное</button></div></article>')
    filters = [f'<button data-group="" aria-pressed="true">Все {len(items)}</button>']
    for group in dict.fromkeys(x['group'] for x in items):
        safe = html.escape(group, quote=True)
        filters.append(f'<button data-group="{safe}" aria-pressed="false">{safe}</button>')
    content = TEMPLATE.replace('__FILTERS__', ''.join(filters)).replace('__CARDS__', '\n'.join(cards))
    content = content.replace('__DATA__', json.dumps(items, ensure_ascii=False).replace('<', '\\u003c'))
    title = manifest.get('gallery_title', f'RH Junker Freighter — {items[0]["id"]}–{items[-1]["id"]}')
    heading = manifest.get('gallery_heading', f'{len(items)} вариантов пиратского грузовика')
    intro = manifest.get('gallery_intro', 'На каждом листе перспектива, профиль и вид сверху. Нажмите на арт, чтобы рассмотреть его крупно.')
    for token, value in [('__TITLE__',title),('__HEADING__',heading),('__INTRO__',intro),('__COUNT__',str(len(items))),('__PROMPTS__',manifest.get('prompt_files',['prompts.json'])[-1])]:
        content = content.replace(token, html.escape(value, quote=True))
    content = content.replace('__STORAGE_KEY__', json.dumps('rh-freighter-junker-' + folder.name + '-favorites'))
    dest = folder / 'index.html'
    dest.write_text(content, encoding='utf8')
    print(dest)


if __name__ == '__main__':
    main()
