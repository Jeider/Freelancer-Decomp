"""Publish upper-finish review with the native art and saved-file validation."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_08'

def fig(path,label):return f'<figure><a href="{path}"><img src="{path}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'
def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'));build=json.loads((OUT/'report.json').read_text(encoding='utf8'))
    digest=hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()
    assert digest==check['blend_sha256']==check['previews_bound_to_blend_sha256'] and check['clearance_checks_passed']
    previous=TOP/'index_step07.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 08: плечи, аксельбант и открытая шея</title>
<style>body{background:#161c24;color:#e7eef5;font:17px system-ui;margin:32px auto;padding:0 24px;max-width:1540px}h1{font-size:30px}a{color:#91d3ff}p{line-height:1.6;max-width:1200px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.reference{display:grid;grid-template-columns:202px 202px 1fr;gap:18px;align-items:start}figure{margin:0;background:#28323d}img{width:100%;display:block}figcaption{padding:12px}details{margin:28px 0}summary{cursor:pointer;margin-bottom:16px}h2{margin-top:32px;font-size:23px}@media(max-width:850px){.pair,.grid,.reference{grid-template-columns:1fr}.reference img{max-height:600px;object-fit:contain}}</style>
<h1>Хасслер — шаг 08: верх мундира</h1>
<p><a href="step_08/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_08/README.txt">Устройство и редактирование</a> · <a href="step_08/validation.json">Проверки</a> · <a href="index_step07.html">Предыдущий шаг 07</a></p>
<p>Красная ткань подогнана под плечо и меньше заходит за эполет. Золотые эполеты увеличены, под ними видна серая деталь, повторяющая форму плеча. Добавлены три золотые петли разной длины. Чёрная стойка вокруг шеи снята: видимая шея принадлежит исходной голове Хасслера.</p>
<div class="pair">'''
    page+=fig('step_08/front.png','Шаг 08 — открытая штатная шея, заметные эполеты и три петли аксельбанта')
    page+=fig('step_08/three_quarter.png','Общий вид; одобренная раскрытая полочка сохранена')
    page+='</div><h2>Посадка деталей</h2><div class="pair">'
    page+=fig('step_08/shoulder_detail.png','Золотой эполет перекрывает плечо; серая деталь лежит под ним')
    page+=fig('step_08/cord_detail.png','Петли разной длины обходят углубление между плечом и грудью')
    page+='</div><div class="pair">'+fig('step_08/collar_close.png','Штатная шея видна над низким краем внутренней одежды')+fig('step_08/shoulders_above.png','Положение эполетов и ткани сверху')+'</div>'
    page+='<details><summary>Сравнение с шагом 07 и исходным артом</summary><div class="pair">'
    page+=fig('step_07/front.png','Шаг 07: высокая чёрная стойка и один шнур')+fig('step_08/front.png','Шаг 08: свободная шея, увеличенные эполеты, три шнура')
    page+='</div><div class="reference">'+fig('source/art/hassler1.png','Исходный арт: перед')+fig('source/art/hassler2.png','Исходный арт: спина')+fig('step_08/back.png','Текущий вид сзади')+'</div></details>'
    page+='<details><summary>Пробные движения головы и рук</summary><div class="grid">'
    for f,label in [('head_turn_right','Поворот головы'),('head_nod','Наклон головы'),('shoulder_pose','Подъём рук'),('elbow_pose','Сгиб локтей'),('turn_pose','Поворот корпуса и головы'),('side','Профиль')]:page+=fig(f'step_08/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>После повторного открытия проверены девять поз: эполеты не пересекают мундир; свободные петли не пересекают ткань и друг друга; голова не пересекает мундир/воротник. Контакт первого шнура с эполетом ограничен первыми тремя сегментами в зоне крепления под ним. Край внутренней одежды следует штатному нижнему контуру шеи. Геометрия головы/шеи и 28 костей сохранена.</p>
<p>UV без вырожденных треугольников, до четырёх костей на вершину. Тело с толщиной ткани, кантом, подложками и тремя петлями: {check['body_triangles_with_modifiers']:,} треугольников, без головы и кистей. Эполеты сохраняют текстуры и UV Дитриха.</p>
<p>Это офлайн-версия Blender для оценки верхней части. Показаны пробные позы, а не полный набор игровых анимаций. Экспорт, LOD и установка в игру ещё не выполнялись. Предыдущие шаги сохранены.</p></html>'''
    seam=max(a['neck_seam_max_error_m'] for a in check['pose_audits'])
    readme=f'''ХАССЛЕР — ШАГ 08: ПОСАДКА ВЕРХА, ТРИ ПЕТЛИ, ОТКРЫТАЯ ШЕЯ

Blender: hassler_native_upper.blend. Галерея: ../index.html.
Предыдущая версия step_07 сохранена; галерея ../index_step07.html.
Источник формы — исходный арт Хасслера и одобренное раскрытие из step_07.

ЧТО ИЗМЕНЕНО
Красная ткань у правого плеча убрана внутрь и вниз, под эполет. Форма и
геометрия нижней раскрытой золотой полочки с красной изнанкой сохранены.
Эполеты увеличены по ширине от внутренней опоры на 12%, в глубину на 38%,
сдвинуты вперёд на 14 мм и выше на 20 мм относительно step_07. Их прежние
пропорции/изгиб использованы как основа; текстура и UV Дитриха сохранены.
Серая объёмная подложка построена между фактической нижней стороной золотого
верха и поверхностью плеча. Её верх следует весам эполета, низ — весам плеча.
Золотая оболочка имеет толщину 1.5 мм. Подложка закрывает пустоту под ней.

Аксельбант теперь состоит из трёх отдельных петель разной длины. Основной
шнур диаметром 6.6 мм, два остальных — 5.6 мм. Они выходят из зоны под левым
эполетом и закрепляются на левой полочке. Шнуры перекрывают в воздухе резкое
углубление плеча/груди; прямое следование глубине этого углубления давало
пересечения. Первые четыре сечения принадлежат зоне крепления под эполетом.

Чёрная высокая стойка полностью снята (48 граней). Голова и её штатная шея
не менялись, новая кожа/шейная геометрия не добавлялась. Верхний край внутренней
одежды совпадает с фактическим нижним контуром штатной шеи и привязан к той же
кости Body_Head. Ниже края сохраняются плавно распределённые веса торса.
Одежда не поднимается по шее и не закрывает её новой высокой оболочкой.
Для наклона головы вперёд верх задней части серого воротника отведён назад
до 14 мм и немного опущен (до 4 мм), с плавным переходом к прежнему основанию.
Передние концы воротника и раскрытая полочка при этом не менялись.

ОБЪЕКТЫ ДЛЯ РЕДАКТИРОВАНИЯ
EDIT — native costume upper study:
10 Sewn uniform — finished shoulder fit: основная оболочка с рукавами,
  воротником и одобренной свисающей полочкой. UV, грани и веса step_07 сохранены.
15 Red lining — tucked below shoulder board: верхняя красная ткань.
14 Epaulettes — enlarged seated gold boards: увеличенные золотые эполеты.
  Исправлены веса: они не привязаны к предплечьям/кистям. Вклад верхней части
  руки ограничен 30%; остальная привязка следует плечу/торсу.
16 Grey shoulder supports — seated under gold roofs: объёмная серая подложка.
13.1 / 13.2 / 13.3 Aiguillette — graduated gold loop: отдельные петли.
  Их траектории, радиусы и координаты сечений есть в report.json / cords;
  на каждом объекте сохранён editable_centerline.
12 Inner shirt — native open neckline: низкий открытый край внутренней одежды.
11 Red binding — continuous 3 mm seams.005: кант подогнан к плечу.

Все ARCHIVE / REFERENCE скрыты одновременно во viewport и render. Исходная
голова, кисти, низ и пояс, скелет и предыдущий step_07 сохранены без изменений.

ПРОВЕРКИ СОХРАНЁННОГО ФАЙЛА
SHA256: {check['blend_sha256']}
Повторное открытие; неизменность головы/шеи, кистей, низа и 28 костей;
неизменность раскрытой полочки; связность основной оболочки; UV и веса.
Девять поз: покой, локти, плечи, поворот корпуса/головы, два поворота головы,
наклон вперёд, взгляд вверх, наклон вбок. Зазор шва шеи не более {seam:.9f} м.
Во всех этих позах проверены пересечения треугольников: эполет/мундир — 0;
голова/мундир — 0; шнуры/мундир — 0; шнуры между собой — 0. Контакт первого
шнура с эполетом остаётся только в зоне крепления (сечения 1–3, вне свободной
части петель). Это соединение деталей, не заявление об отсутствии любых
соприкосновений в многослойном костюме.
У серой подложки отдельно учтён внутренний контакт с серой изнанкой эполета;
его внешняя золотая поверхность не пробивается (0 пересечений в девяти позах).
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольников, без головы/кистей.

Это пробные Blender-позы, а не полная проверка игровых анимаций. Верх подготовлен
для визуального согласования; финальный DFM, LOD и установка пока не делались.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step08.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step08_check.py
python tools/character_rounding/hassler_step08_review.py

Ручные правки сохранять отдельным .blend рядом: hassler_native_upper.blend
автоматически пересобирается генератором из step_07.
'''
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if p!='step_08/README.txt' and not (TOP/p).is_file()];assert not missing,missing
    (OUT/'README.txt').write_text(readme,encoding='utf8');(TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущий вариант: шаг 08 — подогнанные увеличенные эполеты, три петли аксельбанта, открытая штатная шея.\nBlender: step_08/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_08/README.txt. Предыдущие шаги сохранены.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 08, плечи, три петли аксельбанта и открытая штатная шея.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_08/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'body_triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
