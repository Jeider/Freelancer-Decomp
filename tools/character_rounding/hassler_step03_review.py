"""Review package for the connected tunic iteration; previous steps are kept."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_03'

def fig(path,label,reference=False):
    assert (TOP/path).exists(),path
    return f'<figure><a href="{path}"><img class="{"reference" if reference else "model"}" loading="lazy" src="{path}" alt="{label}"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==check['blend_sha256']
    refs=TOP/'source/art';refs.mkdir(exist_ok=True)
    for name in ('hassler1.png','hassler2.png'):
        original=Path('D:/Work/Meshy/Hassler1')/name;dest=refs/name
        if not dest.exists():dest.write_bytes(original.read_bytes())
        assert dest.read_bytes()==original.read_bytes()
    old=TOP/'index_step02.html'
    if not old.exists():old.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 03: китель-жилет</title>
<style>body{background:#151b22;color:#e7eef5;font:17px system-ui;margin:30px auto;padding:0 24px;max-width:1600px}h1{font-size:30px}a{color:#8cd0ff}p{line-height:1.55;max-width:1120px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.artpair{display:grid;grid-template-columns:1fr 2fr 1fr 2fr;gap:12px}figure{margin:0;background:#26303a}img{width:100%;display:block}.reference{height:520px;object-fit:contain;background:#eee}.artpair .model{height:520px;object-fit:contain}figcaption{padding:12px}details{margin:24px 0}h2{font-size:23px;margin-top:30px}@media(max-width:950px){.grid,.pair,.artpair{grid-template-columns:1fr}.reference{height:420px}}</style>
<h1>Хасслер — шаг 03: цельный китель-жилет</h1>
<p><a href="step_03/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_03/README.txt">Устройство модели</a> · <a href="step_03/validation.json">Проверки</a> · <a href="index_step02.html">Шаг 02</a></p>
<p>Верх перестроен в общую оболочку кителя-жилета. Золотые плечевые участки идут к основанию воротника и переходят в отделку спины. Сам воротник имеет внутреннюю стойку, перегиб и свободные асимметричные концы. Для объёма над ремнём изучен настоящий li_scrote_body.</p>
<p>Красный кант шириной 3 мм проходит по открытым краям, проймам, подолу и границам отделки. Скрытый шов под отворотом не окантован. Фактура золота взята у Дитриха; голова сохраняет посадку ниже на 25 мм из предыдущего шага.</p>
<div class="grid">'''
    for f,label in [('front','Общий вид спереди'),('three_quarter','Связь воротника, плеч и жилета'),('back','Непрерывная плечевая отделка и спина')]:page+=fig(f'step_03/{f}.png',label)
    page+='</div><h2>Сверка с исходным артом</h2><div class="artpair">'
    page+=fig('source/art/hassler1.png','Исходный арт — спереди',True)+fig('step_03/front.png','Новый верх — спереди')
    page+=fig('source/art/hassler2.png','Исходный арт — сзади',True)+fig('step_03/back.png','Новый верх — сзади')
    page+='</div><p>Контуры кроя интерпретированы вручную по этому небольшому арту. Это визуальный прототип для дальнейшей правки формы; нижняя часть костюма и кобура не входят в текущий шаг.</p>'
    page+='<h2>Воротник и объём над поясом</h2><div class="grid">'
    for f,label in [('collar_close','Стойка и отворот крупно'),('waist_close','Объём и красный подол над штатным поясом'),('side','Профиль жилета и плеча')]:page+=fig(f'step_03/{f}.png',label)
    page+='</div><details><summary>До и после: одна камера</summary><div class="pair">'
    page+=fig('step_02/three_quarter.png','Шаг 02 — отдельные детали верха')+fig('step_03/three_quarter.png','Шаг 03 — общий объём и связанная сетка')
    page+='</div></details><details><summary>Референс объёма — настоящий li_scrote_body</summary><div class="pair">'
    page+=fig('source/scrote/study/front.png','Scrote: отдельный объём жилета над ремнём')+fig('source/scrote/study/side.png','Scrote: профиль и свободный нижний край')
    page+='</div></details><details><summary>Геометрия и пробные позы</summary><div class="pair">'
    for f,label in [('clay_front','Отсечение обратных граней — спереди'),('clay_back','Отсечение обратных граней — сзади'),('turn_pose','Синтетический поворот'),('shoulder_pose','Синтетический подъём плеч')]:page+=fig(f'step_03/{f}.png',label)
    page+='</div></details>'
    page+=f'<p>После повторного открытия: одна связная сетка кителя с воротником, четыре штатных отверстия одежды (низ, горловина и две проймы), 70 общих вершин шва воротника. Сохранены 72 грани пояса, голова, кисти и все 28 костей предыдущего шага. Контрольные меши не имеют треугольников с нулевой площадью UV.</p><p>С толщиной ткани и объёмным кантом тело содержит {check["body_triangles_with_modifiers"]} треугольников, без отдельных головы и кистей. Это пока подробный Blender-исходник; оптимизация экспорта и LOD не выполнялись. Все изображения — офлайн-рендеры. В игру модель не установлена; игровые анимации не проверены.</p></html>'
    (TOP/'index.html').write_text(page,encoding='utf8')
    readme='''ХАССЛЕР — ШАГ 03: КИТЕЛЬ-ЖИЛЕТ

Открывать hassler_native_upper.blend. Галерея: ../index.html.
Родитель step_02/hassler_native_upper.blend сохранён без изменений.

КРОЙ И ИСТОЧНИКИ
Небольшие исходные hassler1.png/hassler2.png — основные визуальные ориентиры.
Плечевая золотая часть интерпретирована как продолжение кителя к воротнику,
с переходом в Y-образную отделку спины. Эти контуры заданы вручную и хранятся
в pattern.json. Автоматического распознавания изображения здесь нет.
li_scrote_body изучен по настоящему DFM, текстурным видам и профилю: он задаёт
принцип свободного объёма жилета над ремнём. Его костюм не скопирован целиком.
Wilham использован как конструктивный пример внутренней стойки и перегиба.
Геометрия нового воротника авторская, со свободным длинным левым концом.
Золотые ткани — rh_deidrich_body: отдельные исходные рисунки плеч и кителя.

УСТРОЙСТВО BLENDER
10 Tunic-vest — continuous shell and collar: общая связная контрольная сетка.
Цветные поля являются её гранями; это не набор наложенных друг на друга пластин.
Воротник пришит общими вершинами. Отдельный модификатор задаёт толщину 2.4 мм.
11 Red binding — continuous 3 mm seams: кант из границ кроя и открытых краёв.
Его радиус везде 1.5 мм; скрытые швы под отворотом и стыки двух золотых рисунков
исключены. Это намеренно отдельная редактируемая деталь, как настоящая тесьма.
12 Inner shirt — torso and fitted black neck: подкладка и нижняя рубашка,
закрывающая проймы и горловину. Она подогнана внутрь оболочки жилета.
13 Aiguillette — fitted to tunic volume: шнур на новом объёме.
00 Native sleeves and lower body: штатные рукава и низ; скрытые торсовые грани
старой формы убраны в этом производном варианте. Пояс сохранён полностью.
Голова, кисти, их геометрия и посадка, а также все 28 костей — как в шаге 02.
Вес жилета, канта и нижней рубашки привязан к корпусу и ключицам. Ближайшие
веса верхних частей рук у пройм перенесены на кости корпуса: жилет не должен
вытягиваться вслед за рукой. Штатные веса рукавов сохранены.

ARCHIVE — step 02 separate panels содержит прежний набор деталей.
Архивные коллекции отключены и в viewport, и при рендере. Исходники игрового
тела дополнительно доступны в прежней коллекции ARCHIVE — original references.
Для ручных правок сохранять отдельный .blend в этой же папке: генератор заменяет
автоматический hassler_native_upper.blend внутри step_03.

ПРОВЕРКА И ГРАНИЦЫ ЭТАПА
validation.json связан с SHA256 сохранённого файла. Повторно проверены связность,
общий шов воротника, нормали, открытые контуры, веса и UV; сохранность пояса,
нижних граней, головы, кистей и костей; неизменность исходных DFM и предыдущего
Blender. Границы контроля одежды — низ, горловина и две проймы; толщина закрывает
их торцы. Показаны реальные отсечения обратных граней и синтетические позы.
Числа треугольников в отчёте включают Solidify и объёмную тесьму. Это подробный
редактируемый прототип; финальная игровая сетка и LOD ещё не подготовлены.
Игровых анимаций, запуска игры, DFM-экспорта и установки не было.

ПЕРЕСБОРКА ИЗ КОРНЯ РЕПОЗИТОРИЯ
python -B tools/character_rounding/hassler_scrote_prepare.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step03.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step03_check.py
python -B tools/character_rounding/hassler_step03_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    p=TOP/'README.txt';text=p.read_text(encoding='utf8')
    if text.startswith('ТЕКУЩИЙ ВАРИАНТ:'):text=text.split('\n\n',1)[1]
    p.write_text('ТЕКУЩИЙ ВАРИАНТ: шаг 03 — step_03/hassler_native_upper.blend. Общая сетка кителя-жилета, воротника и плеч; ровный красный кант. Подробности: step_03/README.txt.\n\n'+text,encoding='utf8')
    p=TOP.parents[1]/'README.txt';text=p.read_text(encoding='utf8')
    lines=text.splitlines();lines[0]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 03, цельный китель-жилет.'
    lines[1]='Blender: hassler/native_upper/step_03/hassler_native_upper.blend.';p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    print('UPDATED',TOP/'index.html')

if __name__=='__main__':main()
