"""Reviewable offline delivery of the sewn uniform and corrected front layers."""
import json,hashlib,re
from pathlib import Path
from hassler_step04_review import fig
ROOT=Path(__file__).resolve().parents[2]
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_05'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==check['blend_sha256']
    previous=TOP/'index_step04.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 05: единый мундир и раскрытая золотая полочка</title>
<style>body{background:#151b22;color:#e7eef5;font:17px system-ui;margin:30px auto;padding:0 24px;max-width:1600px}h1{font-size:30px}a{color:#8cd0ff}p{line-height:1.55;max-width:1180px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.refs{display:grid;grid-template-columns:1fr 2fr 1fr 2fr;gap:12px}figure{margin:0;background:#26303a}img{width:100%;display:block}.art{height:520px;object-fit:contain;background:#ddd}.refs .model{height:520px;object-fit:contain}figcaption{padding:12px}details{margin:24px 0}h2{font-size:23px;margin-top:30px}@media(max-width:950px){.grid,.pair,.refs{grid-template-columns:1fr}.art{height:420px}}</style>
<h1>Хасслер — шаг 05: единый мундир и раскрытая золотая полочка</h1>
<p><a href="step_05/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_05/README.txt">Устройство модели</a> · <a href="step_05/validation.json">Проверки</a> · <a href="index_step04.html">Предыдущий шаг 04</a></p>
<p>Раскрывается золотая передняя полочка мундира. Её наружная сторона остаётся золотой, а отогнутая изнанка — красная. За раскрытием виден ещё один красный слой ткани. Серый воротник относится к другой части кроя и заканчивается выше, собственным свободным краем: красный отворот больше не является его продолжением.</p>
<p>Плечи и рукава сшиты с корпусом в одну сетку. Прежние открытые проймы жилета убраны; переход к штатным предплечьям также соединён общей геометрией. Зелёная ткань согласована по цвету. Эполеты, задняя отделка и аксельбант сохранены из предыдущего варианта.</p>
<div class="grid">'''
    for f,label in [('front','Единый мундир: плечи, рукава и раскрытая полочка'),('three_quarter','Красная изнанка и красный слой за ней'),('back','Закрытые плечевые соединения и задняя отделка')]:
        page+=fig(f'step_05/{f}.png',label)
    page+='</div><h2>Раздельные края воротника и полочки</h2><div class="grid">'
    for f,label in [('collar_close','Короткий правый конец серого воротника находится выше'),('fold_side','Раскрытая золотая полочка с красной внутренней стороной'),('clay_fold','Объём сгиба и два отдельных края без текстур')]:
        page+=fig(f'step_05/{f}.png',label)
    page+='</div><h2>Сравнение с шагом 04</h2><div class="pair">'
    page+=fig('step_04/three_quarter.png','Шаг 04: отворот продолжал воротник, рукава оставались внутри пройм')
    page+=fig('step_05/three_quarter.png','Шаг 05: раскрывается полочка; плечи и рукава соединены')
    page+='</div><details><summary>Арт и исходные ориентиры</summary><div class="refs">'
    page+=fig('source/art/hassler1.png','Исходный Хасслер спереди',True)+fig('step_05/front.png','Текущий верх мундира')
    page+=fig('source/art/hassler2.png','Исходный Хасслер сзади',True)+fig('step_05/back.png','Текущий вид со спины')
    page+='</div><p>Крой интерпретирован вручную по арту и уточнениям пользователя. Последнее уточнение о раскрытой золотой оболочке заменяет трактовку шага 04, где красный отворот продолжал серый воротник.</p></details>'
    page+='<details><summary>Проверочные позы и геометрия</summary><div class="pair">'
    for f,label in [('shoulder_pose','Подъём рук: сшитая пройма'),('elbow_pose','Сгиб локтей: стык с сохранённым предплечьем'),('turn_pose','Поворот корпуса и головы'),('clay_front','Общая сетка мундира без текстур'),('side','Профиль рукава и переднего раскрытия')]:
        page+=fig(f'step_05/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>После повторного открытия проверены обе плечевые петли и стыки предплечий: {check['closed_shoulder_and_forearm_stitches'][0]} и {check['closed_shoulder_and_forearm_stitches'][1]} общих вершин. Мундир с рукавами — одна связная сетка; отверстия остались только у шеи и нижнего края. Геометрия и UV {check['native_cuff_faces_positions_uv_preserved']} штатных граней наручей сохранены. Серый воротник и отогнутая полочка имеют разные свободные края и не соединены напрямую.</p>
<p>Голова, кисти, 28 костей, пояс и нижняя часть тела сохранены. UV проверены на вырожденные треугольники. Тело с толщиной ткани, кантом и внутренним красным слоем: {check['body_triangles_with_modifiers']:,} треугольников, без головы и кистей.</p>
<p>Это редактируемый офлайн-прототип формы. Изображения и пробные позы получены в Blender; полный набор игровых анимаций не проверен. В игру модель не установлена. Оптимизация экспорта и LOD остаются после принятия формы.</p></html>'''
    readme='''ХАССЛЕР — ШАГ 05: ЕДИНЫЙ МУНДИР И РАСКРЫТАЯ ЗОЛОТАЯ ПОЛОЧКА

Blender: hassler_native_upper.blend. Галерея: ../index.html.
Предыдущий step_04 сохранён неизменённым, галерея ../index_step04.html.

КОНСТРУКЦИЯ ПО ПОСЛЕДНЕМУ УТОЧНЕНИЮ ПОЛЬЗОВАТЕЛЯ
Золотой мундир раскрывается как оболочка: золотой снаружи, красный изнутри.
Красная ткань видна также ЗА отогнутой золотой полочкой.
Серый воротник относится к другой части кроя; справа он имеет собственный
короткий свободный край выше полочки. Это не красный конец серого воротника.

ЧТО ИЗМЕНИЛОСЬ
10 Sewn uniform — sleeves and opened gold front: корпус, новые плечевые
переходы, рукава и сохранённые штатные наручи соединены общей сеткой.
Открытых пройм жилета больше нет. Стыки с исходными предплечьями также сварены
общими вершинами, без T-стыков; веса плавно переходят от корпуса к рукам.
Зелёная ткань согласована между корпусом и рукавами. Нормали рукавов перенесены
с фактической штатной модели с плавным переходом по весам костей: это сглаживает
тень у стыка плотной авторской сетки и исходного предплечья. Геометрия и UV штатных
наручей сохранены. Плечевой переход авторский; рукав не является цилиндром,
его конечные контуры взяты с фактических пройм и сечения штатного предплечья.

Полочка имеет золотой материал на наружной поверхности. У Solidify отдельная
таблица внутренних материалов: обратная сторона золотого кителя — красная.
На отогнутой полочке к наблюдателю обращена именно эта изнанка.
Серый воротник пришит к другой части горловины, его конец не соединён с полочкой.
Группы индексов граней/краёв доступны в report.json / flap и collar.
15 Red coat underlap: красная внутренняя ткань за раскрытием. Чёрная шея остаётся.
11 Red binding: красный кант; технический стык рукава на уровне предплечья
не подчёркивается кантом. 14 Epaulettes и 13 Aiguillette — предыдущая посадка.
00 Native lower body and belt: неизменённые исходные вершины, пояс и низ.
Все прежние верхние детали доступны в скрытом ARCHIVE шага 04.

ПРОВЕРКА
validation.json привязан к SHA256 сохранённого и повторно открытого Blender.
Проверены связность, швы плеч/предплечий, нормали отогнутой ткани, отдельное
окончание воротника, золотой наружный/красный внутренний материалы, UV и веса.
Проверена сохранность головы, кистей, скелета, пояса, низа и геометрии/UV наручей.
Показаны пробные позы плеч, локтей и поворота, а также отсечение обратных граней.
Это не полная игровая проверка всех анимаций и не готовый экспорт/LOD.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step05.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step05_check.py
python tools/character_rounding/hassler_step05_review.py
Генератор начинает с step_04. Для ручных правок сохранять отдельный .blend рядом:
автоматический hassler_native_upper.blend пересобирается генератором.
Игра и исходные DFM не изменяются; модель не установлена в игру.
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    (TOP/'index.html').write_text(page,encoding='utf8')
    missing=[u for u in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/u).is_file()];assert not missing,missing
    intro='Текущий вариант: шаг 05 — единый мундир с рукавами; раскрытая золотая полочка с красной изнанкой и отдельным концом серого воротника.\nBlender: step_05/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_05/README.txt. Предыдущие шаги сохранены.\n\n'
    path=TOP/'README.txt';old=path.read_text(encoding='utf8')
    if not old.startswith(intro):path.write_text(intro+old,encoding='utf8')
    path=ROOT/'out/character_rounding/README.txt';old=path.read_text(encoding='utf8')
    old=old.replace('hassler/native_upper/index.html — шаг 04, раскрытый мундир и свисающий отворот.',
                    'hassler/native_upper/index.html — шаг 05, сшитые рукава, раскрытая золотая полочка и отдельный воротник.')
    old=old.replace('Blender: hassler/native_upper/step_04/hassler_native_upper.blend.',
                    'Blender: hassler/native_upper/step_05/hassler_native_upper.blend.')
    path.write_text(old,encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':check['blend_sha256'],'body_triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
