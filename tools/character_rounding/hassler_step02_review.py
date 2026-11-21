"""Publish the local step-02 gallery and keep the topic entry current."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_02'

def figure(path,label):
    assert (TOP/path).is_file(),path
    return f'<figure><a href="{path}"><img loading="lazy" src="{path}" alt="{label}"></a><figcaption>{label}</figcaption></figure>'

def main():
    report=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==report['blend_sha256']
    old=TOP/'index_step01.html'
    if not old.exists():old.write_bytes((TOP/'index.html').read_bytes())
    gallery='''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — шаг 02</title>
<style>body{background:#151b22;color:#e7eef5;font:17px system-ui;margin:30px auto;padding:0 24px;max-width:1500px}h1{font-size:30px}a{color:#8cd0ff}p{line-height:1.55;max-width:1100px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#26303a}img{width:100%;display:block}figcaption{padding:12px}details{margin:22px 0}h2{font-size:23px;margin-top:30px}@media(max-width:900px){.grid,.pair{grid-template-columns:1fr}}</style>
<h1>Хасслер — шаг 02: ниже посадка головы, новый воротник и отделка</h1>
<p><a href="step_02/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_02/README.txt">Устройство и правки</a> · <a href="step_02/validation.json">Проверки</a> · <a href="index_step01.html">Предыдущая галерея</a></p>
<p>Голова опущена на <b>25 мм</b> относительно плеч вместе с точкой вращения. Её форма и UV сохранены.
Воротник взят из настоящей модели Wilham, подогнан ниже и переработан в асимметричный перегиб по арту Хасслера.
Геометрия эполет осталась от Райхмана; текстура перенесена с Дитриха. Нагрудная и задняя отделка используют его отдельную тканевую текстуру.</p>
<p>Это отдельный прототип верха. Все виды — офлайн-рендеры Blender; в игру он не установлен.</p>
<div class="grid">'''
    for f,label in [('front','Вид спереди'),('three_quarter','Посадка головы и воротника'),('back','Перегиб воротника и задняя отделка')]:
        gallery+=figure(f'step_02/{f}.png',label)
    gallery+='</div><h2>Одинаковая камера: первый и второй варианты</h2><div class="pair">'
    gallery+=figure('step_01/three_quarter.png','Шаг 01: прежняя высота головы, воротник и текстуры')
    gallery+=figure('step_02/three_quarter.png','Шаг 02: голова ниже на 25 мм, воротник Wilham, отделка Дитриха')
    gallery+='</div><details open><summary>Крупно: посадка и профиль</summary><div class="grid">'
    for f,label in [('collar_close','Фактура и конструкция складки'),('side','Профиль и положение головы'),('clay_neck','Геометрия с реальным отсечением обратных граней')]:
        gallery+=figure(f'step_02/{f}.png',label)
    gallery+='</div></details><details><summary>Поворот и использованные штатные модели</summary><div class="grid">'
    gallery+=figure('step_02/turn_pose.png','Синтетический поворот корпуса и головы; это не игровая анимация')
    gallery+=figure('source/collar_study/wilham.png','Настоящий воротник Wilham до подгонки')
    gallery+=figure('source/collar_study/dietrich.png','Текстуры Дитриха на его исходном теле')
    gallery+='</div></details>'
    gallery+=f'<p>Проверено после открытия сохранённого файла: форма головы, неизменность тела и кистей, 14 общих позиций шейного шва, веса и UV. Тело с новыми деталями и модификаторами: {report["body_triangles_with_modifiers"]} треугольников, без отдельных головы и кистей. Игровые анимации и DFM-экспорт ещё не проверялись.</p></html>'
    (TOP/'index.html').write_text(gallery,encoding='utf8')
    readme='''ХАССЛЕР — ШАГ 02

Файл: hassler_native_upper.blend. Обзор: ../index.html.
Родитель: ../step_01/hassler_native_upper.blend — сохранён без изменений.

ИЗМЕНЕНИЯ
Голова опущена на 0.025 м без изменения её формы, UV или весов.
Body_Head и Head_End опущены на ту же величину; иерархия сохранена.
Остальные 26 костей и геометрия штатного тела, кистей и эполет неизменны.
Скорректированные inverse bind и hp_head записаны в report.json для будущего
экспорта. Это пока Blender-посадка; перенос в DFM и совместимость с настоящими
игровыми анимациями требуют отдельной проверки.

Воротник построен из 52 реально выбранных треугольников rh_wilham_body.
Выбор сделан по UV острову воротника и пространственным координатам; скопированы
наружная и внутренняя стороны перегиба. Посадка снижена, передние концы сделаны
асимметричными. Сохранены UV ткани Wilham; красная окантовка переведена в серую
узлом материала, исходная текстура не изменена. Subdivision остаётся модификатором.

Эполеты: геометрия из rh_reichman_body, текстура из rh_deidrich_body,
материал rh_dedrich_body_1. Старая UV хранится первым слоем для сравнения,
активная развёртка Dietrich shoulder artwork получена переносом по соответствующей
поверхности левого/правого плеча. Происхождение каждой вершины: epaulette_uv_transfer.json.
Нагрудная панель, плечевая полоса и Y на спине используют отдельную ткань
rh_dedrich_body_3. UV непрерывны по общим координатам тела, без сбросов по треугольникам.
Это материал для прототипа; отдельный финальный атлас костюма пока не выпекался.

Чёрная вставка укорочена под новую посадку головы. Все 14 общих позиций её
присоединения к телу закреплены. Чёрный нагрудник отведён за красный лацкан:
в предыдущей версии они лежали на одинаковой глубине и пересекались.

РЕДАКТИРОВАНИЕ
Новые детали — отдельные объекты в EDIT — native costume upper study.
01 Collar — Wilham folded construction: редактируемая основа и модификатор сглаживания.
02 Epaulettes — Reichman source geometry: два UV слоя, активен материал Дитриха.
RIG — native Rheinland: положение головы уже подогнано; исходные inverse bind
изменённых костей сохранены как original_native_inverse_bind.
ARCHIVE и REFERENCE ART скрыты и в viewport, и при рендере.
Таймлайн содержит только синтетические позы для визуальной подгонки.
Ручные изменения сохранять отдельным .blend в этой же папке: пересборка заменяет
автоматический hassler_native_upper.blend, но не родительский step_01.

ПРОВЕРКИ
validation.json связан с SHA256 сохранённого Blender-файла.
Проверены форма головы и её смещение, кости, неизменность тела/кистей/эполет,
шейный шов, нормализация весов и отсутствие треугольников с нулевой площадью UV
в авторских мешах. Показаны текстурные виды, профиль, синтетический поворот и
геометрия с отсечением обратных граней. Это не проверка запуска в игре.
Исходные DFM, пользовательские файлы и игровые настройки не менялись.

ПЕРЕСБОРКА ИЗ КОРНЯ РЕПОЗИТОРИЯ
python -B tools/character_rounding/hassler_dietrich_prepare.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step02.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step02_check.py
python -B tools/character_rounding/hassler_step02_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    intro='ТЕКУЩИЙ ВАРИАНТ: шаг 02 — step_02/hassler_native_upper.blend. Голова ниже на 25 мм, воротник Wilham, текстуры Дитриха. Подробности: step_02/README.txt.\n\n'
    top_readme=TOP/'README.txt';text=top_readme.read_text(encoding='utf8')
    if text.startswith('ТЕКУЩИЙ ВАРИАНТ:'):text=text.split('\n\n',1)[1]
    top_readme.write_text(intro+text,encoding='utf8')
    topic=TOP.parents[1]/'README.txt';text=topic.read_text(encoding='utf8')
    text=text.replace('hassler/native_upper/index.html — шаг 01, верх костюма.','hassler/native_upper/index.html — шаг 02, ниже голова, воротник Wilham, текстуры Дитриха.')
    text=text.replace('Blender: hassler/native_upper/step_01/hassler_native_upper.blend.','Blender: hassler/native_upper/step_02/hassler_native_upper.blend.')
    topic.write_text(text,encoding='utf8')
    print('UPDATED',TOP/'index.html')

if __name__=='__main__':main()
