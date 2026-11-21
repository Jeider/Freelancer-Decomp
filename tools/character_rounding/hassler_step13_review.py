"""Publish native cloth material review and record the user's accepted step12 shape."""
import json,re,hashlib,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_13'

def record(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def fig(p,label):return f'<figure><a href="{p}"><img src="{p}" loading="lazy" alt="{html.escape(label)}"></a><figcaption>{label}</figcaption></figure>'

def atlas_diagram(build):
    # SVG is a UV inspection diagram over the untouched native image.
    # No new bitmap texture or image retouching is performed.
    tex=Path(build['donor']['textures'][1]['path']).name
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1100"><rect width="1024" height="1100" fill="#191c20"/><image href="../textures/{tex}" width="1024" height="1024"/>'
    for key,color,label in [('collar','#53e1ff','Серая ткань воротника'),('shirt','#ffce64','Тёмная вставка со складками')]:
        u0,v0,u1,v1=build[key]['source_uv_bounds'];x=u0*1024;y=(1-v1)*1024;w=(u1-u0)*1024;h=(v1-v0)*1024
        svg+=f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="none" stroke="{color}" stroke-width="4"/>'
    svg+='<text x="20" y="1052" fill="#53e1ff" font-family="sans-serif" font-size="24">Голубой: ткань воротника Хасслера, без карманов и ремней</text><text x="20" y="1087" fill="#ffce64" font-family="sans-serif" font-size="24">Жёлтый: область чёрной рубашки; границы охвата UV</text></svg>'
    (OUT/'donor_uv.svg').write_text(svg,encoding='utf8')

def main():
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'));check=json.loads((OUT/'validation.json').read_text(encoding='utf8'));digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert check['checks_passed'] and digest==check['blend_sha256']==check['previews_bound_to_blend_sha256']
    assert record(Path(build['parent']))['sha256']==build['parent_sha256']
    prior=TOP/'index_step12.html'
    if not prior.exists():
        old=(TOP/'index.html').read_text(encoding='utf8');assert 'step_12/hassler_native_upper.blend' in old;prior.write_text(old,encoding='utf8')
    acceptance={'accepted_step':12,'accepted_blend':str(Path(build['parent'])),'sha256':build['parent_sha256'],'date':'2026-11-19','user_quote':build['accepted_shape']['user_quote'],'scope':'Upper shape, shoulder pads, epaulettes and collar. Later texture studies are separate reviews.'}
    (TOP/'accepted_shape.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    atlas_diagram(build)
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 13: ткань воротника и тёмная вставка</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img,object{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 13: фактура ткани</h1>
<p>Воротник получил серую ткань Вильгельма. Для широких отворотов использован крупный участок ткани его мундира, чтобы сохранить мелкую фактуру. Обе стороны серые, красный кант сохранён. На тёмной вставке под шеей появились мягкие складки и фактура его чёрной рубашки.</p>
<p>Форма шага 12 принята пользователем и сохранена без изменений. Этот шаг меняет только материалы и добавляет две отдельные UV-развёртки.</p>
<nav class="links"><a href="step_13/hassler_native_upper.blend">Blender</a><a href="step_13/README.txt">Материалы и редактирование</a><a href="step_13/validation.json">Проверки</a><a href="index_step12.html">Принятая форма — шаг 12</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('step_13/front.png','Новые материалы на принятой форме')+fig('step_13/collar_close.png','Серая ткань, красный кант и тёмная вставка со складками')+'</div>'
    page+='<h2>Сравнение</h2><div class="pair">'+fig('step_12/front.png','Шаг 12 — до текстурирования')+fig('step_13/front.png','Шаг 13 — ткань Вильгельма')+'</div>'
    page+='<h2>Воротник с обеих сторон</h2><div class="pair">'+fig('step_13/right_shoulder_detail.png','Правое плечо Хасслера')+fig('step_13/shoulder_detail.png','Левое плечо Хасслера')+'</div>'
    page+='<div class="pair">'+fig('step_13/shoulders_above.png','Серая изнанка и открытая шея')+fig('step_13/back.png','Фактура на задней стороне воротника')+'</div>'
    page+='<details><summary>Источник ткани и UV</summary><p>Оба участка взяты из сохранённого атласа rh_wilham_body. Исходная текстура не изменена. Голубая рамка показывает поле серой ткани, жёлтая — область чёрной вставки. У воротника одна непрерывная развёртка вдоль складки; шов развёртки рубашки расположен сзади.</p>'
    page+='<object type="image/svg+xml" data="step_13/donor_uv.svg" style="aspect-ratio:1024/1100">'+ '<a href="step_13/donor_uv.svg">Открыть карту участков атласа</a></object></details>'
    page+='<details><summary>Общий вид в три четверти</summary>'+fig('step_13/three_quarter.png','Общий вид')+'</details>'
    page+=f'<p class="muted">Сохранённый файл открыт заново: геометрия, нормали, веса, скелет и прежние UV совпадают с шагом 12. Проверено совпадение вершин и в трёх пробных позах. {check["body_triangles_with_modifiers"]:,} треугольников тела с модификаторами — количество прежнее. Это офлайн-пример материалов; в игру не установлен.</p></html>'
    readme=f'''ХАССЛЕР — ШАГ 13: СЕРАЯ ТКАНЬ И ТЁМНАЯ ВСТАВКА

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Принятая форма: {build['parent']}
Фиксация принятой формы: {TOP / 'accepted_shape.json'}

Пользователь принял геометрию шага 12. Этот шаг меняет только материалы
воротника и внутренней рубашки, добавляет UV. Старые UV, геометрия, нормали,
веса, скелет, открытая шея, эполеты, наплечники, кант и полочки сохранены.

ДОНОР
{build['donor']['source']}
SHA256 DFM: {build['donor']['source_sha256']}
Используется закреплённая копия модели и извлечённые раньше нативные атласы.
Для серого воротника выбран участок серой ткани верхней спины Вильгельма
на атласе fb450611a1d11f2c.png: U 0.06–0.62, V 0.57–0.7122.
Его собственная узкая полоска воротника проверена и отвергнута при примерке:
при переносе на широкий отворот Хасслера слишком укрупнялась фактура.
Для тёмной вставки взято поле чёрной рубашки вверху справа на том же атласе.
Складки уже нарисованы в исходнике, новая геометрия для них не добавлена.
Схема участков: {OUT / 'donor_uv.svg'}
Изображение донора не отретушировано и не перезаписано; оно упаковано в blend.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study.
10 Sewn uniform — Wilham cloth collar: единый мундир, форма шага 12.
  Материал Hassler 13 — Wilham grey collar cloth, слоты 4/15/22/33.
  Обе стороны воротника серые. Отдельная UV: Collar grey cloth — Wilham UV.
  Развёртка идёт непрерывно вдоль длины перегиба; поперёк — по длине ткани.
12 Inner shirt — Wilham dark woven cloth: прежняя открытая горловина.
  Материал Hassler 13 — Wilham charcoal shirt folds.
  Отдельная UV: Inner shirt — Wilham UV, шов сзади.
Цвет серой ткани настраивается в Color Ramp материала. У чёрной вставки
яркость фактуры регулируется Power 0.72 и её Color Ramp.
Это узлы цвета Blender; перед игровым экспортом понадобится перенос или
запекание этих цветовых настроек в отдельные текстуры Хасслера.
Процедурных displacement/bump и новых деталей геометрии нет.
Остальные материалы и старые UV не менялись. Красный кант — прежний меш 18.
Исходные два объекта сохранены в ARCHIVE — accepted step12 before cloth texturing;
архив выключен в viewport и render. Сам step12 blend также не перезаписан.
Ручную правку сохранять отдельным blend рядом: генератор обновляет автоматический файл.

ПРОВЕРКИ
SHA256 blend: {digest}
Сохранённый файл открыт заново. Совпадают координаты, грани, нормали, веса,
трансформации, скелет и все прежние UV всех рабочих мешей с шагом 12.
Проверены вершины после модификаторов в кадрах 1, 60 и 120: разница 0.
Новые используемые UV-треугольники имеют ненулевую площадь; координаты в атласе.
Материалы используют именно свои новые UV; изображения упакованы.
Донорские DFM и атласы сохранены. Рендеры привязаны к хешу этого blend.
Число треугольников тела с модификаторами: {check['body_triangles_with_modifiers']}.
Игровые DFM/MAT, LOD, анимации и установка в этом шаге не выполнялись.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step13.py -- --no-render
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step13_check.py -- --render
python tools/character_rounding/hassler_step13_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src|data)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 13 — серая ткань воротника и чёрная рубашка Вильгельма на принятой форме шага 12.\nBlender: step_13/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_13/README.txt. Принятая геометрия: accepted_shape.json; step_12 сохранён.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 13, ткань воротника и тёмной вставки; форма шага 12 принята.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_13/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'accepted_parent':record(Path(build['parent'])),'acceptance':record(TOP/'accepted_shape.json'),'report':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'readme':record(OUT/'README.txt'),'donor_uv_diagram':record(OUT/'donor_uv.svg'),'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/p) for p in ('hassler_native_step13.py','hassler_step13_check.py','hassler_step13_review.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest},ensure_ascii=False))

if __name__=='__main__':main()
