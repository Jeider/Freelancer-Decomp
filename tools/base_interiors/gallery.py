"""Build a local comparison gallery and verify that source content is untouched."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/base_interiors';OUT=TOP/'rh_biz_01_base/bar/prototype_v1'
source=json.loads((OUT/'source.json').read_text());assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
stats=json.loads((OUT/'prototype_stats.json').read_text());assert stats['modified_batches'] and stats['prototype_triangles']>stats['original_triangles']
style='<meta charset="utf-8"><style>body{background:#161d24;color:#e7edf3;font:17px system-ui;max-width:1500px;margin:32px auto;padding:20px}a{color:#7fcef5}img{width:100%;display:block}section{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:30px}figure{margin:0}figcaption{padding:10px;background:#263340}p{max-width:1100px;line-height:1.5}</style>'
html=style+'<h1>Бисмарк — прототип рельефа бара</h1><p>Офлайн-рендеры Blender из текущего rh_bizmark_bar.cmp. Это не скриншоты игры. Текущие текстуры сохранены. Игровые файлы не изменены.</p>'
html+='<p>Настоящая геометрия: кольца и рамки технических панелей, полосы стойки, рёбра колонн, круглые углубления. Обработано шесть групп материалов; это проба метода, не завершённая переработка всего бара.</p>'
html+=f'<p>Треугольники: {stats["original_triangles"]:,} → {stats["prototype_triangles"]:,}. Сетка прототипа требует оптимизации и проверки швов перед экспортом в CMP. Производительность в игре пока не измерена.</p>'
for title,a,b,la,lb in [
 ('Общий план: только изменение геометрии','before_overview','geometry_overview','Исходный меш','Новый меш, тот же свет'),
 ('Стойка: только изменение геометрии','before_counter','geometry_counter','Исходный меш','Новый меш, тот же свет'),
 ('Техническая панель — форма без текстур','detail_clay_before','detail_clay_after','Исходная плоскость','Реальные рамки и кольца'),
 ('Техническая панель — текущая текстура','detail_texture_before','detail_texture_after','До','После'),
 ('Отдельная проба нового освещения','geometry_overview','lighting_overview','Прежняя схема Blender','Мягкие локальные источники и другой материал'),
 ('Новый свет у стойки','geometry_counter','lighting_counter','Прежняя схема Blender','Новый свет')]:
 html+='<h2>'+title+'</h2><section>'
 for name,label in ((a,la),(b,lb)):
  assert (OUT/(name+'.png')).exists(),name
  html+=f'<figure><a href="{name}.png"><img src="{name}.png"></a><figcaption>{label}</figcaption></figure>'
 html+='</section>'
html+='<h2>Ограничения и перенос в движок</h2><p>Свет исходного THN приближён в Cycles; native detail maps Dm/Bt и мелкий реквизит отдельной сцены не воспроизведены. Отражения и мягкие тени нового варианта показывают направление работы, а не готовый эффект RP9. Часть старого освещения запечена в цветных текстурах и остаётся видимой.</p><p>Следующий этап: согласовать глубину деталей, заменить регулярную сетку экономной топологией, проверить стыки UV и исходные подвижные узлы. Затем экспортировать CMP и отдельно реализовать свет в RP9. Для полного динамического освещения потребуется очистка albedo от запечённых бликов и теней; добавление источников само по себе этого не решит.</p>'
html+='<p><a href="bismarck_bar_prototype.blend">Редактируемая Blender-сцена</a> · <a href="prototype_stats.json">Статистика</a> · <a href="source.json">Источник и SHA-256</a> · <a href="file:///D:/work/ART_BASE/RH/r04.JPG">Концепт Rheinland</a></p>'
(OUT/'index.html').write_text(html,encoding='utf-8')
(TOP/'index.html').write_text(style+'<h1>Базы и интерьеры</h1><p>Общий каталог исследований и прототипов. Существующие эксперименты сохранены на прежних местах.</p><ul><li><a href="rh_biz_01_base/bar/prototype_v1/index.html">rh_biz_01_base — бар, прототип 1</a></li><li><a href="../capital_interiors/">Ранее: интерьеры крупных кораблей</a></li><li><a href="../hair_lighting/">Ранее: диагностика освещения персонажей в барах</a></li></ul>',encoding='utf-8')
print('Gallery ready; live CMP SHA-256 unchanged; geometry counts checked.')
