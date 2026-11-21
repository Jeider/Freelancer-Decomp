"""Publish the reviewed, saved step 07 next to the user's exact drawing."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_07'

def fig(path,label):return f'<figure><a href="{path}"><img src="{path}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==check['blend_sha256']
    previous=TOP/'index_step06.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 07: опущенная полочка мундира</title>
<style>body{background:#161c24;color:#e7eef5;font:17px system-ui;margin:32px auto;padding:0 24px;max-width:1540px}h1{font-size:30px}a{color:#91d3ff}p{line-height:1.6;max-width:1200px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}figure{margin:0;background:#28323d}img{width:100%;display:block}figcaption{padding:12px}details{margin:28px 0}summary{cursor:pointer;margin-bottom:16px}h2{margin-top:32px;font-size:23px}@media(max-width:850px){.pair,.grid{grid-template-columns:1fr}}</style>
<h1>Хасслер — шаг 07: раскрыта золотая полочка</h1>
<p><a href="step_07/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_07/README.txt">Устройство и редактирование</a> · <a href="step_07/validation.json">Проверки</a> · <a href="index_step06.html">Предыдущий шаг 06</a></p>
<p>На стороне правой руки персонажа — слева на фронтальном изображении — верхняя золотая часть заменена открытой красной тканью. Ниже диагонали сама золотая полочка отогнута наружу и опущена: видимая изнанка красная, обратная сторона золотая. Серый воротник заканчивается отдельно; центральная область шеи и груди чёрная.</p>
<div class="pair">'''
    page+=fig('source/open_uniform_study/user_front_opening_step07.png','Рисунок пользователя — основной ориентир этой правки')
    page+=fig('step_07/front.png','Шаг 07 — тот же фронтальный ракурс')
    page+='</div><h2>Сгиб принадлежит мундиру</h2><div class="pair">'
    page+=fig('step_07/collar_close.png','Красная ткань сверху, свободная полочка снизу, отдельное окончание воротника')
    page+=fig('step_07/fold_side.png','Отворот выступает над грудью; край и обратная сторона сохраняют золотую ткань')
    page+='</div><div class="pair">'+fig('step_07/three_quarter.png','Общий вид в три четверти')+fig('step_07/clay_fold.png','Форма складки без текстур, с отсечением обратных граней')+'</div>'
    page+='<details><summary>Сравнение с предыдущим вариантом</summary><div class="pair">'
    page+=fig('step_06/front.png','Шаг 06 — высокий отворот, соединённый с воротником')+fig('step_07/front.png','Шаг 07 — полочка ниже, сгиб на золотом переде мундира')+'</div></details>'
    page+='<details><summary>Спина, профиль и пробные позы</summary><div class="grid">'
    for name,label in [('back','Спина'),('side','Профиль'),('turn_pose','Поворот корпуса и головы'),('shoulder_pose','Подъём рук'),('elbow_pose','Сгиб локтей')]:page+=fig(f'step_07/{name}.png',label)
    page+='</div></details>'
    page+=f'''<p>В сохранённом и повторно открытом файле полочка соединена с нижним золотым передом по {check['gold_facing_hinge_edges']} рёбрам. Общих вершин с серым воротником нет. Сохранены голова, кисти, 28 костей, пояс и низ, эполеты и рукава. Проверены UV, веса, закрытые швы рукавов и видимые материалы в раскрытии. Тело с толщиной ткани и кантом: {check['body_triangles_with_modifiers']:,} треугольников, без головы и кистей.</p>
<p>Это офлайн-прототип Blender для согласования формы. Контуры заданы вручную по рисунку; пробные позы не заменяют проверку игровых анимаций. Физика ткани не добавлялась. В игру модель не устанавливалась; предыдущие шаги сохранены.</p></html>'''
    readme=f'''ХАССЛЕР — ШАГ 07: ОПУЩЕННАЯ ЗОЛОТАЯ ПОЛОЧКА С КРАСНОЙ ИЗНАНКОЙ

Blender: hassler_native_upper.blend. Галерея: ../index.html.
Основной ориентир: ../source/open_uniform_study/user_front_opening_step07.png.
Исходный рисунок сохранён без изменений. Трактовка шага 06 заменена новым рисунком.

КОНСТРУКЦИЯ
Слева на фронтальном изображении (правая сторона персонажа) удалены верхние
золотые грани до эполета. Вместо них видна красная внутренняя ткань.
Ниже диагонального сгиба золотая полочка отогнута вперёд и свисает вниз.
Её видимая сторона — красная изнанка; обратная сторона — золотая ткань мундира.
Сгиб пришит к нижнему золотому переду, а не к серому воротнику.
Серый воротник заканчивается отдельно. Центральная область шеи/груди чёрная.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study содержит рабочую модель.
10 Sewn uniform — lowered gold front with red reverse:
  общая оболочка мундира, сшитые рукава, отдельное окончание воротника и
  отогнутая полочка. Последние грани — новая полочка; точные индексы есть
  в report.json / flap. Контур сгиба: flap.hinge_vertices; свободный край:
  flap.free_edge_vertices. Точечные boolean-атрибуты EDIT — hanging gold front,
  EDIT — front fold hinge и EDIT — free hanging edge помечают эти участки.
  Это атрибуты выделения, а не дополнительные группы весов скелета.
  Внешние грани полочки имеют золотой материал. Solidify назначает их обратной
  стороне красную ткань. Не менять золотой материал на красный на основной сетке:
  при текущем выворачивании это поменяет стороны местами.
15 Exposed red tunic lining — upper right chest:
  верхняя красная ткань, расположенная на 6 мм глубже удалённого золотого слоя.
  Её можно редактировать отдельно; прежнего золотого перекрытия под ней нет.
12 Inner shirt — torso and fitted black neck.002:
  неизменённая чёрная ткань шеи/груди. Широкая красная вставка шага 06 скрыта.
11 Red binding — continuous 3 mm seams.004:
  кант, построенный по актуальным границам и материалам.

Все ARCHIVE и REFERENCE отключены и во viewport, и в render. Предыдущий вариант
сохранён в step_06 и в архиве сцены. Голова, кисти, нижняя часть и пояс, эполеты,
аксельбант, скелет и ранее сшитые рукава сохранены. Геометрия независимого
воротника/рукавов берётся из step_05; step_06 — неизменённый родитель обзора.

ПРОВЕРКИ
SHA256 Blender: {check['blend_sha256']}
Повторное открытие: успешно. {check['gold_facing_hinge_edges']} общих рёбер сгиба с золотым передом;
0 общих вершин новой полочки с серым воротником. UV без вырожденных треугольников,
максимум 4 кости на вершину. Полная оболочка остаётся одной связной сеткой.
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольников, без головы/кистей.
Контуры вручную заданы по рисунку; это не автоматическая реконструкция изображения.
Показаны пробные Blender-позы. Игровые анимации, LOD и DFM ещё не финализировались.
Физика ткани не добавлялась; в игру ничего не устанавливалось.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step07.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step07_check.py
python tools/character_rounding/hassler_step07_review.py

Ручные изменения сохранять отдельным .blend рядом: hassler_native_upper.blend
пересобирается генератором. Предыдущие шаги генератор не перезаписывает.
'''
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if p!='step_07/README.txt' and not (TOP/p).is_file()]
    assert not missing,missing
    (OUT/'README.txt').write_text(readme,encoding='utf8');(TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущий вариант: шаг 07 — золотая полочка опущена по рисунку пользователя, красная изнанка снаружи; воротник отдельный, шея чёрная.\nBlender: step_07/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_07/README.txt. Предыдущие шаги сохранены.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';old=p.read_text(encoding='utf8');lines=old.splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 07, опущенная полочка по рисунку, отдельный воротник.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_07/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':check['blend_sha256']},ensure_ascii=False))

if __name__=='__main__':main()
