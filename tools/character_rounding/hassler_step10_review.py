"""Publish the fitted shoulder wrap and external collar as a separate revision."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_10'

def record(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def fig(p,label):return f'<figure><a href="{p}"><img src="{p}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'));build=json.loads((OUT/'report.json').read_text(encoding='utf8'));digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert digest==check['blend_sha256']==check['previews_bound_to_blend_sha256'] and check['layer_checks_passed']
    previous=TOP/'index_step09.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 10: эполет огибает наплечник, воротник снаружи</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.art img{max-height:510px;object-fit:contain}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair,.grid{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 10: собранное плечо и воротник поверх него</h1>
<p>Золотая оболочка целиком огибает наплечник и заканчивается замкнутым краем. Внутренний конец доходит до основания воротника. Серый воротник развёрнут наружу и лежит поверх золота.</p>
<nav class="links"><a href="step_10/hassler_native_upper.blend">Blender</a><a href="step_10/README.txt">Описание и редактирование</a><a href="step_10/validation.json">Проверки</a><a href="index_step09.html">Шаг 09</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p><div class="pair">'
    page+=fig('step_10/front.png','Новая посадка спереди')+fig('step_10/three_quarter.png','Воротник снаружи, золотая оболочка вокруг наплечника')+'</div>'
    page+='<h2>Крупные планы</h2><div class="pair">'+fig('step_10/shoulder_detail.png','Золото огибает весь наплечник; наружный край оформлен по объёму')+fig('step_10/right_shoulder_detail.png','Сторона с красной полочкой: воротник накрывает внутренний конец эполета')+'</div>'
    page+='<div class="pair">'+fig('step_10/shoulders_above.png','Посадка сверху')+fig('step_10/back.png','Замыкание деталей сзади')+'</div>'
    page+='<details><summary>Сравнение с предыдущей версией</summary><div class="pair">'+fig('step_09/shoulder_detail.png','Шаг 09: отдельный нависающий верх и открытый серый наплечник')+fig('step_10/shoulder_detail.png','Шаг 10: замкнутая оболочка и воротник поверх неё')+'</div></details>'
    page+='<details><summary>Пробные движения и профиль</summary><div class="grid">'
    for f,label in [('head_turn_right','Поворот головы'),('head_nod','Наклон головы'),('shoulder_pose','Подъём рук'),('turn_pose','Поворот корпуса'),('side','Профиль'),('collar_close','Воротник крупно')]:page+=fig(f'step_10/{f}.png',label)
    page+='</div></details><details><summary>Исходный арт</summary><div class="pair art">'+fig('source/art/hassler1.png','Перед: направление наружного отворота')+fig('source/art/hassler2.png','Спина: положение воротника над плечами')+'</div></details>'
    page+=f'''<p>Проверен сохранённый .blend в девяти пробных позах: наплечники полностью внутри оболочек; пересечений оболочки с наплечником и серым воротником нет. Голова не задевает воротник. Оба эполета замкнуты, свободных граничных рёбер нет. Голова, кисти, скелет, рукава, нижняя раскрытая полочка и три петли сохранены.</p>
<p class="muted">Посадочные поверхности снизу и внутренние торцы входят в мундир; эти контакты отдельно записаны в отчёте. Шнуры выходят из зоны крепления под эполетом. Это офлайн-прототип: {check['body_triangles_with_modifiers']:,} треугольников в теле с деталями и толщиной ткани, без головы и кистей. Пробные позы не заменяют проверку игровых анимаций. В игру не установлен.</p></html>'''
    readme=f'''ХАССЛЕР — ШАГ 10: ЗАМКНУТЫЙ ЭПОЛЕТ И ВОРОТНИК СНАРУЖИ

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Предыдущая версия: {TOP / 'step_09/hassler_native_upper.blend'}
Предыдущая галерея: {TOP / 'index_step09.html'}

ПОСАДКА
Эполет — замкнутая оболочка по объёму наплечника. Он огибает наружную,
переднюю и заднюю стороны, заканчивается нижним возвратом и внутренним торцом
под воротником. Прежней отдельной нависающей крыши нет. Поддерживающий серый
объём находится внутри, примерно на 2 мм глубже поверхности оболочки.
Внутренний конец продлён до основания воротника и ограничен со стороны шеи.
Внутренняя подкладка и нижнее замыкание тёмные; наружная поверхность золотая.
Текстура золота — Дитрих. Новая непрерывная окружная UV, отдельные замкнутые
верх и низ. Нижнее замыкание явно разбито на треугольники.

Серый воротник расправлен наружу. Перегиб у шеи выше, свободная кромка
спускается поверх золотого плеча. Передняя часть проходит снаружи золотой
поверхности. Линия вшивания воротника в мундир сохранена, шея остаётся открытой.
Указание пользователя о полном закрытии наплечника имеет приоритет над
частично открытой серой деталью на исходном арте.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study:
14 Epaulettes — closed gold wrap to collar root: два отдельных замкнутых
  компонента в одном объекте. Для выбора одного — L в режиме редактирования.
16 Shoulder padding — fully enclosed by gold: скрытая внутри серая опора;
  можно временно скрыть объект 14, чтобы увидеть её форму. Та же топология
  и веса, поэтому слои согласованно двигаются.
10 Sewn uniform — outward collar over gold: основной мундир и воротник.
  Его UV, грани и веса сохранены; изменены {len(build['collar']['changed_vertices'])} вершин воротника.
15 Red lining — below drawn blue boundary: красная полочка из шага 09.
13.1 / 13.2 / 13.3: прежние петли аксельбанта.
Голова, кисти, низ, пояс, рукава, внутренняя одежда и свисающая нижняя полочка
сохранены. ARCHIVE / REFERENCE отключены во viewport и render.
Для ручных правок сохранять отдельный .blend рядом; генератор пересобирает
hassler_native_upper.blend из шага 09.

ПРОВЕРКИ
SHA256: {digest}
Повторное открытие файла, проверка исходных деталей и 28 костей. UV без
вырожденных треугольников; до четырёх нормированных весов на вершину.
Две замкнутые оболочки, без граничных и неманифолдных рёбер, положительный
ориентированный объём. Наплечники целиком внутри оболочек.
Проверены девять пробных поз: покой, локти, плечи, поворот корпуса/головы,
два поворота головы, наклон вперёд, взгляд вверх, наклон вбок.
Во всех позах: оболочка/наплечник — 0; оболочка/серый воротник — 0;
голова/воротник — 0; несоседние самопересечения воротника и оболочки — 0.
Сохранён шов штатной шеи. Свободные шнуры не пересекают мундир и друг друга;
их контакт с оболочкой ограничен первыми семью сечениями в зоне крепления.

Посадочные поверхности замкнутого плеча входят внутрь старого мундира и
красной подкладки: эти соединения отдельно учтены как seating_contacts.
Отчёт не утверждает отсутствие всех контактов в многослойной одежде.
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольников, без головы и кистей.
DFM, игровые анимации, LOD и установка не выполнялись.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step10.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step10_check.py -- --render --strict
python tools/character_rounding/hassler_step10_review.py
'''
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if p!='step_10/README.txt' and not (TOP/p).is_file()];assert not missing,missing
    (OUT/'README.txt').write_text(readme,encoding='utf8');(TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 10 — эполет полностью огибает наплечник и доходит до основания воротника; воротник расправлен наружу поверх него.\nBlender: step_10/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_10/README.txt. Предыдущие шаги сохранены.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 10, замкнутый эполет и воротник снаружи.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_10/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(build['parent'])),'references':[record(Path(p)) for p in build['references']],'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/p) for p in ('hassler_native_step10.py','hassler_step10_check.py','hassler_step10_review.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
