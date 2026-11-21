"""Publish the lower belt and Bretonia trousers/boots offline study."""
import json,re
from pathlib import Path
from hassler_step14_review import ROOT,TOP,record,fig
OUT=TOP/'step_15'


def main():
    b=json.loads((OUT/'report.json').read_text(encoding='utf8'));c=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert c['checks_passed'] and digest==c['blend_sha256']==c['previews_bound_to_blend_sha256']
    prior=TOP/'index_step14.html'
    if not prior.exists():
        old=(TOP/'index.html').read_text(encoding='utf8');assert 'step_14/hassler_native_upper.blend' in old
        prior.write_text(old,encoding='utf8')
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — шаг 15: пояс и брюки</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.refs{display:grid;grid-template-columns:1fr 1fr;gap:20px}.refs img{height:480px;object-fit:contain}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair,.refs{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 15: пояс ниже мундира</h1>
<p>Пояс стал ниже, уже и ближе к талии. Его высота уменьшена с 8,6 до 5,4 см; между верхом ремня и подолом оставлено около 3 см ткани. Мундир выступает над поясом. Пряжка тоже уменьшена.</p>
<p>Брюки и высокие сапоги взяты из br_male_elite: брюки зелёные, сапоги серые, подошвы тёмные. Убрана прежняя паховая накладка. Принятый верх, воротник, плечи, кисти и голова сохранены.</p>
<nav class="links"><a href="step_15/hassler_native_upper.blend">Blender со скелетом</a><a href="step_15/README.txt">Исходники и редактирование</a><a href="step_15/validation.json">Проверки</a><a href="index_step14.html">Предыдущий шаг</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('step_15/full_front.png','Новый пояс, брюки и сапоги')+fig('step_15/waist_front.png','Ткань между ремнём и нависающим подолом')+'</div>'
    page+='<h2>Пояс: до и после</h2><div class="pair">'+fig('step_14/waist_front.png','Шаг 14: прежний высокий и широкий ремень')+fig('step_15/waist_front.png','Шаг 15: компактная посадка по br_male_elite')+'</div>'
    page+='<h2>Посадка со всех сторон</h2><div class="pair">'+fig('step_15/waist_side.png','Мундир выступает над ремнём сбоку')+fig('step_15/waist_back.png','Небольшой промежуток сзади')+fig('step_15/full_three_quarter.png','Общий силуэт в три четверти')+fig('step_15/full_back.png','Брюки и сапоги сзади')+'</div>'
    page+='<details><summary>Сапоги, пробные позы и исходный арт</summary><div class="pair">'+fig('step_15/boots.png','Родные формы высоких сапог br_male_elite')+fig('step_15/step_pose.png','Синтетическая проба: шаг и сгиб колена')+fig('step_15/turn_pose.png','Синтетическая проба: поворот корпуса')+'</div><div class="refs">'+fig('source/art/hassler1.png','Исходный арт: пояс, зелёные брюки и серые сапоги')+fig('source/art/hassler2.png','Исходный арт: вид сзади')+'</div></details>'
    page+=f'<p class="muted">Рендеры сделаны из заново открытого сохранённого Blender-файла. Проверены неизменность верха и скелета, сохранение исходных UV/весов низа, отсутствие отверстий в сапогах, стык талии и ремень в пяти пробных позах. Тело с модификаторами: {c["body_triangles_with_modifiers"]:,} треугольников. Это офлайн-прототип; игровые анимации не проверены. Цвета пока настроены материалами Blender, перед игровым экспортом потребуется перенос или запекание.</p></html>'
    readme=f'''ХАССЛЕР — ШАГ 15: ПОЯС НИЖЕ МУНДИРА, БРЮКИ И САПОГИ

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {b['parent']}
SHA256 родителя: {b['parent_sha256']}
SHA256 результата: {digest}

ИЗМЕНЕНИЯ
Пояс опущен и уменьшен: высота 54,18 мм вместо 86 мм (на 37% ниже).
Верх ремня Z=.18509; нижний край мундира примерно Z=.215.
Между ними около 29,91 мм, заполненных зелёной тканью. Подол шире ремня.
Контур ремня получен сечением реального пояса br_male_elite при Z=.185.
Родная застёжка донора не переносится; скрытый ею разрыв ленты замкнут.
Прежние материалы тёмного ремня и рейнландской фурнитуры сохранены.
Пряжка уменьшена до 47,52 × 48,96 мм; держатели уменьшены по высоте.

Низ заменён на br_male_elite_body: родные брюки и высокие сапоги.
Положение, UV и веса сохранённых исходных граней перенесены; обрезан только
скрытый верх талии на Z=.145. Родной край брюк продолжен до Z=.237 внутрь
мундира. Нижние точки продолжения и их веса совпадают с реальным краем брюк.
Брюки зелёные, кожа сапог серая, подошвы тёмные. Исходный рисунок материалов
сохранён; цвета настроены узлами Blender, без правки нативных атласов.
Все 28 исходных матриц и имён костей br_male_elite совпадают с rh_male_elite.
Принятый верх, голова, кисти, воротник, аксельбанты и их материалы не менялись.
Кобура не добавлена, согласно прежней просьбе пользователя.

ДОНОР
{b['donor']['source']}
DFM SHA256: {b['donor']['dfm_sha256']}
Изолированный снимок: {b['donor']['json']}
JSON SHA256: {b['donor']['json_sha256']}
Арт: source/art/hassler1.png и hassler2.png.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study.
00 Hassler lower — Bretonia trousers and high boots: исходная форма низа.
19 Hassler belt — lower narrow Bretonia fit: замкнутый ремень.
20 Rheinland clasp — compact waist fit: пряжка.
21 Belt keepers — compact waist fit: держатели.
23 Waist cloth — recessed below overhanging tunic: ткань под подолом.
Старый пояс и низ сохранены в скрытой в viewport И render коллекции
ARCHIVE — step14 wide belt and former trousers. Предыдущие blend не изменены.
Ручные правки сохранять отдельным файлом рядом с автоматическим исходником.

ПРОВЕРКИ И ГРАНИЦЫ
Сохранённый файл заново открыт, проверены геометрия/UV/веса/нормали принятого
верха и матрицы скелета. Все совпадают с родителем. Все грани родных ног ниже
паха сохранены; отверстия в нативной сетке низа остались только на талии,
где добавлено продолжение ткани. Три вырожденных UV-треугольника унаследованы
от br_male_elite; новых вырождений нет. Новые ремень и фурнитура замкнуты.
Кадры 1, 30, 60, 90, 120: стык брюк не расходится, ремень не пересекает мундир
и не самопересекается. Это синтетические позы, не игровые анимации.
Тело с модификаторами: {c['body_triangles_with_modifiers']} треугольников.
Исходные DFM/MAT и игра не изменены. Экспорт/LOD/установка не выполнялись.
Цветовые узлы Blender перед экспортом потребуется перенести или запечь.

ВОСПРОИЗВЕДЕНИЕ
python tools/character_rounding/hassler_bretonia_prepare.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step15.py -- --no-render
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step15_check.py -- --render
python tools/character_rounding/hassler_step15_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 15 — уменьшенный пояс с промежутком под мундиром; зелёные брюки и серые сапоги по br_male_elite.\nBlender: step_15/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_15/README.txt. Принятый верх сохранён.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 15, пояс ниже мундира; брюки и сапоги по br_male_elite.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_15/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(b['parent'])),'report':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'readme':record(OUT/'README.txt'),'source_geometry':record(Path(b['donor']['json'])),'source_audit':record(TOP/'source/bretonia/source_audit.json'),'references':[record(TOP/'source/art'/n) for n in ('hassler1.png','hassler2.png')],'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/n) for n in ('hassler_native_step15.py','hassler_step15_check.py','hassler_step15_review.py','hassler_bretonia_prepare.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'triangles':c['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
