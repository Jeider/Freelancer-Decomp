"""Publish the annotated shoulder correction and its editable Blender source."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_11'
def record(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def fig(p,label):return f'<figure><a href="{p}"><img src="{p}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'));build=json.loads((OUT/'report.json').read_text(encoding='utf8'));digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert digest==check['blend_sha256']==check['previews_bound_to_blend_sha256'] and check['layer_checks_passed']
    previous=TOP/'index_step10.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 11: тонкие эполеты и золотая изнанка</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair,.grid{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 11: тонкий эполет с завёрнутым краем</h1>
<p>Золото занимает верхнюю часть плеча; снизу виден серый наплечник. Кромка плавно заворачивается на изнанку и замыкается. Между воротником и эполетом добавлена золотая ткань. Снаружи воротник серый, внутри — орнамент Дитриха.</p>
<nav class="links"><a href="step_11/hassler_native_upper.blend">Blender</a><a href="step_11/README.txt">Редактирование и проверки</a><a href="step_11/validation.json">Отчёт</a><a href="index_step10.html">Шаг 10</a><a href="index_step09.html">Шаг 09</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('source/shoulder_fit_study/user_front_step11.png','Разметка пользователя: синий контур — эполет, серое — наплечник')+fig('step_11/front.png','Новая геометрия: золотая верхняя часть и открытый серый низ')+'</div>'
    page+='<h2>Посадка и подвёрнутый край</h2><div class="pair">'+fig('step_11/shoulder_detail.png','Сторона с аксельбантом: тонкая замкнутая кромка и золотая ткань под воротником')+fig('step_11/right_shoulder_detail.png','Сторона с раскрытой красной полочкой')+'</div>'
    page+='<div class="pair">'+fig('step_11/three_quarter.png','Общий вид в три четверти')+fig('step_11/shoulders_above.png','Золотая изнанка и соединение деталей сверху')+'</div>'
    page+='<details><summary>Предыдущие формы</summary><div class="grid">'+fig('step_09/front.png','09: нависающая пластина')+fig('step_10/front.png','10: слишком объёмная золотая оболочка')+fig('step_11/front.png','11: тонкая верхняя часть, край возвращается внутрь')+'</div></details>'
    page+='<details><summary>Штатные эполеты Дитриха и Райхмана</summary><p>Отдельно изучены реальные меши и UV. Это вырезки плечевых областей исходных тел, поэтому у вырезок есть открытые границы. Новая форма построена вручную по разметке; автоматическое распознавание контура не использовалось.</p><div class="grid">'
    for f,label in [('dietrich_front','Дитрих, спереди'),('dietrich_profile','Дитрих, сбоку'),('reichman_front','Райхман, спереди')]:page+=fig(f'source/shoulder_fit_study/{f}.png',label)
    page+='</div></details><details><summary>Профиль, спина и пробные движения</summary><div class="grid">'
    for f,label in [('side','Профиль'),('back','Спина'),('collar_close','Воротник'),('head_nod','Наклон головы'),('head_turn_right','Поворот головы'),('shoulder_pose','Поднятые руки'),('turn_pose','Поворот корпуса')]:page+=fig(f'step_11/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>Проверен повторно открытый .blend: обе золотые детали и серые наплечники замкнуты; между ними и воротником нет пересечений в девяти пробных позах. Голова, руки, скелет, основная геометрия мундира, красная полочка и аксельбанты сохранены.</p>
<p class="muted">Это офлайн-прототип. Тело с деталями и толщиной ткани: {check['body_triangles_with_modifiers']:,} треугольников, без головы и кистей. Соединительные швы и посадка деталей в мундир отдельно описаны в отчёте. Пробные позы не заменяют игровые анимации. В игру не установлен.</p></html>'''
    readme=f'''ХАССЛЕР — ШАГ 11: ТОНКИЙ ЭПОЛЕТ, СЕРЫЙ НАПЛЕЧНИК И ЗОЛОТАЯ ИЗНАНКА

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {TOP / 'step_10/hassler_native_upper.blend'}
Разметка: {TOP / 'source/shoulder_fit_study/user_front_step11.png'}

ФОРМА
Тонкая золотая верхняя часть вместо сплошной объёмной оболочки шага 10.
Профиль соединяет идею шага 09 с подвернутой кромкой штатных эполет Дитриха
и Райхмана. Контур вручную задан по последнему рисунку пользователя.
Толщина замкнутого золотого края — 5 мм. Снизу видна серая округлая опора.
Внутренняя часть доходит под воротник; золотая тканевая вставка закрывает
просвет между ними. Воротник снаружи серый, внутри имеет отдельную UV-карту
для золотого орнамента Дитриха. Старые геометрия и основная UV воротника
сохранены; выбор стороны материала учитывает направление перегиба ткани.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study:
14 Epaulettes — thin gold with inward rolled hem: два замкнутых компонента,
  наружная поверхность, скруглённый возврат и полная изнанка. Выбор одного — L.
16 Grey shoulder pads — exposed below gold hem: отдельные серые опоры.
17 Gold cloth — closes collar to shoulder: соединительная ткань под воротником.
10 Sewn uniform — grey collar with brocade lining: сам мундир и воротник.
  Основная UV сохранена. Новая карта: Collar inside brocade UV.
  Серые стороны: слоты 4/33. Золотая изнанка: 15/22.
15 Red lining — below drawn blue boundary: прежняя красная полочка.
13.1 / 13.2 / 13.3: прежние петли аксельбанта.
Новые части сохраняют нормированные веса штатного скелета, до четырёх на вершину.
ARCHIVE / REFERENCE выключены во viewport и render. Предыдущие шаги сохранены.
Ручную правку сохранять отдельным .blend рядом: генератор заменяет только
автоматический step_11/hassler_native_upper.blend.

ПРОВЕРКИ
SHA256: {digest}
Файл сохранён и открыт заново. Проверены исходные голова, кисти, низ, скелет,
рукава, основная геометрия мундира и её UV, красная полочка и шнуры.
В новых замкнутых плечевых деталях нет граничных или неманифолдных рёбер.
UV без вырожденных треугольников. До четырёх нормированных весов на вершину.
Девять синтетических поз: покой, локти, плечи, поворот корпуса/головы,
два поворота головы, наклон вперёд, вверх и вбок. Голова не задевает воротник,
эполет не пересекает серую опору или воротник. В закрытых плечевых деталях
не обнаружены несоседние самопересечения.
Соединение нового золота с исходным мундиром остаётся посадочным швом.
Верхняя кромка соединительной ткани пришита под внутренним перегибом воротника;
контакты шва отличаются от столкновений свободной части ткани в отчёте.
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольников, без головы и кистей.
DFM, игровые анимации, LOD и установка этим шагом не выполнялись.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_shoulder_reference.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step11.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step11_check.py -- --render --strict
python tools/character_rounding/hassler_step11_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 11 — тонкие эполеты с подвёрнутым краем, открытые серые наплечники и золотая изнанка воротника.\nBlender: step_11/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_11/README.txt. Предыдущие шаги сохранены.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 11, тонкие эполеты и золотая изнанка воротника.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_11/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    refs=[TOP/'source/shoulder_fit_study'/n for n in ('user_front_step11.png','native_reference_geometry.json')]+[TOP/'source/art'/n for n in ('hassler1.png','hassler2.png')]
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(build['parent'])),'build':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'contacts':record(OUT/'contacts.json'),'references':[record(p) for p in refs],'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/p) for p in ('hassler_native_step11.py','hassler_step11_check.py','hassler_step11_review.py','hassler_shoulder_reference.py','hassler_step11_contacts.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
