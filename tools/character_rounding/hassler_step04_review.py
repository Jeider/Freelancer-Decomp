"""Publish the checked offline iteration in the existing Hassler topic gallery."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_04'

def fig(path,label,art=False):
    assert (TOP/path).is_file(),path
    return f'<figure><a href="{path}"><img loading="lazy" class="{"art" if art else "model"}" src="{path}" alt="{label}"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    assert hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()==check['blend_sha256']
    previous=TOP/'index_step03.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 04: раскрытый мундир</title>
<style>body{background:#151b22;color:#e7eef5;font:17px system-ui;margin:30px auto;padding:0 24px;max-width:1600px}h1{font-size:30px}a{color:#8cd0ff}p{line-height:1.55;max-width:1150px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.refs{display:grid;grid-template-columns:1fr 2fr 1fr 2fr;gap:12px}figure{margin:0;background:#26303a}img{width:100%;display:block}.art{height:520px;object-fit:contain;background:#ddd}.refs .model{height:520px;object-fit:contain}figcaption{padding:12px}details{margin:24px 0}h2{font-size:23px;margin-top:30px}@media(max-width:950px){.grid,.pair,.refs{grid-template-columns:1fr}.art{height:420px}}</style>
<h1>Хасслер — шаг 04: раскрытый мундир</h1>
<p><a href="step_04/hassler_native_upper.blend">Blender со скелетом</a> · <a href="step_04/README.txt">Устройство модели</a> · <a href="step_04/validation.json">Проверки</a> · <a href="index_step03.html">Предыдущий шаг 03</a></p>
<p>Правый борт расстёгнут и отогнут наружу. Красная область — внутренняя сторона самого кителя, видимая на свисающем отвороте. Она продолжает ту же ткань, что и серый воротник; длинный левый конец воротника также опущен на грудь. Верх перестроен после пояснения пользователя о крое офицерского мундира.</p>
<p>Вернулись выступающие эполеты с рисунком Дитриха и серой нижней подкладкой. Золотая плечевая часть кителя продолжается под ними к воротнику и к Y-образной отделке спины. Красные боковые швы на спине опираются на линии штатного rh_male_elite_body. Аксельбант сохранён без новой детализации.</p>
<div class="grid">'''
    for f,label in [('front','Раскрытый правый борт и свисающий воротник'),('three_quarter','Отворот в объёме и выступающие эполеты'),('back','Плечевая отделка, задние полосы и красные швы')]:
        page+=fig(f'step_04/{f}.png',label)
    page+='</div><h2>Крой и свободный край ткани</h2><div class="grid">'
    for f,label in [('collar_close','Красная сторона отогнутого кителя крупно'),('fold_side','Отворот отделён от груди реальной геометрией'),('clay_fold','Тот же перегиб без текстур, с отсечением обратных граней')]:
        page+=fig(f'step_04/{f}.png',label)
    page+='</div><h2>Исходный арт</h2><div class="refs">'
    page+=fig('source/art/hassler1.png','Хасслер — исходный вид спереди',True)+fig('step_04/front.png','Новая конструкция верха')
    page+=fig('source/art/hassler2.png','Хасслер — исходный вид сзади',True)+fig('step_04/back.png','Новый вид со спины')
    page+='</div><p>Это ручная интерпретация небольшого арта и пояснения пользователя. Фотография мундира ниже объясняет застёжку и устройство борта; она не заменяет рисунок Хасслера и его цвета.</p>'
    page+='<details><summary>Референсы конструкции</summary><div class="grid">'
    page+=fig('source/open_uniform_study/user_uniform_reference.png','Мундир, присланный пользователем: пример кроя',True)
    page+=fig('source/open_uniform_study/dietrich_front.png','Настоящий Дитрих: форма выступающих плечевых деталей')
    page+=fig('source/open_uniform_study/elite_back.png','Настоящий rh_male_elite_body: боковые швы спины')
    page+='</div></details><details><summary>Шаг 03 и шаг 04 — одна камера</summary><div class="pair">'
    page+=fig('step_03/three_quarter.png','Шаг 03: красная вставка на закрытом верхе')+fig('step_04/three_quarter.png','Шаг 04: единая ткань с отогнутым бортом')
    page+='</div></details><details><summary>Геометрия и пробные позы</summary><div class="pair">'
    for f,label in [('side','Профиль свободного отворота'),('turn_pose','Поворот корпуса и головы'),('shoulder_pose','Подъём плеч: проверочная поза скелета'),('clay_front','Геометрия без текстур'),('clay_back','Геометрия со спины')]:
        page+=fig(f'step_04/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>Сохранённый Blender повторно открыт и проверен. Китель и отвороты образуют одну связную контрольную сетку с {check['shared_tunic_fold_vertices']} общими вершинами перехода. Красный отворот отстоит от основной ткани груди примерно на 18–45 мм по проверочным центрам граней. Голова, кисти, штатные рукава, пояс, низ и все 28 костей сохранены из шага 03. В проверенных UV нет треугольников с нулевой площадью.</p>
<p>Тело с толщиной ткани, кантом и эполетами: {check['body_triangles_with_modifiers']:,} треугольников, без отдельных головы и кистей. Это подробный Blender-прототип формы. Экспорт, оптимизация и LOD остаются следующим этапом. Все виды здесь — офлайн-рендеры; реальные игровые анимации не проверялись, в игру вариант не устанавливался.</p></html>'''
    (TOP/'index.html').write_text(page,encoding='utf8')
    missing=[url for url in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/url).is_file()
             and url!='step_04/README.txt']
    assert not missing,missing
    readme='''ХАССЛЕР — ШАГ 04: РАСКРЫТЫЙ МУНДИР

Открывать hassler_native_upper.blend. Галерея: ../index.html.
Родитель step_03 сохранён без изменений; его галерея — ../index_step03.html.

УТОЧНЕНИЕ КОНСТРУКЦИИ ОТ ПОЛЬЗОВАТЕЛЯ
Красный цвет — часть самого кителя, не нижняя красная рубашка.
Правый борт расстёгнут, отогнут наружу и свисает; видна его красная сторона.
Серый воротник — продолжение этой конструкции, его свободный конец также свисает.
Фотография офицерского мундира объясняет крой. Основная форма/палитра остаются по
hassler1.png/hassler2.png. Задние красные линии сверены со швами rh_male_elite_body.
Выступающие эполеты возвращены; отделка кителя доходит под них и к воротнику.
Аксельбант на этом этапе не перерабатывался.

РЕДАКТИРОВАНИЕ
10 Open tunic — turned red facing and hanging collar: одна связная сетка кителя.
Красный отворот и серый воротник выделяются по материалам; редактируемые контуры
перегиба и свободного края хранятся также в report.json / fold / *_rail.
Красное находится только на отвёрнутой ткани, прежняя красная накладка удалена
из нового видимого кителя. Архив шага 03 остаётся скрытым.
Толщина ткани 2.4 мм задаётся Solidify после Armature.
11 Red binding: отдельная окантовка диаметром 3 мм, полученная из границ кроя.
12 Inner shirt: прежний чёрный ворот нижнего слоя и зелёная внутренняя оболочка.
14 Projecting epaulettes: форма штатных плечевых деталей Рейхмана, UV/текстура
Дитриха из шага 02; посадка подогнана к общему плечу, серая подкладка 8 мм.
13 Aiguillette: посадка предыдущего шага, без новой детализации.
00 Native sleeves and lower body: неизменённые рукава и низ из шага 03.
Голова, кисти и скелет также сохранены точно; повторного опускания головы нет.
Все ARCHIVE-коллекции отключены одновременно в viewport и render.

Для ручной правки сохранять отдельный .blend рядом: генератор пересобирает
автоматический hassler_native_upper.blend внутри step_04.

ВОСПРОИЗВЕДЕНИЕ И ПРОВЕРКИ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step04.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step04_check.py
python tools/character_rounding/hassler_step04_review.py
Генератор начинает с сохранённого step_03; исходники/игра доступны только для чтения.
validation.json связан с SHA256 готового Blender и проверяет сохранность родителя,
головы/кистей/рукавов/пояса/низа/скелета, общую сетку, границы, UV и веса.
Геометрический зазор перед грудью измеряется отдельно от цвета материала.
Показаны пробные позы и рендеры с отсечением обратных граней.
Это не полноценная проверка всех игровых анимаций и не готовый игровой экспорт.
Оптимизация тела и LOD отложены до принятия формы. В игру не установлено.
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    intro='Текущий вариант: шаг 04 — раскрытый мундир, свисающий красный отворот и воротник.\nBlender: step_04/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_04/README.txt. Предыдущие шаги сохранены.\n\n'
    path=TOP/'README.txt';old=path.read_text(encoding='utf8')
    if not old.startswith(intro):path.write_text(intro+old,encoding='utf8')
    index=ROOT/'out/character_rounding/README.txt';text=index.read_text(encoding='utf8')
    text=text.replace('hassler/native_upper/index.html — шаг 03, цельный китель-жилет.',
                      'hassler/native_upper/index.html — шаг 04, раскрытый мундир и свисающий отворот.')
    text=text.replace('Blender: hassler/native_upper/step_03/hassler_native_upper.blend.',
                      'Blender: hassler/native_upper/step_04/hassler_native_upper.blend.')
    index.write_text(text,encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':check['blend_sha256'],'body_triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))

if __name__=='__main__':main()
