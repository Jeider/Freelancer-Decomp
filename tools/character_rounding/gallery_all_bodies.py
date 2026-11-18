"""Review gallery for the complete offline body package, two views per model."""
from pathlib import Path
import json,html,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/all_bodies';GAME=Path('D:/Games/FL_MOD/DATA/CHARACTERS/BODIES')
reports=[];missing=[];stale=[]
for source in sorted(GAME.glob('*.dfm')):
 folder=OUT/source.stem
 if not (folder/'report.json').exists():missing.append(source.name);continue
 r=json.loads((folder/'report.json').read_text());reports.append(r)
 assert hashlib.sha256(source.read_bytes()).hexdigest()==r['source_sha256'],source.name
 for view in ('front','back'):
  path=folder/(view+'.png')
  if not path.exists():missing.append(source.stem+'/'+view);continue
  with Image.open(path) as im:im.verify()
  cache=folder/'render_source.json'
  if not cache.exists() or json.loads(cache.read_text())['sha256']!=r['output_sha256']:stale.append(source.stem+'/'+view)
validation=json.loads((OUT/'validation.json').read_text())
assert not validation['errors'],validation['errors']
assert not missing and not stale,(missing,stale)
assert validation['valid']==len(reports)
categories={'technical':'Технический образец / нестандартная форма: оставлен исходным','dense_existing':'Уже детализированная модель: прежняя форма сохранена; для Хетчер отдельно исправлен пояс','rigid_robot':'Робот: мягкая правка верхних поверхностей без превращения механики в ткань','armored':'Броня: исходные формы плеч и выступающих деталей сохранены; края рукавов округлены без расширения','tailored':'Одежда: ровные плечи, крой верха и вырез сохранены по оригиналу; края рукавов округлены без расширения'}
parts=['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>Все body — спереди и сзади</title><style>
body{background:#141c26;color:#e5edf5;font:17px/1.5 system-ui;max-width:1500px;margin:30px auto;padding:0 20px}a{color:#8acbff}header{position:sticky;top:0;background:#141c26ee;padding:12px;z-index:2}input,select{font:inherit;padding:8px;background:#253447;color:white;border:1px solid #789}section{border-top:1px solid #465262;padding:25px 0}img{width:100%;height:auto}summary{cursor:pointer;padding:12px;background:#253447}strong{color:#f2ca87}.meta{color:#aabbcc}.views{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:1000px){.views{grid-template-columns:1fr}}</style>
<h1>Все тела персонажей: обработка Mesh0</h1><p><strong>В игру не установлено. Головы не обрабатывались.</strong> Для каждого тела — ровно два основных вида: спереди и со спины. В обоих сравнительных кадрах слева исходная модель, справа подготовленный вариант. Камера, освещение и текстуры одинаковые.</p>
<p>Приоритет — наручи и сохранение кроя. Плечи сохраняют исходный силуэт без новых выпуклостей; у костюмов, платьев и форменных жилетов восстановлены плоскости верха, вырезы и стыки в области бюста. Для Hatcher передняя часть пояса выровнена в плоскую ленту.</p>
<p>Проверено: изменяется только Mesh0; остальные LOD, скелет, материалы и текстуры побайтно прежние. Веса и индексы проверены. Габариты ограничены исходным объёмом. Анимации всех вариантов в игре не проверялись; пакет предназначен для визуального просмотра перед установкой.</p>
<header><input id="search" placeholder="Поиск: li_, trent, darcy…"><select id="filter"><option value="">Все тела</option><option value="changed">Только изменённые</option><option value="armored">Броня / наручи</option><option value="tailored">Обычная одежда</option><option value="dense_existing">Уже детализированные</option><option value="rigid_robot">Роботы</option><option value="technical">Технические</option></select><span id="count"></span></header>''']
parts.append('<p><strong>Обновление краёв рукавов:</strong> расширение у кистей убрано. Скругление строится внутрь исходного контура среза, с сохранением его размера; переход выше по рукаву плавный.</p>')
parts.append('<p><strong>Обновление плеч и кроя:</strong> исправлены Sinсlair (sc_female1_body), br_karina, торговцы, бармены, мужская и женская элитная форма Рейнланда. Жёлтая вставка br_male_elite сохраняет исходную поверхность. Правка концов рукавов сохранена.</p>')
for r in reports:
 name=r['name'];status='Изменён' if r['changed'] else 'Сохранён исходным'
 parts.append(f'<section data-name="{name}" data-category="{r["category"]}" data-changed="{str(r["changed"]).lower()}"><h2>{name}</h2><p>{categories[r["category"]]}</p><p class="meta">{status}. Треугольники Mesh0: {r["triangles_before"]} → {r["triangles_after"]}. Профилей наручей: {r["cuff_profiles"]}.</p><div class="views">')
 for view,title in [('front','Спереди'),('back','Со спины')]:parts.append(f'<figure><figcaption>{title}: слева до, справа после</figcaption><a href="{name}/{view}.png"><img loading="lazy" src="{name}/{view}.png"></a></figure>')
 parts.append('</div></section>')
parts.append('''<script>function apply(){let q=document.querySelector('#search').value.toLowerCase(),f=document.querySelector('#filter').value,n=0;document.querySelectorAll('section').forEach(s=>{let ok=s.dataset.name.includes(q)&&(!f||(f==='changed'?s.dataset.changed==='true':s.dataset.category===f));s.hidden=!ok;if(ok)n++});document.querySelector('#count').textContent=' Показано: '+n}document.querySelector('#search').oninput=apply;document.querySelector('#filter').onchange=apply;apply()</script></html>''')
(OUT/'index.html').write_text(''.join(parts),encoding='utf8');(OUT/'inventory.json').write_text(json.dumps(reports,indent=2))
summary=dict(bodies=len(reports),changed=sum(r['changed'] for r in reports),cuff_ends_corrected=sum(r.get('cuff_end_revision',0)>0 for r in reports),unchanged=[r['name'] for r in reports if not r['changed']],views=len(reports)*2,head_files_written=0,game_installed=False)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
