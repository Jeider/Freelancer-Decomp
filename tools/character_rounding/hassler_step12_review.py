"""Publish the shoulder tailoring study, keeping the previous review intact."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOP = ROOT / 'out/character_rounding/hassler/native_upper'
OUT = TOP / 'step_12'


def record(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def fig(path, label):
    return f'<figure><a href="{path}"><img src="{path}" loading="lazy" alt="{label}"></a><figcaption>{label}</figcaption></figure>'


def main():
    check = json.loads((OUT / 'validation.json').read_text(encoding='utf8'))
    build = json.loads((OUT / 'report.json').read_text(encoding='utf8'))
    contacts = json.loads((OUT / 'contacts.json').read_text(encoding='utf8'))
    digest = record(OUT / 'hassler_native_upper.blend')['sha256']
    assert digest == check['blend_sha256'] == check['previews_bound_to_blend_sha256'] == contacts['blend_sha256']
    assert check['layer_checks_passed']
    previous = TOP / 'index_step11.html'
    if not previous.exists():
        assert 'step_11/hassler_native_upper.blend' in (TOP / 'index.html').read_text(encoding='utf8')
        previous.write_bytes((TOP / 'index.html').read_bytes())
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Хасслер — шаг 12: посадка наплечников и серого воротника</title>
<style>body{margin:30px auto;max-width:1400px;padding:0 24px;background:#191c20;color:#e5e8eb;font:17px/1.5 system-ui}h1{font-size:30px}h2{font-size:22px;margin-top:32px}a{color:#e8c780}figure{margin:0}img{display:block;width:100%;height:auto;background:#333}figcaption{padding:9px 0 18px;color:#bdc4cc}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.links{display:flex;gap:20px;flex-wrap:wrap}summary{cursor:pointer;color:#e8c780}details{margin:24px 0}.path{overflow-wrap:anywhere;font:14px/1.5 monospace}.muted{color:#b5bdc6}@media(max-width:760px){.pair,.grid{grid-template-columns:1fr}body{padding:0 12px}}</style>
<h1>Хасслер — шаг 12: посадка наплечников и воротника</h1>
<p>Серые опоры уменьшены по последней разметке: наружный выступ убран, округлая часть под золотом сохранена. Зелёные рукава подходят к опорам снизу. Воротник опущен на эполеты, обе его стороны серые, край красный.</p>
<p>Стороны указаны относительно самого персонажа: справа под эполет уходит красная ткань, слева — золотая передняя часть мундира. Эполеты и наплечники зеркально симметричны.</p>
<nav class="links"><a href="step_12/hassler_native_upper.blend">Blender</a><a href="step_12/README.txt">Редактирование и проверки</a><a href="step_12/validation.json">Отчёт</a><a href="index_step11.html">Предыдущий шаг 11</a></nav>'''
    page += f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page += '<div class="pair">' + fig('source/shoulder_fit_study/user_front_step12.png', 'Разметка пользователя: зелёный — воротник, синий — граница эполета, чёрное убрать, голубой — рукав') + fig('step_12/front.png', 'Шаг 12: оба плеча и серый воротник') + '</div>'
    page += '<h2>Оба плеча крупным планом</h2><div class="pair">' + fig('step_12/right_shoulder_detail.png', 'Правое плечо Хасслера: красная ткань под эполетом') + fig('step_12/shoulder_detail.png', 'Левое плечо Хасслера: золотая передняя часть и аксельбант') + '</div>'
    page += '<div class="pair">' + fig('step_12/three_quarter.png', 'Общий вид в три четверти') + fig('step_12/shoulders_above.png', 'Воротник и плечи сверху') + '</div>'
    page += '<details><summary>Сравнение с шагом 11</summary><div class="pair">' + fig('step_11/front.png', 'Шаг 11: крупные серые опоры, золотая изнанка воротника') + fig('step_12/front.png', 'Шаг 12: уменьшенные опоры, серый свисающий воротник') + '</div></details>'
    page += '<details><summary>Профиль, спина и пробные движения</summary><div class="pair">'
    for name, label in [('side', 'Профиль'), ('back', 'Спина'), ('shoulder_pose', 'Пробная поза рук'), ('turn_pose', 'Поворот корпуса')]:
        page += fig(f'step_12/{name}.png', label)
    page += '</div></details>'
    page += f'''<p>Сохранённый Blender-файл открыт заново и проверен в девяти пробных позах. Эполеты, наплечники и воротник не пересекают друг друга; новые участки рукавов не добавляют самопересечений. Голова, кисти, скелет, раскрытая полочка и аксельбанты сохранены.</p>
<p class="muted">Офлайн-прототип: {check['body_triangles_with_modifiers']:,} треугольников тела с модификаторами, без головы и кистей. Посадочные швы учтены отдельно в отчёте. Проверены синтетические позы; игровые анимации этим шагом не проверялись. В игру не установлен.</p></html>'''
    readme = f'''ХАССЛЕР — ШАГ 12: ПОСАДКА НАПЛЕЧНИКОВ И СЕРОГО ВОРОТНИКА

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {build['parent']}
Разметка: {build['reference']}

ФОРМА
Стороны относительно самого Хасслера: правое плечо — красная полочка,
левое плечо — золотая передняя часть и аксельбант.
Золотые эполеты сохранены из шага 11. Серые опоры зеркально уменьшены:
убран наружный выступ, оставлена округлая видимая часть под золотом.
Зелёные верхние части рукавов продлены к опорам; внутренний шов проймы,
крепления аксельбантов и рукава ниже плеч сохранены.
Короткий правый воротник опущен и расправлен поверх эполета.
Воротник серый с обеих сторон, красный кант диаметром 2.8 мм — отдельный меш.
Золотая соединительная ткань толщиной 0.6 мм находится под воротником.
Форма задана вручную по рисунку; автоматического распознавания разметки нет.

РЕДАКТИРОВАНИЕ
Коллекция EDIT — native costume upper study:
10 Sewn uniform — grey draped collar and fitted sleeves: мундир и воротник.
  Основная UV и веса исходного меша сохранены. Слоты 4, 15, 22, 33 серые.
  Старая дополнительная Collar inside brocade UV сохранена, но не используется.
14 Epaulettes — thin gold with inward rolled hem: неизменённые золотые эполеты.
16 Grey shoulder pads — tailored inside gold contour: уменьшенные серые опоры.
17 Gold cloth — fitted under draped grey collar: золотая ткань под воротником.
18 Collar — continuous red edge: отдельный красный кант воротника.
11 Red binding — continuous 3 mm seams.008: остальной кант мундира.
15 Red lining — below drawn blue boundary: неизменённая красная полочка.
13.1 / 13.2 / 13.3: неизменённые петли аксельбанта.
ARCHIVE / REFERENCE отключены и в viewport, и в render.
Ручные правки сохранять отдельным blend рядом: генератор перезаписывает
только автоматический step_12/hassler_native_upper.blend.

ПРОВЕРКИ И ГРАНИЦЫ
SHA256: {digest}
Галерея получена из сохранённого и заново открытого файла с этим хешем.
Обе пары плечевых деталей замкнуты, имеют положительный объём и зеркальную форму.
UV без вырожденных треугольников; до четырёх нормированных весов на вершину.
Исходные голова, кисти, шея, скелет, низ, рубашка, красная полочка,
золотые эполеты и аксельбанты проверены на сохранность.
Девять синтетических поз: покой, локти, плечи, поворот корпуса/головы,
повороты головы в обе стороны, наклоны вперёд, вверх и вбок.
В этих позах нет пересечений между золотом, серыми опорами и воротником,
нет контактов головы с воротником, свободных петель шнуров с тканью или друг с другом.
Соединительная ткань пришита в пределах 3 мм от кромки; контакты там учтены
отдельно от пересечений её свободной поверхности. Посадка эполетов в основную
ткань мундира также учитывается отдельно и не считается глобальным отсутствием контактов.
Изменённые области рукавов проверены относительно шага 11: новых
самопересечений нет. Это локальная проверка, не обещание исправления всей старой сетки.
Тело с модификаторами: {check['body_triangles_with_modifiers']} треугольников.
DFM, LOD, игровые анимации и установка этим шагом не выполнялись.

ВОСПРОИЗВЕДЕНИЕ (из корня репозитория)
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step12.py -- --no-render
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step12_check.py -- --strict --render
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_step12_contacts.py
python tools/character_rounding/hassler_step12_review.py
'''
    (OUT / 'README.txt').write_text(readme, encoding='utf8')
    missing = [p for p in re.findall(r'(?:href|src)="([^"]+)"', page) if not (TOP / p).is_file()]
    assert not missing, missing
    (TOP / 'index.html').write_text(page, encoding='utf8')
    intro = 'Текущая версия: шаг 12 — уменьшенные симметричные наплечники, зелёные рукава под опорами и серый свисающий воротник с красным кантом.\nBlender: step_12/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_12/README.txt. Предыдущие шаги сохранены.\n\n'
    path = TOP / 'README.txt'
    old = path.read_text(encoding='utf8')
    if not old.startswith(intro):
        path.write_text(intro + old, encoding='utf8')
    path = ROOT / 'out/character_rounding/README.txt'
    lines = path.read_text(encoding='utf8').splitlines()
    for i, line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):
            lines[i] = 'Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 12, посадка наплечников и серого воротника.'
        if line.startswith('Blender: hassler/native_upper/step_'):
            lines[i] = 'Blender: hassler/native_upper/step_12/hassler_native_upper.blend.'
    path.write_text('\n'.join(lines) + '\n', encoding='utf8')
    scripts = ['hassler_native_step12.py', 'hassler_step12_check.py', 'hassler_step12_contacts.py', 'hassler_step12_review.py', 'hassler_native_step11.py', 'hassler_step11_check.py', 'hassler_native_step09.py', 'hassler_native_step08.py', 'hassler_step08_check.py', 'hassler_native_step03.py']
    manifest = {'blend': record(OUT / 'hassler_native_upper.blend'), 'parent': record(Path(build['parent'])), 'report': record(OUT / 'report.json'), 'validation': record(OUT / 'validation.json'), 'contacts': record(OUT / 'contacts.json'), 'reference': record(Path(build['reference'])), 'previews': [record(p) for p in sorted(OUT.glob('*.png'))], 'tools': [record(ROOT / 'tools/character_rounding' / p) for p in scripts], 'game_installed': False}
    (OUT / 'review_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'gallery': str(TOP / 'index.html'), 'blend_sha256': digest, 'triangles': check['body_triangles_with_modifiers']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
