"""Publish the small belt-clearance correction, preserving the accepted study."""
import json,re
from pathlib import Path
from hassler_step14_review import ROOT,TOP,record,fig
OUT=TOP/'step_16'

def main():
    b=json.loads((OUT/'report.json').read_text(encoding='utf8'));c=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert c['checks_passed'] and digest==c['blend_sha256']==c['previews_bound_to_blend_sha256']
    old=(TOP/'index.html').read_text(encoding='utf8');prior=TOP/'index_step15.html'
    if not prior.exists():
        assert 'step_15/hassler_native_upper.blend' in old;prior.write_text(old,encoding='utf8')
    css=re.search(r'<style>.*?</style>',old,re.S).group()
    page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — шаг 16: посадка ремня</title>'+css
    page+='''<h1>Хасслер — шаг 16: ремень чуть шире</h1><p>Ремень расширен по окружности на 12 мм, чтобы ткань брюк не проходила сквозь его боковые участки. Пряжка и держатели перемещены вместе с ремнём. Высота ремня и промежуток до мундира сохранены.</p>
<nav class="links"><a href="step_16/hassler_native_upper.blend">Blender со скелетом</a><a href="step_16/README.txt">Описание</a><a href="step_16/validation.json">Проверки</a><a href="index_step15.html">Предыдущий вариант</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('step_16/waist_front.png','Ремень полностью закрывает ткань на своей высоте')+fig('step_16/full_front.png','Общий силуэт')+'</div>'
    page+='<h2>До и после</h2><div class="pair">'+fig('step_15/waist_front.png','Шаг 15: ткань выступала сквозь боковые участки ремня')+fig('step_16/waist_front.png','Шаг 16: ремень расширен по окружности')+'</div>'
    page+='<div class="pair">'+fig('step_16/waist_side.png','Посадка сбоку')+fig('step_16/waist_back.png','Посадка сзади')+'</div>'
    page+='<p class="muted">Сохранённый Blender-файл заново открыт. Проверены неизменность остальной модели, высоты ремня, UV и весов; ремень не пересекает брюки, ткань талии и мундир в пяти пробных позах. Игровые анимации не проверялись. Офлайн-прототип.</p></html>'
    readme=f'''ХАССЛЕР — ШАГ 16: РЕМЕНЬ ЧУТЬ ШИРЕ

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {b['parent']}
SHA256 родителя: {b['parent_sha256']}
SHA256 результата: {digest}

Ремень сдвинут наружу по радиусу на 12 мм. Изменены только координаты X/Y
трёх объектов: ремня, пряжки и держателей. Пряжка и каждый из пяти держателей
перенесены целиком, без масштабирования. Высота, Z, топология, UV, материалы,
веса и скелет сохранены. Остальные объекты модели совпадают с шагом 15.

До правки минимальный радиальный зазор был {b['before']['min_radial_clearance_m']*1000:.2f} мм:
ткань пересекала ремень. После правки минимум {c['after']['min_radial_clearance_m']*1000:.2f} мм.
Проверено {c['after']['samples']} лучей: 720 направлений и 17 высот ремня.
Шаг расширения выбран по максимальному выступу ткани с небольшим запасом.
Сохранённый файл заново открыт. В пяти синтетических позах (1, 30, 60, 90,
120) ремень не пересекает брюки, ткань талии и мундир. Все три изменённых
объекта остаются замкнутыми с положительным объёмом. Архивные коллекции
отключены в viewport и render. Рендеры привязаны к SHA256 сохранённого blend.

Редактирование: коллекция EDIT — native costume upper study, объекты 19/20/21.
Исходный step_15 не изменён. Остальные исходники, материалы и ограничения
игрового экспорта описаны в step_15/README.txt. Цветовые узлы пока Blender.
Игра не изменена; игровые анимации не проверялись.

Воспроизведение:
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step16.py
python tools/character_rounding/hassler_step16_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 16 — ремень чуть шире, ткань брюк больше не пересекает его.\nBlender: step_16/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_16/README.txt. Остальная модель шага 15 сохранена.\n\n'
    p=TOP/'README.txt';text=p.read_text(encoding='utf8')
    if not text.startswith(intro):p.write_text(intro+text,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 16, ремень расширен поверх брюк.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_16/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(b['parent'])),'report':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'readme':record(OUT/'README.txt'),'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/n) for n in ('hassler_native_step16.py','hassler_step16_review.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest},ensure_ascii=False))

if __name__=='__main__':main()
