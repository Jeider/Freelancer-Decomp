"""Build a portable local review page and verify the game was left untouched."""
from pathlib import Path
import json,hashlib,shutil,html
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/character_rounding/li'
records=json.loads((OUT/'inventory.json').read_text());arts=[]
verified_images=0
for r in records:
 for name in (['comparison.png','detail_clay.png'] if r['kind']=='BODIES' else ['reference.png']):
  with Image.open(OUT/r['name']/name) as im:im.verify()
  verified_images+=1
for name in ('belt.png','belt_clay.png'):
 with Image.open(OUT/'li_hatcher_body'/name) as im:im.verify()
 verified_images+=1
for p in sorted(Path('D:/work/ART').rglob('*')):
 if p.is_file():
  with Image.open(p) as im:arts.append(dict(path=str(p),size=im.size))
(OUT/'art_inventory.json').write_text(json.dumps(arts,indent=2))
notes={
'li_bartender_body':([], 'Рукава и ворот округлять локально; прямую кромку жилета, манжеты и пояс не превращать в валики. Прямого подтверждённого арта нет.'),
'li_commtrader_body':([], 'Локти, рукава и обувь — плавнее. Планки одежды, пояс и карманы — плоские. Без точного арта опираться на исходный силуэт.'),
'li_female_elite_body':(['l.elitwo.jpg'],'Округлить парные наплечники и сечения наручей; сохранить ширину пелерины. Нижняя кромка пелерины и ремень остаются чёткими; сумки не надувать.'),
'li_female_guard_body':(['lib_gw.jpg'],'Сечения наручей, колени, наплечники и голенища — плавнее. Диагональная перевязь остаётся лентой, границы цветных вставок требуют отдельной проверки UV.'),
'li_hatcher_body':(['juniconcept01.jpg','l19.JPG'],'Сохранить уже принятые скругления наручей и жилета. У пояса отключено округление, передние кромки выровнены в параллельные линии с сохранением диагонального наклона. Поверхность плоская поперёк ширины ленты, но обходит тело по окружности. Этот дополнительный вариант пояса пока только в превью; перед игрой требуется повторный экспорт DFM.'),
'li_male_elite_body':(['elite_li.jpg'],'Парные плечевые дуги и наручи сгладить в исходном размере. Пелерины, пряжки, подсумки и ремень сохранить плоскими. Канты — ровной ширины, без округления всего торса.'),
'li_male_guard_body':(['g._lib.jpg'],'Наплечники, наколенники и наручи — плавные дуги. Пояс и застёжки не сглаживать поперёк толщины. У сапог сохранить плоскую подошву.'),
'li_manhattan_bartender_body':(['manbartenderconcept01.jpg'],'Округлить сечения подвёрнутых рукавов и плечи. Фартук — лист ткани с ровным низом; жилет и пояс не выпячивать. Полноту персонажа сохранить.'),
'li_rockford_body':(['diplomatconcept.jpg','l13.JPG'],'Арт подписан Rockwell, имя меша Rockford: соответствие по костюму требует визуального подтверждения. Сгладить рукава и обувь; лацканы, диагональный борт и низ пиджака оставить прямыми.'),
'li_scrote_body':(['kingconcept01.jpg','l15.JPG'],'На файле kingconcept01 написано Major Scrote. Сгладить наплечники и края жилета, но сохранить прямой низ и плоский ремень. Накладки локтей и коленей не превращать в шарики.'),
'li_shipdealer_body':([], 'Прямого арта нет. Выправить круглые сечения рукавов и обуви; плоские планки, ремень и карманы сохранить. Проверку полос делать по UV отдельно.'),
'li_tilton_body':(['l18.JPG','l17.JPG'],'Двойные плечевые дуги и наручи округлить, оставив зазор между дугами. Перевязь и пояс — плоские полосы, нижний край накидки — чёткий.'),
'li_tilton_body_alt':(['l18.JPG','l17.JPG'],'Проверять как отдельный вариант Tilton: одинаковые правила формы, но собственные текстуры и возможные отличия геометрии. Не подменять основным вариантом автоматически.'),
}
artdir=OUT/'arts';artdir.mkdir(exist_ok=True)
for p in Path('D:/work/ART/LI').iterdir():
 if p.is_file():shutil.copy2(p,artdir/p.name)
