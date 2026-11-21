"""Review the corrected direction of the Hassler cross-front opening."""
import json,hashlib,re
from pathlib import Path
from hassler_step04_review import fig
ROOT=Path(__file__).resolve().parents[2]
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_06'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==check['blend_sha256']
    previous=TOP/'index_step05.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 06: продолжение левого воротника</title>
<style>body{background:#151b22;color:#e7eef5;font:17px system-ui;margin:30px auto;padding:0 24px;max-width:1600px}h1{font-size:30px}a{color:#8cd0ff}p{line-height:1.55;max-width:1180px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.refs{display:grid;grid-template-columns:1fr 2fr;gap:12px}figure{margin:0;background:#26303a}img{width:100%;display:block}.art{height:520px;object-fit:contain;background:#ddd}figcaption{padding:12px}details{margin:24px 0}h2{font-size:23px;margin-top:30px}@media(max-width:950px){.grid,.pair,.refs{grid-template-columns:1fr}.art{height:420px}}</style>
<h1>Хасслер — шаг 06: от левого воротника к раскрытой полочке</h1>
<p><a href="step_06/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_06/README.txt">Устройство и редактирование</a> · <a href="step_06/validation.json">Проверки</a> · <a href="index_step05.html">Предыдущий шаг 05</a></p>
<p>Длинный свисающий конец воротника со стороны левой руки персонажа теперь продолжается в общий отворот передней полочки. Правое плечо задаёт место застёжки: освобождённый угол опущен от него и повёрнут красной изнанкой наружу. Самостоятельный правый клапан из шага 05 заменён этой конструкцией.</p>
<p>Серый воротник и красная изнанка остаются разными участками отделки, но их общий край идёт непрерывно. Под раскрытием сохранена красная ткань; её поверхность подогнана к внутреннему слою, чтобы чёрная ткань не проступала треугольными просветами.</p>
<div class="grid">'''
    for f,label in [('front','Левая рука персонажа — справа на этом виде; от неё идёт длинный воротник'),('three_quarter','Общий отворот переда и освобождённый правый угол'),('collar_close','Переход от длинного серого конца к красной изнанке')]:
        page+=fig(f'step_06/{f}.png',label)
    page+='</div><h2>Направление раскрытия: шаг 05 и шаг 06</h2><div class="pair">'
    page+=fig('step_05/collar_close.png','Шаг 05: самостоятельный отогнутый угол справа')
    page+=fig('step_06/collar_close.png','Шаг 06: общий край продолжается от длинного левого воротника')
    page+='</div><div class="pair">'+fig('step_06/fold_side.png','Перегиб и глубина раскрытия')+fig('step_06/clay_fold.png','Связь участков ткани без текстур')+'</div>'
    page+='<details><summary>Исходный арт и сохранённая спина</summary><div class="refs">'
    page+=fig('source/art/hassler1.png','Исходный Хасслер',True)+fig('step_06/front.png','Текущая интерпретация раскрытия')
    page+='</div><div class="pair">'+fig('step_06/back.png','Плечи и задняя отделка')+fig('step_06/side.png','Профиль мундира')+'</div></details>'
    page+='<details><summary>Проверочные позы</summary><div class="grid">'
    for f,label in [('shoulder_pose','Подъём рук'),('elbow_pose','Сгиб локтей'),('turn_pose','Поворот корпуса и головы')]:page+=fig(f'step_06/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>После повторного открытия проверен общий шов: {check['left_collar_to_front_shared_vertices']} вершин и {check['left_collar_to_front_shared_edges']} рёбер напрямую соединяют длинный левый воротник с полочкой. Мундир с рукавами остаётся одной связной сеткой. Наружный материал полочки золотой, её обратная сторона красная. Красная подкладка следует поверхности внутреннего торса с зазором 2.5 мм.</p>
<p>Сохранены голова, кисти, скелет, низ, пояс, эполеты, аксельбант, закрытые швы рукавов и их сглаживание. Проверены UV и веса. Тело с толщиной ткани и кантом: {check['body_triangles_with_modifiers']:,} треугольников, без головы и кистей.</p>
<p>Это офлайн-прототип для оценки формы и кроя. Изображения и пробные позы получены в Blender. Полный набор игровых анимаций не проверялся; модель не установлена в игру. Предыдущие шаги сохранены.</p></html>'''
    readme='''ХАССЛЕР — ШАГ 06: ПРОДОЛЖЕНИЕ ЛЕВОГО ВОРОТНИКА В РАСКРЫТЫЙ ПЕРЕД

Blender: hassler_native_upper.blend. Галерея: ../index.html.
Предыдущий step_05 сохранён неизменённым; галерея ../index_step05.html.

ПОСЛЕДНЕЕ УТОЧНЕНИЕ ПОЛЬЗОВАТЕЛЯ
Ориентир — длинный конец воротника со стороны ЛЕВОЙ руки персонажа.
Раскрытый мундир продолжает именно этот конец. У правого плеча находилась
застёжка: после расстёгивания свободный угол открывается и свисает.
Это заменяет трактовку шага 05 с отдельным правым клапаном.
На фронтальном изображении левая рука персонажа находится справа.

УСТРОЙСТВО
10 Sewn uniform — left collar into released front: у длинного левого конца
воротника теперь общий поперечный шов с отворотом полочки — 6 вершин и 5 рёбер.
Серый участок и золотая полочка с красной изнанкой образуют непрерывный край.
Короткий правый конец воротника сохраняется на фиксированной стороне горловины.
Верхняя правая часть золотого переда немного раскрыта вниз, в пределах груди;
сшитые рукава, их геометрия/UV/веса и перенесённые штатные нормали сохранены.
Материалы изнанки явно назначены через Solidify: золотая полочка красная изнутри.

15 Red coat underlap — exact sewn backing: красный слой за раскрытием,
вырезанный по фактическим треугольникам внутренней ткани, с отступом 2.5 мм.
Старая приблизительная сетка подкладки оставляла просветы при новом раскрытии;
она сохранена только в отключённом архиве шага 05.

REFERENCE — fastening construction: скрытая коллекция с двумя ориентирами:
Right shoulder fastening — closed-position reference и Released corner.
Первая точка — авторский ориентир застёжки, не обнаруженный игровой hardpoint.
Она нужна для понимания направления раскрытия; новая пуговица не моделировалась.
Контуры и общий шов доступны в report.json / seam. Архивы и ориентиры отключены
одновременно в viewport и render. Остальные части персонажа сохранены из step_05.

ПРОВЕРКИ И ВОСПРОИЗВЕДЕНИЕ
validation.json привязан к SHA256 повторно открытого Blender. Проверены общий
шов воротника/полочки, замкнутые плечи/предплечья, сохранность исходных деталей,
UV, веса, материалы изнанки и зазор красной подкладки относительно чёрной ткани.
Приведены пробные позы и изображение с отсечением обратных граней.
Это не полная проверка игровых анимаций. Экспорт/LOD и установка не выполнялись.

python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step06.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step06_check.py
python tools/character_rounding/hassler_step06_review.py

Для ручной правки сохранять отдельный .blend рядом: автоматический файл
hassler_native_upper.blend пересобирается генератором из step_05.
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8');(TOP/'index.html').write_text(page,encoding='utf8')
    missing=[u for u in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/u).is_file()];assert not missing,missing
    intro='Текущий вариант: шаг 06 — длинный левый воротник продолжается в раскрытый перед мундира; свободный угол освобождён у правого плеча.\nBlender: step_06/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_06/README.txt. Предыдущие шаги сохранены.\n\n'
    path=TOP/'README.txt';old=path.read_text(encoding='utf8')
    if not old.startswith(intro):path.write_text(intro+old,encoding='utf8')
    path=ROOT/'out/character_rounding/README.txt';old=path.read_text(encoding='utf8')
    old=old.replace('hassler/native_upper/index.html — шаг 05, сшитые рукава, раскрытая золотая полочка и отдельный воротник.',
                    'hassler/native_upper/index.html — шаг 06, левый воротник продолжается в раскрытую полочку.')
    old=old.replace('Blender: hassler/native_upper/step_05/hassler_native_upper.blend.',
                    'Blender: hassler/native_upper/step_06/hassler_native_upper.blend.')
    path.write_text(old,encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':check['blend_sha256'],'body_triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
