"""Publish a review of step09 against the user's exact shoulder annotations."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_09'

def fig(path,label):return f'<figure><a href="{path}"><img src="{path}" loading="lazy"></a><figcaption>{label}</figcaption></figure>'

def main():
    check=json.loads((OUT/'validation.json').read_text(encoding='utf8'));build=json.loads((OUT/'report.json').read_text(encoding='utf8'));digest=hashlib.sha256((OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()
    assert digest==check['blend_sha256']==check['previews_bound_to_blend_sha256'] and check['clearance_checks_passed']
    previous=TOP/'index_step08.html'
    if not previous.exists():previous.write_bytes((TOP/'index.html').read_bytes())
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 09, плечи по разметке</title>
<style>body{margin:32px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:10px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.reference img{max-height:530px;object-fit:contain}.links{display:flex;gap:22px;flex-wrap:wrap;padding:14px 0}details{margin:24px 0}summary{cursor:pointer;color:#e8c780}.muted{color:#b7c0c8}.overlay{position:relative;max-width:800px;margin:auto}.overlay img:last-child{position:absolute;inset:0}input{width:100%;max-width:800px}code{font-size:14px}@media(max-width:760px){.pair,.grid{grid-template-columns:1fr}body{padding:0 12px;margin:18px auto}}</style>
<h1>Хасслер — шаг 09: плечи по твоей разметке</h1>
<p>Золотая часть продлена внутрь до воротника и синей границы. Красная ткань начинается ниже неё. Под эполетами — округлые серые наплечники; короткий серый конец воротника снова свисает.</p>
<nav class="links"><a href="step_09/hassler_native_upper.blend">Открыть Blender</a><a href="step_09/README.txt">Описание и редактирование</a><a href="step_09/validation.json">Проверки</a><a href="index_step08.html">Предыдущий шаг 08</a></nav>
<div class="pair">'''
    page+=fig('source/shoulder_fit_study/user_front_step09.png','Твоя разметка: золотые плечи и серый воротник над синей линией')+fig('step_09/front.png','Шаг 09: новая геометрия, тот же фронтальный ракурс')+'</div>'
    page+='''<details><summary>Наложить разметку на новую модель</summary><p>Ползунок меняет прозрачность исходного рисунка. Контуры интерпретированы вручную, это сравнение формы, а не автоматическая трассировка.</p><div class="overlay"><img src="step_09/front.png"><img id="drawing" src="source/shoulder_fit_study/user_front_step09.png" style="opacity:.5"></div><p style="text-align:center"><input aria-label="Прозрачность рисунка" type="range" min="0" max="100" value="50" oninput="document.getElementById('drawing').style.opacity=this.value/100"></p></details>
<h2>Серый наплечник под золотой деталью</h2><div class="pair reference">'''
    page+=fig('source/shoulder_fit_study/user_grey_shoulder_step09.png','Твоя отметка зоны наплечника')+fig('step_09/shoulder_detail.png','Новый округлый наплечник и протяжённый золотой верх; ракурс немного отличается')+'</div>'
    page+='<div class="pair">'+fig('step_09/three_quarter.png','Общий вид в три четверти')+fig('step_09/right_shoulder_detail.png','Сторона с красной тканью и свисающим серым концом воротника')+'</div>'
    page+='<details><summary>Воротник, плечи сверху и спина</summary><div class="grid">'
    for f,label in [('collar_close','Воротник и открытая штатная шея'),('shoulders_above','Посадка деталей сверху'),('back','Спина и задние края эполетов')]:page+=fig(f'step_09/{f}.png',label)
    page+='</div></details><details><summary>Пробные позы</summary><div class="pair">'
    for f,label in [('head_turn_right','Поворот головы'),('head_nod','Наклон головы'),('shoulder_pose','Подъём рук'),('turn_pose','Поворот корпуса и головы')]:page+=fig(f'step_09/{f}.png',label)
    page+='</div></details>'
    page+=f'''<p>Обе золотые детали имеют общий принцип формы и новую непрерывную UV-развёртку с текстурой Дитриха. Наружная полуширина — 280 мм, чуть меньше шага 08. Прибавка длины направлена внутрь, к воротнику и груди. Нижняя раскрытая полочка, три петли аксельбанта, штатная голова/шея, кисти и скелет сохранены.</p>
<p>Сохранённый .blend повторно открыт и проверен в девяти пробных позах. Проверенные пересечения: золотые эполеты с мундиром, серые наплечники с золотом, голова с воротником, свободные шнуры с одеждой и друг другом — 0. Убран старый перехлёст серой ткани у корня короткого воротника. UV не имеют вырожденных треугольников, до четырёх костей на вершину.</p>
<p class="muted">Офлайн-прототип для оценки формы: {check['body_triangles_with_modifiers']:,} треугольника в теле с толщиной ткани и дополнительными деталями, без головы и кистей. Пробные позы Blender не заменяют полный набор игровых анимаций. DFM, LOD и установка в игру пока не выполнялись. Шаг 08 сохранён.</p></html>'''
    seam=max(a['neck_seam_max_error_m'] for a in check['pose_audits'])
    readme=f'''ХАССЛЕР — ШАГ 09: ЭПОЛЕТЫ И НАПЛЕЧНИКИ ПО РАЗМЕТКЕ

Blender: hassler_native_upper.blend. Галерея: ../index.html.
Предыдущий step_08 сохранён. Его галерея: ../index_step08.html.

ИЗМЕНЕНИЯ
Обе золотые детали перестроены как протяжённые изогнутые поверхности: от
наружного края плеча до воротника и обозначенной синей линии на груди.
Наружная полуширина 0.280 м, чуть меньше step_08; увеличение направлено внутрь.
Красная ткань физически обрезана по верхней границе z = .5476 - .200*x
в координатах тела. Удалённая часть не оставлена скрытым красным слоем.
На оставшейся ткани сохранены прежние сглаженные нормали; на линии среза
они интерполированы вместе с UV и весами, чтобы не появлялись новые заломы света.
Открытая красная сторона сохраняет асимметрию костюма: другая полочка золотая.

Короткий серый конец воротника опущен, его свисающий угол развёрнут к груди.
Серая ткань в правом переднем повороте выведена из старого пересечения со своим
корнем. Оболочка мундира, её грани, UV и веса сохранены; изменены только
{len(build['collar']['changed_vertices'])} вершин воротника. Свисающая нижняя золотая полочка с красной изнанкой
не менялась. Высокая чёрная стойка не возвращалась: штатная шея остаётся видна.

Серые наплечники — отдельные замкнутые округлые оболочки над рукавами.
Верхние сечения посажены под фактическую золотую поверхность, нижние входят
в верх рукава. Историческая угловатая подложка перенесена в скрытый архив.
Текстура эполетов — Дитрих; новая UV развёрнута вдоль длины поверхности,
чтобы орнамент не вытягивался поперёк плеча. Это новая UV, не прежняя проекция.
Толщина золотого верха 2 мм, обратная сторона серая.

ИСХОДНЫЕ РИСУНКИ
../source/shoulder_fit_study/user_front_step09.png
../source/shoulder_fit_study/user_grey_shoulder_step09.png
Копии точные, без изменений. Контуры формы заданы вручную по этой разметке.
Пути и параметры в report.json. Наложение рисунка на фронтальный рендер
доступно в галерее. Старый арт: ../source/art/.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study:
10 Sewn uniform — hanging grey collar: основной мундир и серый воротник.
14 Epaulettes — continuous long gold shoulders: две золотые поверхности;
  каждая сетка 19 поперечных на 25 продольных точек. Форма board_point()
  и grid_vertices в report.json. Максимальный наружный размах не увеличен.
15 Red lining — below drawn blue boundary: настоящая верхняя красная ткань.
16 Grey shoulder caps — rounded over sleeves: отдельные серые наплечники;
  восемь управляющих сечений, плавно интерполированных в 22 кольца по 48
  вершин; параметры grey/rings_z_rx_ry. Нижний край поднят до 0.489 м,
  чтобы наплечник не превращался в длинную накладку на рукав.
13.1 / 13.2 / 13.3 Aiguillette — graduated gold loop: прежние три петли.
12 Inner shirt — native open neckline: прежний низкий край внутренней одежды.
ARCHIVE / REFERENCE выключены и во viewport, и в render.
Для ручной работы сохраняй отдельный .blend рядом: этот файл пересобирается
генератором из step_08. Объекты и материалы можно редактировать независимо.

ПРОВЕРКИ
SHA256 .blend: {digest}
Повторное открытие сохранённого файла, привязка всех показанных рендеров к hash.
Голова/шея, кисти, низ/пояс, внутренний чёрный верх, три шнура и 28 костей
проверены на неизменность. Одобренная нижняя раскрытая полочка не изменилась.
Основной мундир остаётся одной связной поверхностью. UV без нулевой площади;
максимум четыре нормированных костных влияния на вершину. Суммарные вершины
тела укладываются в 16-битный диапазон; окончательного игрового экспорта нет.
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольника, без головы и кистей.

Девять пробных поз: покой, локти, плечи, поворот корпуса/головы; два поворота
головы, наклон вперёд, взгляд вверх и наклон вбок. Эполет/мундир — 0;
серый наплечник/наружное золото — 0; голова/мундир — 0; шнуры/мундир — 0;
шнуры друг с другом — 0. Несоседние участки серого воротника не пересекаются;
соседство учитывает и соответствующие вершины толщины Solidify.
Максимальное расхождение нижнего шва штатной шеи: {seam:.9f} м.
Подробные числа и состояния по позам: validation.json.
Это проверка пробных Blender-поз, не игровых анимаций; игрового DFM/LOD
и установки нет. Окончательное принятие формы остаётся за визуальным просмотром.

ВОСПРОИЗВЕДЕНИЕ
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step09.py
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step09_check.py -- --render --strict
python tools/character_rounding/hassler_step09_review.py
'''
    links=re.findall(r'(?:href|src)="([^"]+)"',page);missing=[p for p in links if p!='step_09/README.txt' and not (TOP/p).is_file()];assert not missing,missing
    (OUT/'README.txt').write_text(readme,encoding='utf8');(TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущий вариант: шаг 09 — длинные эполеты по разметке, красная ткань ниже синей границы, свисающий серый воротник и округлые наплечники.\nBlender: step_09/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_09/README.txt. Предыдущие шаги сохранены.\n\n'
    p=TOP/'README.txt';old=p.read_text(encoding='utf8')
    if not old.startswith(intro):p.write_text(intro+old,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 09, эполеты и серые наплечники по разметке.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_09/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest,'triangles':check['body_triangles_with_modifiers']},ensure_ascii=False))
    def file_record(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    manifest={'blend':file_record(OUT/'hassler_native_upper.blend'),'parent':file_record(TOP/'step_08/hassler_native_upper.blend'),
              'references':[file_record(Path(p)) for p in build['references']],
              'previews':[file_record(p) for p in sorted(OUT.glob('*.png'))],
              'tools':[file_record(ROOT/'tools/character_rounding'/name) for name in ('hassler_native_step09.py','hassler_step09_check.py','hassler_step09_review.py')],
              'game_installed':False,'reference_contours_authored_manually':True}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
