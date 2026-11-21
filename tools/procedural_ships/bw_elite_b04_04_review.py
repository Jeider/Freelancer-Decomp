"""Write the local volume/sweep review after saved model and render validation."""
import html
import json
from pathlib import Path

import bw_elite_b04_03_review as common

OUT = Path(__file__).resolve().parents[2] / 'out/ship_design/bw_family/elite/prototypes/b04_04'


def main():
    common.OUT = OUT
    report = common.validate()
    views = [('form_rear_34.png','Сзади 3/4'),('form_top.png','Сверху — новая стреловидность и широкий нос'),
             ('form_front_34.png','Спереди 3/4'),('form_side.png','Сбоку — сужение кормы и стойка'),
             ('form_upper_rear_34.png','Верхний корпус крупно'),('form_rear.png','Сзади'),
             ('form_belly.png','Снизу'),('form_hold.png','Неглубокий трюм, створки временно скрыты')]
    cards = '\n'.join(f'<figure><a href="{f}"><img loading="lazy" src="{f}" alt="{html.escape(c)}"></a>'
                      f'<figcaption>{html.escape(c)}</figcaption></figure>' for f,c in views)
    files = '\n'.join(f'<li><a href="{n}">{html.escape((OUT/n).as_posix())}</a></li>'
                      for n in ['bw_pir_elite_b04.blend','bw_pir_elite_b04_review_open.cmp','README.md'])
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>B04 ELITE — форма 04</title>
<style>:root{color-scheme:dark}body{margin:0;background:#1b2126;color:#e3e7e9;font:16px/1.5 system-ui,sans-serif}
main{max-width:1480px;margin:auto;padding:26px}h1{font-size:29px;margin:0}h2{font-size:22px;margin:30px 0 12px}
p{max-width:1050px}a{color:#b8d9ec}figure{margin:0;background:#272e34;border:1px solid #414b53;border-radius:6px;overflow:hidden}
img{display:block;width:100%;height:auto}figcaption{padding:9px 14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
li{overflow-wrap:anywhere;margin:8px 0}.muted{color:#b2bdc5}.tag{color:#e8bb84}details{margin:24px 0}summary{cursor:pointer}
@media(max-width:800px){main{padding:14px}.grid{grid-template-columns:1fr}}</style><main>
<div class="tag">BW PIRATE ELITE · B04/04 · 19 ноября 2026</div>
<h1>Выпуклые объёмы, стреловидные крылья, широкий клиновидный нос</h1>
<p>Спинка и плечи получили подъём к середине и плавные переходы. Крылья начинаются дальше вперёд,
их передняя кромка сильнее уходит назад; поверхности имеют выпуклый профиль. Корма сужается
к соплу сверху и снизу. Площадки под оборудование убраны. Родная кабина сохранена.</p>
<p class="muted">Статичный прототип формы · треугольников: TRIANGLES · анимации отложены · UV предварительные.
Нижняя стойка остаётся узкой, её передняя грань выпрямлена. Форма ещё требует вашего просмотра.</p>
<div class="grid">CARDS</div>
<h2>Сравнение силуэта сверху: 03 → 04</h2><div class="grid">
<figure><a href="../b04_03/form_top.png"><img loading="lazy" src="../b04_03/form_top.png" alt="Форма 03 сверху"></a><figcaption>03 — прежние крылья и игольчатый нос</figcaption></figure>
<figure><a href="form_top.png"><img loading="lazy" src="form_top.png" alt="Форма 04 сверху"></a><figcaption>04 — стреловидность, более широкий нос</figcaption></figure></div>
<h2>Референсы и ваши отметки</h2><p>
<a href="../../../concepts/round_04/bw_family_B04_VIEWS_B_sheet.png">B04_VIEWS_B: ELITE REAR; FIGHTER для деталей верхнего корпуса и стреловидности</a> ·
<a href="../../../concepts/round_04/bw_family_B04_VIEWS_A_sheet.png">B04_VIEWS_A</a></p>
<p><a href="../../references/b04_shape_review/user_side_profile_20261119.png">Отмеченный боковой профиль</a> ·
<a href="../../references/b04_shape_review/user_wing_sweep_20261119.png">Сравнение крыла с референсом</a></p>
<h2>Файлы</h2><ul>FILES</ul>
<p>Blender показывает форму условными материалами. CMP использует внешние родные BW-материалы;
полноценный UV-проход и посадка хардпоинтов предстоят после обсуждения геометрии.</p>
<details><summary>Проверки</summary><p><a href="review_validation.json">Хеши и комплектность</a> ·
<a href="manifest.json">Источники и экспорт</a> · <a href="topology_audit.json">Топология</a> ·
<a href="blender_validation.json">Проверка геометрии и трюма</a></p></details></main></html>'''
    page=page.replace('CARDS',cards).replace('FILES',files).replace('TRIANGLES',str(report['triangles']))
    (OUT/'index.html').write_text(page,encoding='utf8')
    print(json.dumps(dict(gallery=(OUT/'index.html').as_posix(),status=report['status'],triangles=report['triangles'])))


if __name__=='__main__':main()
