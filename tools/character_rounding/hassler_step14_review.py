"""Publish the under-tunic belt study and source comparisons."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_14'
def record(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def fig(p,label):return f'<figure><a href="{p}"><img src="{p}" loading="lazy" alt="{label}"></a><figcaption>{label}</figcaption></figure>'

def main():
    b=json.loads((OUT/'report.json').read_text(encoding='utf8'));c=json.loads((OUT/'validation.json').read_text(encoding='utf8'));digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert c['checks_passed'] and digest==c['blend_sha256']==c['previews_bound_to_blend_sha256']
    prior=TOP/'index_step13.html'
    if not prior.exists():
        old=(TOP/'index.html').read_text(encoding='utf8');assert 'step_13/hassler_native_upper.blend' in old;prior.write_text(old,encoding='utf8')
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — шаг 14: пояс под мундиром</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.refs{display:grid;grid-template-columns:1fr 1fr 2fr;gap:20px}.refs img{height:480px;object-fit:contain}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair,.refs{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 14: пояс под мундиром</h1>
<p>Вместо пояса с подсумками — тёмный ремень по конструкции li_scrote, подогнанный к талии Хасслера. Спереди прямоугольная золотая рамка с рейнландской застёжкой; сзади три небольших держателя, как на арте. Верх ремня подходит под нижний край мундира.</p>
<p>Принятые воротник, плечи, рукава, полочки, аксельбант и материалы шага 13 сохранены. Верх родных брюк продолжен внутрь нового ремня, закрывая отверстие от прежнего пояса.</p>
<nav class="links"><a href="step_14/hassler_native_upper.blend">Blender</a><a href="step_14/README.txt">Исходники и редактирование</a><a href="step_14/validation.json">Проверки</a><a href="index_step13.html">Шаг 13</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('step_14/front.png','Новый пояс под мундиром')+fig('step_14/waist_front.png','Золотая рамка и родная рейнландская застёжка')+'</div>'
    page+='<h2>Арт и конструкция донора</h2><div class="refs">'+fig('source/art/hassler1.png','Хасслер: тёмный ремень и золотая пряжка')+fig('source/art/hassler2.png','Сзади: небольшие держатели')+fig('source/scrote/study/front.png','Настоящий li_scrote: пояс под кителем')+'</div>'
    page+='<h2>До и после</h2><div class="pair">'+fig('source/belt_study/before_front.png','Прежний пояс с подсумками')+fig('step_14/waist_front.png','Новый ремень на той же талии')+'</div>'
    page+='<div class="pair">'+fig('step_14/waist_side.png','Посадка сбоку и стык с брюками')+fig('step_14/waist_back.png','Три задних держателя')+'</div>'
    page+='<details><summary>Общий вид и пробный поворот</summary><div class="pair">'+fig('step_14/three_quarter.png','Три четверти')+fig('step_14/turn_pose.png','Поворот корпуса')+fig('step_14/back.png','Общий вид сзади')+'</div></details>'
    page+=f'<p class="muted">Проверен сохранённый и заново открытый Blender-файл. Принятый верх сохранён; исходные вершины и UV брюк не сдвигались. Четыре пробные позы: соединение брюк не расходится, ремень не самопересекается. {c["body_triangles_with_modifiers"]:,} треугольников тела с модификаторами. Офлайн-прототип, в игру не установлен.</p></html>'
    readme=f'''ХАССЛЕР — ШАГ 14: ПОЯС ПОД МУНДИРОМ

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {b['parent']}
SHA256 родителя: {b['parent_sha256']}
SHA256 результата: {digest}

АРТ И ДОНОР
Просмотрены оба исходных рисунка hassler1.png / hassler2.png.
Основные признаки: тёмный горизонтальный ремень под нижним краем мундира,
золотая прямоугольная пряжка, небольшие серые держатели сзади.
Прежняя просьба убрать кобуру сохранена; боковой рисунок кобуры не моделировался.
У li_scrote_body изучены настоящие 24 треугольника ремня (233–256 группы 0),
его 12 пар верхних/нижних точек, UV и соответствующий участок атласа.
Источник: {b['donor']['json']}
SHA256 DFM: {b['donor']['dfm_sha256']}
Контур донора подогнан к рейнландской талии; построена замкнутая лента толщиной
6 мм с небольшими закруглёнными возвратами. Это новая сетка на измеренном
контуре, а не точная копия всего тела Scrote.
Его орёл Либерти не перенесён: у пряжки новая золотая рамка, центральная
застёжка и держатели используют настоящую текстуру фурнитуры rh_male_elite.
Это адаптация под рейнландский костюм; новый национальный герб не придумывался.
Исходные атласы не изменены. Нативная нейтральная часть золотой пряжки Scrote
используется отдельно от его эмблемы; цвета ремня/серой фурнитуры настроены узлами.
Перед игровым экспортом эти настройки цвета понадобится перенести или запечь.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study.
19 Hassler waist belt — fitted Scrote construction: сам замкнутый ремень.
20 Rheinland clasp — gold frame and native latch: золотая рамка и застёжка.
21 Belt keepers — Rheinland fittings: два передних и три задних держателя.
22 Trouser waist — sewn continuation under belt: продолжение 12 родных краёв
  брюк внутрь ремня; нижние вершины и веса совпадают с родным краем.
00 Native lower body — original pouch belt removed: прежний низ без 72 граней
  старого пояса. Остальные координаты, веса, грани и UV сохранены.
Верх, голова, руки, воротник, красная полочка, аксельбант, шея и материалы
совпадают с принятым шагом 13. Скелет сохранён.
Старый пояс сохранён вместе с прежним низом в ARCHIVE — step13 original pouch belt;
коллекция выключена в viewport и render. Сам файл step13 не перезаписан.
Ручные правки сохранять отдельным blend рядом с автоматическим файлом.

ПРОВЕРКИ
Ремень и фурнитура замкнуты, имеют положительный объём; новые UV без вырождений.
Веса нормированы, не более четырёх на вершину. Проверены сохранённый файл
и четыре синтетические позы: кадры 1, 30, 60, 120. Ремень не самопересекается,
стык продолжения брюк с исходным краем не расходится.
Контакты ремня с мундиром разрешены только у посадочного нижнего края;
это не утверждение об отсутствии всех контактов в сборке. Фурнитура крепится
к ремню с небольшим посадочным нахлёстом.
Нормали оставшихся брюк перенесены: максимальное расхождение кодирования
Blender {c['retained_trouser_normal_encoding_max_delta']:.8f}; верх совпадает точно.
Тело с модификаторами: {c['body_triangles_with_modifiers']} треугольников, без головы/кистей.
Рендеры привязаны к хешу этого blend. Игровые DFM/MAT, LOD и установка
не выполнялись; игровые анимации не проверялись.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_belt_study.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step14.py -- --no-render
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step14_check.py -- --render
python tools/character_rounding/hassler_step14_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 14 — пояс под мундиром по li_scrote, золотая рамка и рейнландская фурнитура.\nBlender: step_14/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_14/README.txt. Принятый верх шага 13 сохранён.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 14, пояс под мундиром по Scrote с рейнландской фурнитурой.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_14/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(b['parent'])),'report':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'readme':record(OUT/'README.txt'),'source_geometry':record(TOP/'source/belt_study/geometry.json'),'references':[record(Path(a['path'])) for a in b['art']],'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/n) for n in ('hassler_native_step14.py','hassler_step14_check.py','hassler_step14_review.py','hassler_belt_study.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'triangles':c['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