parts=['''<!doctype html><html lang="ru"><meta charset="utf-8"><title>LI — скругления персонажей</title><style>
body{background:#151b23;color:#e6edf3;font:17px/1.55 system-ui;max-width:1250px;margin:40px auto;padding:0 22px}a{color:#8fceff}section{border-top:1px solid #465364;padding:24px 0}img{max-width:100%;height:auto}figure{margin:15px 0}.arts img{max-height:330px;max-width:40%;object-fit:contain}.heads{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}small{color:#aebdca}summary{cursor:pointer;padding:10px;background:#263140}nav a{display:inline-block;margin:5px 12px 5px 0}strong{color:#ffd386}</style>
<h1>LI: план правки формы и первые превью</h1><p><strong>В игру ничего не установлено.</strong> Слева — текущая игровая модель, справа — пробный вариант Mesh0. Одинаковые свет, камера и текстура; без новых шейдеров. Это настоящие рендеры геометрии в Blender, не нарисованные макеты.</p>
<p>13 тел: сравнения до/после. 12 голов: обзор текущего состояния, без изменения лиц. Генерализованное сглаживание для лица не применяется. Варианты hat рассматриваются отдельно, с сохранением посадки в шлем.</p>
<h2>Правила для всей серии персонажей</h2><ol><li>Сохранять исходные пропорции и максимальную ширину; круглая деталь получает дополнительные сегменты, а не больший радиус.</li><li>Ремни, перевязи, пряжки, лацканы и жёсткие канты — плоские поверхности с чёткими кромками. Не применять ко всему костюму единый Subdivision Surface.</li><li>Полосы геометрии выравнивать по центральной линии с постоянной шириной. Нарисованные полосы исправлять в UV после проверки швов; в этих превью UV только интерполированы.</li><li>Первый проход — небольшое сглаживание и округление малых замкнутых контуров наручей. Для остальных тел смещение ограничено 6 мм и исходным общим bounding box; локальные диаметры требуют отдельной проверки сечений.</li><li>Головы: сначала уши, затылок, внешние контуры; глаза, губы, веки, челюстные ориентиры и стык шеи защищать. Существующие причёски и варианты hat сохранять до отдельного просмотра.</li><li>После выбора формы: перенос весов и UV, проверка швов, поз плеч/локтей/коленей, сборка DFM. Только Mesh0; другие LOD и скелет должны оставаться побайтно прежними. Для массовых черновиков DFM ещё не собирались; Хетчер проверена отдельно.</li><li>После LI повторить обзор BR, KU и RH, затем персонажей без артов. Отсутствующий арт не заменять выдуманной реконструкцией.</li></ol>
<p>Ограничение превью: первый консервативный проход может давать небольшую разницу на общем плане. Крупный серый рендер показывает только геометрию. Ровность каждого канта и каждого ремня ещё требует индивидуального прохода.</p><nav>''']
for r in records:
 parts.append(f'<a href="#{r["name"]}">{r["name"]}</a>')
parts.append('</nav><h2>Тела: текущий вариант / пробная форма</h2>')
for r in records:
 name=r['name'];folder=OUT/name
 assert hashlib.sha256(Path(r['source']).read_bytes()).hexdigest()==r['sha256'],name+' game changed'
 if r['kind']!='BODIES':continue
 before=json.loads((folder/'before.json').read_text());after=json.loads((folder/'after.json').read_text())
 import numpy as np
 bp=np.array(before['points']);ap=np.array(after['points'])
 if name!='li_hatcher_body':assert (ap.min(0)>=bp.min(0)-1e-7).all() and (ap.max(0)<=bp.max(0)+1e-7).all()
 refs,note=notes[name];ntri=sum(len(g['faces']) for g in after['groups'])
 parts.append(f'<section id="{name}"><h2>{name}</h2><p>{note}</p><small>Mesh0: {r["triangles"]} → {ntri} треугольников. Слева до, справа пробный вариант.</small><figure><a href="{name}/comparison.png"><img loading="lazy" src="{name}/comparison.png"></a></figure><details><summary>Крупно, без текстур</summary><img loading="lazy" src="{name}/detail_clay.png"></details>')
 if name=='li_hatcher_body':parts.append(f'<h3>Пояс: прежний вариант / плоская лента с ровными кромками</h3><img src="{name}/belt.png"><details><summary>Пояс без текстур</summary><img src="{name}/belt_clay.png"></details>')
 if refs:parts.append('<div class="arts">'+''.join(f'<a href="arts/{a}"><img loading="lazy" src="arts/{a}" title="{a}"></a>' for a in refs)+'</div>')
 parts.append('</section>')
parts.append('<h2>Головы: исходный обзор, форма пока не изменена</h2><div class="heads">')
for r in records:
 if r['kind']=='HEADS':parts.append(f'<section id="{r["name"]}"><h3>{r["name"]}</h3><a href="{r["name"]}/reference.png"><img loading="lazy" src="{r["name"]}/reference.png"></a><small>Текущая модель, {r["triangles"]} треугольников Mesh0.</small></section>')
parts.append('</div><h2>Остальные арты LI</h2><p>Банкрофт: l11/l12; Джуни: juniheadconcept. Прямого li_-тела с этими именами в текущем списке нет; искать соответствия в costumes/bodyparts, а не переименовывать модель по арту. l21 — устройство с головой, не обычный костюм.</p></html>')
(OUT/'index.html').write_text(''.join(parts),encoding='utf8')
(OUT/'validation.json').write_text(json.dumps(dict(game_files_unchanged=True,models=len(records),bodies=13,heads=12,art_files=len(arts),verified_images=verified_images,preview_only=True),indent=2))
print('Gallery:',OUT/'index.html','art files:',len(arts))
