"""Publish the restrained belt fit after rejecting STEP16's uniform expansion."""
import json,re
from pathlib import Path
from hassler_step14_review import ROOT,TOP,record,fig
OUT=TOP/'step_17'

def main():
    b=json.loads((OUT/'report.json').read_text(encoding='utf8'));c=json.loads((OUT/'validation.json').read_text(encoding='utf8'))
    digest=record(OUT/'hassler_native_upper.blend')['sha256']
    assert c['checks_passed'] and digest==c['blend_sha256']==c['previews_bound_to_blend_sha256']
    old=(TOP/'index.html').read_text(encoding='utf8');prior=TOP/'index_step16.html'
    if not prior.exists():
        assert 'step_16/hassler_native_upper.blend' in old;prior.write_text(old,encoding='utf8')
    css=re.search(r'<style>.*?</style>',old,re.S).group()
    page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — шаг 17: плотная посадка ремня</title>'+css
    page+='''<h1>Хасслер — шаг 17: небольшая поправка ремня</h1><p>Возвращена посадка шага 15. Исправлены только небольшие участки, где ткань проступала через внешнюю поверхность ремня. Общий размер почти прежний; широкое кольцо шага 16 убрано. Высота ремня и расстояние до мундира сохранены.</p>
<nav class="links"><a href="step_17/hassler_native_upper.blend">Blender со скелетом</a><a href="step_17/README.txt">Описание</a><a href="step_17/validation.json">Проверки</a><a href="index_step15.html">Исходная посадка</a><a href="index_step16.html">Отклонённое расширение</a></nav>'''
    page+=f'<p class="path">{OUT / "hassler_native_upper.blend"}</p>'
    page+='<div class="pair">'+fig('step_17/waist_front.png','Плотная посадка с локальной поправкой')+fig('step_17/full_front.png','Общий вид')+'</div>'
    page+='<h2>Сравнение с исходной посадкой</h2><div class="pair">'+fig('step_15/waist_front.png','Шаг 15: ткань выступала сквозь ремень')+fig('step_17/waist_front.png','Шаг 17: почти тот же размер, выступания устранены')+'</div>'
    page+='<div class="pair">'+fig('step_17/waist_side.png','Сбоку')+fig('step_17/waist_back.png','Сзади')+'</div>'
    page+='<details><summary>Сравнить с отклонённым широким ремнём</summary><div class="pair">'+fig('step_16/waist_front.png','Шаг 16: слишком свободная посадка')+fig('step_17/waist_front.png','Шаг 17: возвращён близкий к телу контур')+'</div></details>'
    page+='<p class="muted">Проверены сохранённый Blender-файл и пять пробных поз. Ткань не пересекает наружную поверхность ремня; контакт с его скрытой внутренней стороной допустим. Остальная модель, UV, веса и скелет сохранены. Офлайн-прототип.</p></html>'
    readme=f'''ХАССЛЕР — ШАГ 17: ПЛОТНАЯ ПОСАДКА РЕМНЯ

Blender: {OUT / 'hassler_native_upper.blend'}
Галерея: {TOP / 'index.html'}
Родитель: {b['parent']}
SHA256 родителя: {b['parent_sha256']}
SHA256 результата: {digest}

Общее расширение на 12 мм шага 16 отклонено пользователем. Работа снова
от шага 15: небольшие локальные поправки внешнего контура, без расширения
всего кольца по максимальному зазору. Сдвиги 72 сечений записаны в report.json.
Максимальный локальный сдвиг: {b['max_offset_m']*1000:.3f} мм.
Средний сдвиг: {b['mean_offset_m']*1000:.3f} мм.
Изменение полной ширины по X относительно шага 15: {b['width_increase_m']*1000:.3f} мм.
Итоговый силуэт по ширине практически исходный. Исправлены локальные участки
переднебокового обхвата. Пряжка/держатели перемещены по местному контуру.
Высота, Z, топология, UV, материалы и веса ремня сохранены. Вся остальная
геометрия, включая брюки, ткань талии, мундир, голову и кисти, совпадает
с шагом 15. Скелет сохранён. Старые Blender-файлы не изменены.

ИСПРАВЛЕНИЕ КРИТЕРИЯ ПОСАДКИ
В шаге 16 требовался зазор между тканью и всей 6-мм толщиной ремня, включая
скрытую внутреннюю поверхность. Это привело к ненужному общему увеличению.
Здесь проверяется видимая наружная сторона с обоими узкими скосами.
Скрытый контакт ткани внутри толщины ремня допустим; он не должен выходить
на наружную поверхность. Нижние возвраты входят в ткань под ремнём.
Минимальный наружный радиальный зазор: {c['outside_clearance_min_m']*1000:.3f} мм
(720 направлений × 17 высот). В пяти синтетических позах (1,30,60,90,120)
ткань не пересекает наружную сторону; мундир не пересекает ремень целиком.
Сохранённый файл заново открыт, проверены неизменённые данные и замкнутость.
Рендеры привязаны к SHA256 blend. Игровые анимации не проверялись.

Коллекция EDIT — native costume upper study, объекты 19/20/21.
Игра не изменена. Остальные материалы и ограничения: step_15/README.txt.

Воспроизведение:
python tools/blender_workspace.py --topic character_rounding --script tools/character_rounding/hassler_native_step17.py
python tools/character_rounding/hassler_step17_review.py
'''
    (OUT/'README.txt').write_text(readme,encoding='utf8')
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    intro='Текущая версия: шаг 17 — возвращена плотная посадка ремня, поправлены только места выступания ткани.\nBlender: step_17/hassler_native_upper.blend. Галерея: index.html.\nПодробности: step_17/README.txt. Общее расширение шага 16 отклонено.\n\n'
    p=TOP/'README.txt';text=p.read_text(encoding='utf8')
    if not text.startswith(intro):p.write_text(intro+text,encoding='utf8')
    p=ROOT/'out/character_rounding/README.txt';lines=p.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]='Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 17, плотная посадка ремня с локальными поправками.'
        if line.startswith('Blender: hassler/native_upper/step_'):lines[i]='Blender: hassler/native_upper/step_17/hassler_native_upper.blend.'
    p.write_text('\n'.join(lines)+'\n',encoding='utf8')
    manifest={'blend':record(OUT/'hassler_native_upper.blend'),'parent':record(Path(b['parent'])),'report':record(OUT/'report.json'),'validation':record(OUT/'validation.json'),'readme':record(OUT/'README.txt'),'previews':[record(p) for p in sorted(OUT.glob('*.png'))],'tools':[record(ROOT/'tools/character_rounding'/n) for n in ('hassler_native_step17.py','hassler_step17_review.py')],'game_installed':False}
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'gallery':str(TOP/'index.html'),'blend_sha256':digest},ensure_ascii=False))

if __name__=='__main__':main()
